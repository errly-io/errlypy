from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.http import DjangoHTTPCallbackImpl
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.type import EventType

__all__ = ["DjangoModule"]


class DjangoModule:
    @classmethod
    def _register_events(cls):
        cls._on_exc_has_been_parsed_event_instance = EventType[
            OnDjangoExceptionHasBeenParsedEvent
        ]()

        cls._on_exc_has_been_parsed_event_instance.subscribe(
            DjangoHTTPCallbackImpl.send_through_urllib,
        )

    @classmethod
    def register(cls):
        cls._register_events()

        cls.exc_plugin = DjangoExceptionPlugin(
            cls._on_exc_has_been_parsed_event_instance
        )
