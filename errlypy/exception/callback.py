import sys
import traceback
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Dict, Optional, Type, cast

from errlypy.api import ExceptionCallback, ExceptionCallbackWithContext, Extractor
from errlypy.client.credentials import Credentials
from errlypy.exception import FrameDetail, ParsedExceptionDto
from errlypy.exception.stack import StackSummaryWrapper
from errlypy.utils import has_contract_been_implemented


@dataclass(frozen=True)
class CreateExceptionCallbackMeta:
    dry_mode: bool = False
    credentials: Optional[Credentials] = None


class FrameExtractor(Extractor):
    def extract(self, raw_data: traceback.FrameSummary) -> FrameDetail:
        return FrameDetail(
            filename=raw_data.filename,
            function=raw_data.name,
            lineno=raw_data.lineno,
            line=raw_data.line,
            locals=raw_data.locals,
        )


class BaseExceptionCallbackImpl(ExceptionCallback):
    _context: Dict[str, Any]
    _meta: CreateExceptionCallbackMeta

    @classmethod
    def create(
        cls, context: Dict[str, Any], meta: CreateExceptionCallbackMeta
    ) -> "BaseExceptionCallbackImpl":
        instance = cls()
        instance._context = context
        instance._meta = meta

        return instance

    def set_next(self, callback: "ExceptionCallback") -> "ExceptionCallback":
        self._next_callback = callback
        return callback


class ExceptionCallbackImpl(BaseExceptionCallbackImpl):
    def __call__(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ) -> ParsedExceptionDto:
        response = ParsedExceptionDto(content=str(exc_value))
        python_lib_paths = sys.prefix, sys.base_prefix
        frame_extractor = FrameExtractor()

        stack_summary_wrapper = StackSummaryWrapper()
        frames = stack_summary_wrapper.extract(
            traceback.walk_tb(exc_traceback), capture_locals=True
        )

        for frame in frames:
            has_lib_path = next(
                (True for lib_path in python_lib_paths if frame.filename.startswith(lib_path)),
                False,
            )

            if has_lib_path:
                continue

            response.frames.append(frame_extractor.extract(frame))

        if self._next_callback is None:
            return response

        if has_contract_been_implemented(self._next_callback, ExceptionCallbackWithContext):
            self._next_callback = cast(ExceptionCallbackWithContext, self._next_callback)
            # TODO: Create dataclass for context
            self._next_callback.set_context(response)

        return self._next_callback(exc_type, exc_value, exc_traceback)
