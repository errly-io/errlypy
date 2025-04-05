from typing import ClassVar, List, Optional, Union
from uuid import uuid4

from errlypy.api import IModule, IUninitializedModule
from errlypy.client import HTTPClient
from errlypy.client.urllib import URLLibClient
from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.django.plugin import DjangoExceptionPlugin
from errlypy.internal.event.on_plugin_initialized import OnPluginInitializedEvent
from errlypy.internal.event.type import EventType


class UninitializedDjangoModule(IUninitializedModule):
    """
    Represents the uninitialized state of the Django module.
    Handles configuration and initialization of Django-specific components.
    """
    _instance: ClassVar[Optional['UninitializedDjangoModule']] = None

    def __new__(cls) -> 'UninitializedDjangoModule':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _initialize_plugin(exc_has_been_parsed_event: EventType[OnDjangoExceptionHasBeenParsedEvent]) -> DjangoExceptionPlugin:
        """Initializes and sets up the Django exception plugin."""
        plugin = DjangoExceptionPlugin(exc_has_been_parsed_event)
        plugin.setup()

        return plugin

    @staticmethod
    def _verify_django_installed() -> bool:
        """Verifies that Django is installed in the environment."""
        try:
            import django  # noqa: F401
        except ImportError:
            return False

        return True

    @classmethod
    def setup(cls, base_url: str, api_key: str) -> Union["IModule", "IUninitializedModule"]:
        """
        Initializes the Django module and transitions to initialized state.

        Returns:
            DjangoModule: Initialized Django module instance

        Raises:
            ValueError: If module is not configured
            ImportError: If Django is not installed
            RuntimeError: If initialization sequence is invalid
        """
        if not cls._verify_django_installed():
            return UninitializedDjangoModule()

        http_client = HTTPClient(
            client=URLLibClient(
                base_url=base_url,
                api_key=api_key,
            ),
        )

        exc_has_been_parsed_event = EventType[OnDjangoExceptionHasBeenParsedEvent]()
        on_initialized_event = EventType[OnPluginInitializedEvent]()

        exc_has_been_parsed_event.subscribe(
            http_client.send_through_urllib,
        )

        plugin = cls._initialize_plugin(exc_has_been_parsed_event)

        on_initialized_event.notify(
            OnPluginInitializedEvent(event_id=uuid4()),
        )

        return DjangoModule(
            plugins=[plugin],
            events=[exc_has_been_parsed_event, on_initialized_event],
        )


class DjangoModule(IModule):
    """
    Represents the initialized state of the Django module.
    Manages plugins and events for Django exception handling.
    """
    _instance: ClassVar[Optional['DjangoModule']] = None
    _plugins: List[DjangoExceptionPlugin]
    _events: List[EventType]

    def __new__(cls, *args, **kwargs) -> 'DjangoModule':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, plugins: List[DjangoExceptionPlugin], events: List[EventType]) -> None:
        """
        Initializes the Django module with plugins and events.

        Args:
            plugins: List of Django exception plugins
            events: List of event handlers
        """
        self._plugins = plugins
        self._events = events

    @classmethod
    def revert(cls) -> IUninitializedModule:
        """
        Reverts the module to uninitialized state.

        Returns:
            UninitializedDjangoModule: Uninitialized module instance
        """
        for plugin in cls._plugins:
            plugin.revert()

        for event in cls._events:
            event.unsubscribe_all()

        return UninitializedDjangoModule()
