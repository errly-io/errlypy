import sys
from dataclasses import asdict
from typing import cast

import pytest

from errlypy.exception import ParsedExceptionDto
from errlypy.exception.callback import (
    CreateExceptionCallbackMeta,
    ExceptionCallbackImpl,
    FrameDetail,
)
from errlypy.utils import has_dict_contract_been_implemented


@pytest.mark.asyncio
async def test_exception_callback_impl_result_success():
    mpatch = pytest.MonkeyPatch()
    callback = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    assert isinstance(result, ParsedExceptionDto)
    assert isinstance(result.frames, list)
    assert len(result.frames) > 0
    assert isinstance(result.frames[0], FrameDetail)


@pytest.mark.asyncio
async def test_exception_callback_impl_result_frame_detail_contract_success():
    mpatch = pytest.MonkeyPatch()
    callback = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    frame_detail = result.frames[0]
    assert has_dict_contract_been_implemented(asdict(frame_detail), FrameDetail)


@pytest.mark.asyncio
async def test_exception_callback_impl_result_frame_detail_body_success():
    mpatch = pytest.MonkeyPatch()
    callback = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
    mpatch.setattr(sys, "excepthook", callback)

    try:
        raise ValueError("Test")
    except ValueError as err:
        result = sys.excepthook(type(err), err, err.__traceback__)

    frame_detail = cast(FrameDetail, result.frames[0])
    assert (
        frame_detail.function
        == "test_exception_callback_impl_result_frame_detail_body_success"
    )
    assert frame_detail.line == 'raise ValueError("Test")'
    assert frame_detail.filename.endswith("test_async_excepthook.py") is True
    assert "pytest.monkeypatch.MonkeyPatch object at" in frame_detail.locals["mpatch"]
    assert (
        "errlypy.exception.callback.ExceptionCallbackImpl object at"
        in frame_detail.locals["callback"]
    )
