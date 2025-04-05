import sys
from types import TracebackType
from typing import Callable, Optional, Type
from uuid import uuid4

from errlypy.api import IPlugin
from errlypy.excepthook.events import OnExceptionHasBeenParsedEvent
from errlypy.exception.callback import ExceptionCallbackImpl
from errlypy.internal.event.type import EventType


class ExceptHookPlugin(IPlugin):
    original_excepthook: Optional[Callable] = None

    def __init__(
        self,
        on_exception_has_been_parsed_event: EventType[OnExceptionHasBeenParsedEvent],
    ) -> None:
        self._on_exception_has_been_parsed_event = on_exception_has_been_parsed_event

    def setup(self):
        self.original_excepthook = sys.excepthook
        sys.excepthook = self

    def revert(self):
        sys.excepthook = self.original_excepthook

    def __call__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ):
        callback = ExceptionCallbackImpl()
        response = callback(exc_type, exc_value, exc_traceback)

        self._on_exception_has_been_parsed_event.notify(
            OnExceptionHasBeenParsedEvent(event_id=uuid4(), data=response),
        )
