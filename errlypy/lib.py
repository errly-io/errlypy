from typing import ClassVar, List, Optional, Union

from errlypy.api import IModule, IModuleController, IUninitializedModuleController
from errlypy.django.module import UninitializedDjangoModule
from errlypy.excepthook.module import UninitializedExceptHookModule
from errlypy.internal.event.type import EventType


class UninitializedModuleController(
    IUninitializedModuleController,
):
    @staticmethod
    def init(base_url: str, api_key: str) -> Union["IModuleController", "IUninitializedModuleController"]:
        django_module = UninitializedDjangoModule.setup(base_url=base_url, api_key=api_key)
        excepthook_module = UninitializedExceptHookModule.setup(base_url=base_url, api_key=api_key)
        modules = [django_module, excepthook_module]

        initialized_modules = [module for module in modules if isinstance(module, IModule)]

        has_been_initialized = len(initialized_modules) > 0

        if not has_been_initialized:
            return UninitializedModuleController()

        module_controller = ModuleController(
            modules=initialized_modules,
            events=[],
        )

        return module_controller


class ModuleController(IModuleController):
    _instance: ClassVar[Optional['ModuleController']] = None
    _modules: List[IModule]
    _events: List[EventType]

    def __new__(cls, *args, **kwargs) -> 'ModuleController':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, modules: List[IModule], events: List[EventType]) -> None:
        self._modules = modules
        self._events = events

    def revert(self) -> UninitializedModuleController:
        for module in self._modules:
            module.revert()

        for event in self._events:
            event.unsubscribe_all()

        return UninitializedModuleController()

        # on_destroyed_event_instance = EventType[OnPluginDestroyedEvent]()

        # for plugin in self.registry.values():
        #     plugin.revert()
        #     on_destroyed_event_instance.notify(
        #         OnPluginDestroyedEvent(event_id=uuid4()),
        #     )

        # return UninitializedModuleController()


class Errly:
    _module_controller: IModuleController

    @classmethod
    def init(
        cls,
        *,
        url: str,
        api_key: str,
    ):
        controller = UninitializedModuleController.init(base_url=url, api_key=api_key)

        if isinstance(controller, IUninitializedModuleController):
            raise ValueError("No modules have been initialized")

        cls._module_controller = controller
