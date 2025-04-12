from typing import ClassVar, List, Optional, Union
from uuid import uuid4

from fastapi import FastAPI

from errlypy.api import IModule, IUninitializedModule
from errlypy.client import HTTPClient
from errlypy.client.urllib import URLLibClient
from errlypy.fastapi.events import OnFastAPIExceptionHasBeenParsedEvent
from errlypy.fastapi.plugin import FastAPIExceptionPlugin
from errlypy.internal.event.on_plugin_initialized import OnPluginInitializedEvent
from errlypy.internal.event.type import EventType


class UninitializedFastAPIModule(IUninitializedModule):
    """
    Represents the uninitialized state of the FastAPI module.
    Handles configuration and initialization of FastAPI components.
    """

    _instance: ClassVar[Optional["UninitializedFastAPIModule"]] = None

    def __new__(cls) -> "UninitializedFastAPIModule":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _initialize_plugin(
        exc_has_been_parsed_event: EventType[OnFastAPIExceptionHasBeenParsedEvent],
        app: Optional[FastAPI] = None,
    ) -> FastAPIExceptionPlugin:
        """Initializes and sets up the FastAPI exception plugin."""
        plugin = FastAPIExceptionPlugin(exc_has_been_parsed_event, app=app)
        plugin.setup()

        return plugin

    @staticmethod
    def _verify_fastapi_installed() -> bool:
        """Verifies that FastAPI is installed in the environment."""
        try:
            import fastapi  # noqa: F401
        except ImportError:
            return False

        return True

    @classmethod
    def setup(
        cls,
        base_url: str,
        api_key: str,
        app: Optional[FastAPI] = None,
        plugin: Optional[FastAPIExceptionPlugin] = None,
    ) -> Union["IModule", "IUninitializedModule"]:
        """
        Initializes the FastAPI module and transitions to initialized state.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            app: Optional FastAPI app instance to register immediately
            plugin: Optional custom FastAPIExceptionPlugin instance

        Returns:
            FastAPIModule: Initialized FastAPI module instance

        Raises:
            ValueError: If module is not configured
            ImportError: If FastAPI is not installed
            RuntimeError: If initialization sequence is invalid
        """
        if not cls._verify_fastapi_installed():
            return UninitializedFastAPIModule()

        http_client = HTTPClient(
            client=URLLibClient(
                base_url=base_url,
                api_key=api_key,
            ),
        )

        exc_has_been_parsed_event = EventType[OnFastAPIExceptionHasBeenParsedEvent]()
        on_initialized_event = EventType[OnPluginInitializedEvent]()

        exc_has_been_parsed_event.subscribe(
            http_client.send_through_urllib,
        )

        if plugin is not None:
            plugin._on_exc_has_been_parsed_event_instance = exc_has_been_parsed_event
            if app is not None and plugin._app is None:
                plugin.register_app(app)
            plugin.setup()
            final_plugin = plugin
        else:
            final_plugin = cls._initialize_plugin(exc_has_been_parsed_event, app=app)

        on_initialized_event.notify(
            OnPluginInitializedEvent(event_id=uuid4()),
        )

        return FastAPIModule(
            plugins=[final_plugin],
            events=[exc_has_been_parsed_event, on_initialized_event],
        )


class FastAPIModule(IModule):
    """
    Represents the initialized state of the FastAPI module.
    Manages plugins and events for FastAPI exception handling.
    """

    _instance: ClassVar[Optional["FastAPIModule"]] = None
    _plugins: List[FastAPIExceptionPlugin]
    _events: List[EventType]

    def __new__(cls, *args, **kwargs) -> "FastAPIModule":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, plugins: List[FastAPIExceptionPlugin], events: List[EventType]) -> None:
        """
        Initializes the FastAPI module with plugins and events.

        Args:
            plugins: List of FastAPI exception plugins
            events: List of event handlers
        """
        self._plugins = plugins
        self._events = events

    def register_app(self, app: FastAPI) -> None:
        """
        Registers a FastAPI application with all plugins.

        Args:
            app: FastAPI application instance
        """
        for plugin in self._plugins:
            plugin.register_app(app)

    def get_plugin(self) -> Optional[FastAPIExceptionPlugin]:
        """
        Returns the FastAPI exception plugin.

        Returns:
            FastAPIExceptionPlugin: The plugin instance or None if no plugins
        """
        return self._plugins[0] if self._plugins else None

    @classmethod
    def revert(cls) -> IUninitializedModule:
        """
        Reverts the module to uninitialized state.

        Returns:
            UninitializedFastAPIModule: Uninitialized module instance
        """
        for plugin in cls._plugins:
            plugin.revert()

        for event in cls._events:
            event.unsubscribe_all()

        return UninitializedFastAPIModule()
