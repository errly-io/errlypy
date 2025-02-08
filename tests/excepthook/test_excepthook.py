import sys
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import NoReturn, cast

from pytest import MonkeyPatch

from errlypy.api import ExceptionCallback
from errlypy.exception import ParsedExceptionDto
from errlypy.exception.callback import (
    CreateExceptionCallbackMeta,
    ExceptionCallbackImpl,
    FrameDetail,
)
from errlypy.utils import has_contract_been_implemented, has_dict_contract_been_implemented


class UncaughtExceptionFromRepr(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ExceptionCallbackImplWithInvalidRepr(ExceptionCallbackImpl):
    def __repr__(self) -> NoReturn:
        raise UncaughtExceptionFromRepr("Uncaught error for __repr__")


def test_exception_callback_impl_contract_success():
    instance = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    result = has_contract_been_implemented(instance, ExceptionCallback)

    assert result is True


def test_exception_callback_impl_contract_fail():
    class IncorrectCallback(ABC):
        @abstractmethod
        def incorrect_method(self):
            pass

    instance = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    result = has_contract_been_implemented(instance, IncorrectCallback)

    assert result is False


def test_exception_callback_impl_result_success():
    mpatch = MonkeyPatch()
    callback = ExceptionCallbackImpl.create()
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    assert isinstance(result, ParsedExceptionDto)
    assert isinstance(result.frames, list)
    assert len(result.frames) > 0
    assert isinstance(result.frames[0], FrameDetail)


def test_exception_callback_impl_result_frame_detail_contract_success():
    mpatch = MonkeyPatch()
    callback = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    frame_detail = result.frames[0]
    assert has_dict_contract_been_implemented(asdict(frame_detail), FrameDetail)


def test_exception_callback_impl_result_frame_detail_body_success():
    mpatch = MonkeyPatch()
    callback = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    frame_detail = cast(FrameDetail, result.frames[0])
    assert frame_detail.function == "test_exception_callback_impl_result_frame_detail_body_success"
    assert frame_detail.line == 'raise ValueError("Test")'
    assert frame_detail.filename.endswith("test_excepthook.py") is True
    assert "pytest.monkeypatch.MonkeyPatch object at" in frame_detail.locals["mpatch"]
    assert (
        "errlypy.exception.callback.ExceptionCallbackImpl object at"
        in frame_detail.locals["callback"]
    )


def test_exception_callback_impl_with_invalid_repr_result_frame_detail_body_success():
    mpatch = MonkeyPatch()
    callback = ExceptionCallbackImplWithInvalidRepr.create({}, CreateExceptionCallbackMeta())
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    assert len(result.frames) == 0
