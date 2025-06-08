from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class IngestEvent:
    message: str
    environment: str
    level: ErrorLevel = ErrorLevel.ERROR
    stack_trace: Optional[str] = None
    release_version: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_ip: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    url: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None


@dataclass
class IngestRequest:
    events: List[IngestEvent]
