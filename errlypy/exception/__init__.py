from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FrameDetail:
    filename: str
    function: str
    lineno: Optional[int]
    line: Optional[str]
    locals: Optional[Dict[str, str]]


@dataclass(frozen=True)
class ParsedExceptionDto:
    content: str
    frames: List[FrameDetail] = field(default_factory=list)
