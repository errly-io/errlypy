import pytest
from channels.testing import HttpCommunicator  # type: ignore[import-untyped]

from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.type import EventType
from errlypy.lib import UninitializedPluginControllerImpl
from tests.django.mysite.asgi import application


@pytest.mark.asyncio
async def test_asgi_zero_division():
    communicator = HttpCommunicator(application, "GET", "/async-view-zero-division")

    on_exc_has_been_parsed = EventType[OnDjangoExceptionHasBeenParsedEvent]()

    UninitializedPluginControllerImpl.init(plugins=[DjangoExceptionPlugin(on_exc_has_been_parsed)])

    resp = await communicator.get_response()
    await communicator.wait()

    assert resp["status"] == 500


@pytest.mark.asyncio
async def test_asgi_zero_division_sleep_3_sec():
    communicator = HttpCommunicator(application, "GET", "/async-view-zero-division-sleep-3-sec")

    on_exc_has_been_parsed = EventType[OnDjangoExceptionHasBeenParsedEvent]()

    UninitializedPluginControllerImpl.init(plugins=[DjangoExceptionPlugin(on_exc_has_been_parsed)])

    resp = await communicator.get_response(5)
    await communicator.wait(5)

    assert resp["status"] == 500


@pytest.mark.asyncio
async def test_asgi_ok():
    communicator = HttpCommunicator(application, "GET", "/async-view-ok")

    on_exc_has_been_parsed = EventType[OnDjangoExceptionHasBeenParsedEvent]()

    UninitializedPluginControllerImpl.init(plugins=[DjangoExceptionPlugin(on_exc_has_been_parsed)])

    resp = await communicator.get_response()
    await communicator.wait()

    assert resp["status"] == 200


@pytest.mark.asyncio
async def test_asgi_ok_sleep_3_sec():
    communicator = HttpCommunicator(application, "GET", "/async-view-ok-sleep-3-sec")

    on_exc_has_been_parsed = EventType[OnDjangoExceptionHasBeenParsedEvent]()

    UninitializedPluginControllerImpl.init(plugins=[DjangoExceptionPlugin(on_exc_has_been_parsed)])

    resp = await communicator.get_response(5)
    await communicator.wait(5)

    assert resp["status"] == 200
