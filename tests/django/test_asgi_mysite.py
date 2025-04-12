from unittest.mock import MagicMock

import pytest
from channels.testing import HttpCommunicator  # type: ignore[import-untyped]

from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.type import EventType
from errlypy.lib import UninitializedModuleController
from tests.django.mysite.asgi import application


@pytest.fixture
def mock_django_module(monkeypatch):
    django_plugin = DjangoExceptionPlugin()
    mock_module = MagicMock()
    mock_module.setup.return_value = mock_module
    mock_module.plugins = [django_plugin]
    monkeypatch.setattr("errlypy.lib.UninitializedDjangoModule", mock_module)
    return mock_module


@pytest.fixture
def on_exc_parsed_fixture():
    return EventType[OnDjangoExceptionHasBeenParsedEvent]()


@pytest.mark.asyncio
async def test_asgi_zero_division(mock_django_module):
    communicator = HttpCommunicator(application, "GET", "/async-view-zero-division")
    UninitializedModuleController.init(base_url="test", api_key="test")

    resp = await communicator.get_response()
    await communicator.wait()

    assert resp["status"] == 500


@pytest.mark.asyncio
async def test_asgi_zero_division_sleep_3_sec(mock_django_module):
    communicator = HttpCommunicator(application, "GET", "/async-view-zero-division-sleep-3-sec")
    UninitializedModuleController.init(base_url="test", api_key="test")

    resp = await communicator.get_response(5)
    await communicator.wait(5)

    assert resp["status"] == 500


@pytest.mark.asyncio
async def test_asgi_ok(mock_django_module):
    communicator = HttpCommunicator(application, "GET", "/async-view-ok")
    UninitializedModuleController.init(base_url="test", api_key="test")

    resp = await communicator.get_response()
    await communicator.wait()

    assert resp["status"] == 200


@pytest.mark.asyncio
async def test_asgi_ok_sleep_3_sec(mock_django_module):
    communicator = HttpCommunicator(application, "GET", "/async-view-ok-sleep-3-sec")
    UninitializedModuleController.init(base_url="test", api_key="test")

    resp = await communicator.get_response(5)
    await communicator.wait(5)

    assert resp["status"] == 200
