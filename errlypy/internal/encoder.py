import dataclasses
import json
from uuid import UUID


class DataclassJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)
