from typing import Optional, Type
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from errlypy.api import IPlugin
from errlypy.exception.callback import CreateExceptionCallbackMeta, ExceptionCallbackImpl
from errlypy.fastapi.events import OnFastAPIExceptionHasBeenParsedEvent
from errlypy.internal.event.type import EventType


class FastAPIExceptionPlugin(IPlugin):
    def __init__(
        self,
        on_exc_has_been_parsed_event_instance: EventType[OnFastAPIExceptionHasBeenParsedEvent],
        app: Optional[FastAPI] = None,
    ) -> None:
        self._on_exc_has_been_parsed_event_instance = on_exc_has_been_parsed_event_instance
        self._app: Optional[FastAPI] = app
        self._callback = ExceptionCallbackImpl.create({}, CreateExceptionCallbackMeta())
        self._middleware_class: Optional[Type] = None

        if self._app is not None:
            self.register_app(self._app)

    def setup(self):
        pass

    def register_app(self, app: FastAPI):
        """Registers the plugin for a FastAPI application"""
        self._app = app

        plugin = self

        class ErrlyExceptionMiddleware(BaseHTTPMiddleware):
            async def dispatch(
                self, request: Request, call_next: RequestResponseEndpoint
            ) -> Response:
                try:
                    return await call_next(request)
                except Exception as exc:
                    exc_type = type(exc)
                    exc_value = exc
                    exc_traceback = exc.__traceback__

                    response = plugin._callback(exc_type, exc_value, exc_traceback)

                    plugin._on_exc_has_been_parsed_event_instance.notify(
                        OnFastAPIExceptionHasBeenParsedEvent(event_id=uuid4(), data=response),
                    )

                    raise

        app.add_middleware(ErrlyExceptionMiddleware)

        self._middleware_class = ErrlyExceptionMiddleware

    def revert(self):
        """Removes the middleware from the FastAPI application"""
        if self._app is not None and self._middleware_class is not None:
            middlewares = [m for m in self._app.user_middleware if m.cls != self._middleware_class]

            self._app.user_middleware = middlewares

            self._app.middleware_stack = None

    def __call__(self, *args, **kwargs):
        exc_type = args[0] if len(args) > 0 else kwargs.get("exc_type")
        exc_value = args[1] if len(args) > 1 else kwargs.get("exc_value")
        exc_traceback = args[2] if len(args) > 2 else kwargs.get("exc_traceback")

        if not all([exc_type, exc_value, exc_traceback]):
            raise ValueError("Missing required arguments: exc_type, exc_value, exc_traceback")

        response = self._callback(exc_type, exc_value, exc_traceback)

        self._on_exc_has_been_parsed_event_instance.notify(
            OnFastAPIExceptionHasBeenParsedEvent(event_id=uuid4(), data=response),
        )

        return response
