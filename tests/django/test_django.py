import builtins
import contextlib
from unittest.mock import MagicMock, patch

import django
import pytest
from django.core.handlers.exception import get_exception_response, response_for_exception
from pytest import MonkeyPatch

from errlypy.api import IModule
from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.type import EventType
from errlypy.lib import UninitializedModuleController


@pytest.fixture
def on_exc_parsed_fixture():
    return EventType[OnDjangoExceptionHasBeenParsedEvent]()


@pytest.fixture
def mock_django_module(monkeypatch, on_exc_parsed_fixture, request):
    django_plugin = DjangoExceptionPlugin()
    django_plugin.setup(on_exc_parsed_fixture)
    request.addfinalizer(django_plugin.revert)

    mock_initialized_django_module = MagicMock()
    mock_initialized_django_module.plugins = [django_plugin]
    monkeypatch.setattr(
        "errlypy.django.module.UninitializedDjangoModule.setup",
        MagicMock(return_value=mock_initialized_django_module),
    )

    mock_uninitialized_excepthook_module = MagicMock()
    monkeypatch.setattr(
        "errlypy.excepthook.module.UninitializedExceptHookModule.setup",
        MagicMock(return_value=mock_uninitialized_excepthook_module),
    )

    original_isinstance = builtins.isinstance

    def mocked_isinstance(obj, class_or_tuple):
        if class_or_tuple is IModule:
            if obj is mock_initialized_django_module:
                return True
            if obj is mock_uninitialized_excepthook_module:
                return False
        return original_isinstance(obj, class_or_tuple)

    isinstance_patcher = patch("errlypy.lib.isinstance", new=mocked_isinstance)
    isinstance_patcher.start()
    request.addfinalizer(isinstance_patcher.stop)

    yield django_plugin


def get_resolver_mock(*args):
    return MagicMock()


def get_settings_mock(*args, env=None, **kwargs):
    if env is None:
        env = {}
    mock = MagicMock()
    mock.DEBUG_PROPAGATE_EXCEPTIONS = env.get("DEBUG_PROPAGATE_EXCEPTIONS", False)
    mock.DEBUG = env.get("DEBUG", False)

    return mock


def test_response_for_exception_trigger(mock_django_module):
    django_plugin = mock_django_module
    request = MagicMock()
    exc = Exception("Test")

    UninitializedModuleController.init(base_url="test", api_key="test")

    mpatch = MonkeyPatch()
    mpatch.setattr(django.core.handlers.exception, "get_resolver", get_resolver_mock)
    mpatch.setattr(django.core.handlers.exception, "settings", get_settings_mock())

    with patch(
        "django.core.handlers.exception.handle_uncaught_exception",
        wraps=django_plugin,
    ) as mocked_handle_uncaught:
        response_for_exception(request, exc)
        assert mocked_handle_uncaught.call_count == 1

    mpatch.undo()


def test_get_exception_response_trigger(mock_django_module):
    django_plugin = mock_django_module
    request = MagicMock()
    resolver = MagicMock()

    def error(status_code: int):
        raise Exception("Test")

    resolver.resolve_error_handler = error
    status_code = 500
    exc = Exception("Test")

    UninitializedModuleController.init(base_url="test", api_key="test")

    mpatch = MonkeyPatch()
    mpatch.setattr(django.core.handlers.exception, "settings", get_settings_mock())

    with patch(
        "django.core.handlers.exception.handle_uncaught_exception", wraps=django_plugin
    ) as mocked_handle_uncaught:
        with contextlib.suppress(Exception):
            get_exception_response(request, resolver, status_code, exc)

        assert mocked_handle_uncaught.call_count == 1
    mpatch.undo()
