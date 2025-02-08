from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.http import DjangoHTTPCallbackImpl
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.type import EventType

__all__ = ["DjangoModule"]


class DjangoModule:
    plugin: DjangoExceptionPlugin
    exc_has_been_parsed_event: EventType[
            OnDjangoExceptionHasBeenParsedEvent
        ]

    @classmethod
    def _register_events(cls):
        cls.exc_has_been_parsed_event = EventType[
            OnDjangoExceptionHasBeenParsedEvent
        ]()

        cls.exc_has_been_parsed_event.subscribe(
            DjangoHTTPCallbackImpl.send_through_urllib,
        )

    @classmethod
    def register(cls, *, base_url: str, api_key: str):
        DjangoHTTPCallbackImpl.initialize(
            base_url=base_url,
            api_key=api_key,
        )

        cls._register_events()
        cls.plugin = DjangoExceptionPlugin(cls.exc_has_been_parsed_event)
