from typing import ClassVar, List, Optional, Union

from errlypy.api import IModule, IModuleController, IUninitializedModuleController
from errlypy.config import ErrlyConfig
from errlypy.django.module import UninitializedDjangoModule
from errlypy.excepthook.module import UninitializedExceptHookModule
from errlypy.fastapi.module import UninitializedFastAPIModule
from errlypy.internal.event.type import EventType


class UninitializedModuleController(
    IUninitializedModuleController,
):
    @staticmethod
    def init(
        base_url: str, api_key: str, environment: str = "production"
    ) -> Union["IModuleController", "IUninitializedModuleController"]:
        config = ErrlyConfig(base_url=base_url, api_key=api_key, environment=environment)

        if not config.validate_api_key():
            raise ValueError(
                f"Invalid API key format. Expected: errly_XXXX_{'X' * 64} where X is alphanumeric"
            )

        django_module = UninitializedDjangoModule.setup(
            base_url=base_url, api_key=api_key, environment=environment
        )
        excepthook_module = UninitializedExceptHookModule.setup(
            base_url=base_url, api_key=api_key, environment=environment
        )
        fastapi_module = UninitializedFastAPIModule.setup(
            base_url=base_url, api_key=api_key, environment=environment
        )

        modules = [django_module, excepthook_module, fastapi_module]
        initialized_modules = [module for module in modules if isinstance(module, IModule)]

        has_been_initialized = len(initialized_modules) > 0

        if not has_been_initialized:
            return UninitializedModuleController()

        module_controller = ModuleController(
            modules=initialized_modules,
            events=[],
            config=config,
        )

        return module_controller


class ModuleController(IModuleController):
    _instance: ClassVar[Optional["ModuleController"]] = None
    _modules: List[IModule]
    _events: List[EventType]
    _config: ErrlyConfig

    def __new__(cls, *args, **kwargs) -> "ModuleController":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, modules: List[IModule], events: List[EventType], config: ErrlyConfig
    ) -> None:
        self._modules = modules
        self._events = events
        self._config = config

    def revert(self) -> UninitializedModuleController:
        for module in self._modules:
            module.revert()

        for event in self._events:
            event.unsubscribe_all()

        return UninitializedModuleController()


class Errly:
    _module_controller: IModuleController

    @classmethod
    def init(
        cls,
        *,
        url: str,
        api_key: str,
        environment: str = "production",
    ):
        # Normalize URL
        if url.endswith("/"):
            url = url[:-1]

        controller = UninitializedModuleController.init(
            base_url=url, api_key=api_key, environment=environment
        )

        if isinstance(controller, IUninitializedModuleController):
            raise ValueError("No modules have been initialized")

        cls._module_controller = controller
