import asyncio
import asyncio.coroutines
import inspect
from typing import Any, Callable, Coroutine, Generic, List, TypeVar, Union

T = TypeVar("T")


class EventType(Generic[T]):
    def __init__(self) -> None:
        self._subscribers: List[
            Union[Callable[[T], None], Callable[[T], Coroutine[Any, Any, None]]]
        ] = []

    def subscribe(
        self,
        callback: Union[Callable[[T], None], Callable[[T], Coroutine[Any, Any, None]]],
    ) -> None:
        self._subscribers.append(callback)

    def unsubscribe(
        self,
        callback: Union[Callable[[T], None], Callable[[T], Coroutine[Any, Any, None]]],
    ) -> None:
        self._subscribers.remove(callback)

    def unsubscribe_all(self) -> None:
        self._subscribers = []

    def notify(self, message: T) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        for subscriber in self._subscribers:
            if inspect.iscoroutinefunction(subscriber):
                if loop:
                    loop.create_task(subscriber(message))
                else:
                    asyncio.run(subscriber(message))
            else:
                subscriber(message)
