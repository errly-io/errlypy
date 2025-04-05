from abc import ABC, abstractmethod
from collections import OrderedDict
from types import TracebackType
from typing import Any, Optional, Type, Union

from errlypy.exception import ParsedExceptionDto


class ExceptionCallback(ABC):
    _next_callback: Optional["ExceptionCallback"] = None

    @abstractmethod
    def set_next(self, callback: "ExceptionCallback") -> "ExceptionCallback":
        pass

    @abstractmethod
    def __call__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ) -> ParsedExceptionDto:
        pass


class ExceptionCallbackWithContext(ExceptionCallback):
    @abstractmethod
    def set_context(self, data: ParsedExceptionDto) -> None:
        pass


class Extractor(ABC):
    @abstractmethod
    def extract(self, raw_data: Any) -> Any:
        pass


class IPlugin(ABC):
    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def revert(self) -> None:
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class IUninitializedModule(ABC):
    @classmethod
    @abstractmethod
    def setup(cls, base_url: str, api_key: str) -> Union["IModule", "IUninitializedModule"]:
        pass


class IModule(ABC):
    @classmethod
    @abstractmethod
    def revert(cls) -> IUninitializedModule:
        pass


class IUninitializedModuleController(ABC):
    @classmethod
    @abstractmethod
    def init(
        cls, base_url: str, api_key: str
    ) -> Union["IModuleController", "IUninitializedModuleController"]:
        pass


class IModuleController(ABC):
    _registry: OrderedDict[type, IPlugin]

    @abstractmethod
    def revert(self) -> IUninitializedModuleController:
        pass
