from types import TracebackType
from typing import Any, Tuple, Type
from uuid import uuid4

from django.core.handlers import exception

from errlypy.api import Plugin
from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.exception.callback import ExceptionCallbackImpl
from errlypy.internal.event.type import EventType


class DjangoExceptionPlugin(Plugin):
    def __init__(
        self,
        on_exc_has_been_parsed_event_instance: EventType[OnDjangoExceptionHasBeenParsedEvent],
    ) -> None:
        self._on_exc_has_been_parsed_event_instance = on_exc_has_been_parsed_event_instance

    def setup(self):
        self._callback = ExceptionCallbackImpl.create()
        self._original_fn = exception.handle_uncaught_exception
        exception.handle_uncaught_exception = self

    def revert(self):
        exception.handle_uncaught_exception = self._original_fn

    def __call__(
        self,
        request,
        resolver,
        exc_info: Tuple[Type[BaseException], BaseException, TracebackType],
    ) -> Any:
        response = self._callback(exc_info[0], exc_info[1], exc_info[2])

        self._on_exc_has_been_parsed_event_instance.notify(
            OnDjangoExceptionHasBeenParsedEvent(event_id=uuid4(), data=response),
        )

        return self._original_fn(request, resolver, exc_info)
