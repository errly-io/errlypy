from typing import ClassVar, List, Optional, Union
from uuid import uuid4

from errlypy.api import IModule, IPlugin, IUninitializedModule
from errlypy.client import HTTPClient
from errlypy.client.urllib import URLLibClient
from errlypy.excepthook.events import OnExceptionHasBeenParsedEvent
from errlypy.excepthook.plugin import ExceptHookPlugin
from errlypy.internal.event.on_plugin_initialized import OnPluginInitializedEvent
from errlypy.internal.event.type import EventType


class UninitializedExceptHookModule(IUninitializedModule):
    _instance: ClassVar[Optional['UninitializedExceptHookModule']] = None

    def __new__(cls) -> 'UninitializedExceptHookModule':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _initialize_plugin(on_exception_has_been_parsed_event: EventType[OnExceptionHasBeenParsedEvent]) -> ExceptHookPlugin:
        plugin = ExceptHookPlugin(on_exception_has_been_parsed_event)
        plugin.setup()

        return plugin

    @classmethod
    def setup(cls, base_url: str, api_key: str) -> Union['ExceptHookModule', 'UninitializedExceptHookModule']:
        http_client = HTTPClient(
            client=URLLibClient(
                base_url=base_url,
                api_key=api_key,
            ),
        )

        exc_has_been_parsed_event = EventType[OnExceptionHasBeenParsedEvent]()
        on_initialized_event = EventType[OnPluginInitializedEvent]()

        exc_has_been_parsed_event.subscribe(
            http_client.send_through_urllib,
        )

        plugin = cls._initialize_plugin(exc_has_been_parsed_event)

        on_initialized_event.notify(
            OnPluginInitializedEvent(event_id=uuid4()),
        )

        return ExceptHookModule(plugins=[plugin])

class ExceptHookModule(IModule):
    _instance: ClassVar[Optional['ExceptHookModule']] = None
    _plugins: List[IPlugin]

    def __new__(cls, *args, **kwargs) -> 'ExceptHookModule':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, plugins: List[IPlugin]) -> None:
        self._plugins = plugins

    @classmethod
    def revert(cls) -> IUninitializedModule:
        for plugin in cls._plugins:
            plugin.revert()

        return UninitializedExceptHookModule()
