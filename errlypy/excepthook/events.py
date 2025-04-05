from dataclasses import dataclass

from errlypy.exception import ParsedExceptionDto
from errlypy.internal.event import Event


@dataclass(frozen=True)
class OnExceptionHasBeenParsedEvent(Event):
    data: ParsedExceptionDto
