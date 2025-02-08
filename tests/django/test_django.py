from unittest.mock import MagicMock, patch

import django
import pytest
from django.core.handlers.exception import get_exception_response, response_for_exception
from pytest import MonkeyPatch

from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.type import EventType
from errlypy.lib import UninitializedPluginControllerImpl


@pytest.fixture
def on_exc_parsed_fixture():
    return EventType[OnDjangoExceptionHasBeenParsedEvent]()


def get_resolver_mock(*args):
    return MagicMock()


def get_settings_mock(*args, env={}, **kwargs):
    mock = MagicMock()
    mock.DEBUG_PROPAGATE_EXCEPTIONS = env.get("DEBUG_PROPAGATE_EXCEPTIONS", False)
    mock.DEBUG = env.get("DEBUG", False)

    return mock


def test_response_for_exception_trigger(on_exc_parsed_fixture):
    request = MagicMock()
    exc = Exception("Test")

    django_plugin = DjangoExceptionPlugin(on_exc_parsed_fixture)
    UninitializedPluginControllerImpl.init(plugins=[django_plugin])

    mpatch = MonkeyPatch()
    mpatch.setattr(django.core.handlers.exception, "get_resolver", get_resolver_mock)
    mpatch.setattr(django.core.handlers.exception, "settings", get_settings_mock())

    with patch.object(django_plugin, "__call__", wraps=django_plugin.__call__) as wrapped_call:
        response_for_exception(request, exc)

        wrapped_call.call_count == 1

    mpatch.undo()


def test_get_exception_response_trigger(on_exc_parsed_fixture):
    request = MagicMock()
    resolver = MagicMock()

    def error(status_code: int):
        raise Exception("Test")

    resolver.resolve_error_handler = error
    status_code = 500
    exc = Exception("Test")

    django_plugin = DjangoExceptionPlugin(on_exc_parsed_fixture)
    UninitializedPluginControllerImpl.init(plugins=[django_plugin])

    mpatch = MonkeyPatch()
    mpatch.setattr(django.core.handlers.exception, "settings", get_settings_mock())

    with patch.object(django_plugin, "__call__", wraps=django_plugin.__call__) as wrapped_call:
        try:
            get_exception_response(request, resolver, status_code, exc)
        except Exception:
            pass

        wrapped_call.call_count == 1

    mpatch.undo()
