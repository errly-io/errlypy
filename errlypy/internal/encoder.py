import dataclasses
import json
from datetime import datetime
from enum import Enum
from uuid import UUID


class DataclassJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            # Filter None values for omitempty compatibility
            data = dataclasses.asdict(o)
            # Remove None values (Go omitempty)
            return {k: v for k, v in data.items() if v is not None}
        if isinstance(o, UUID):
            return str(o)
        # Support for datetime
        if isinstance(o, datetime):
            # RFC3339 format for Go compatibility
            return o.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # Support for Enum
        if isinstance(o, Enum):
            return o.value
        return super().default(o)
