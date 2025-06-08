import re
from dataclasses import dataclass


@dataclass
class ErrlyConfig:
    base_url: str
    api_key: str
    environment: str = "production"
    debug: bool = False
    timeout: int = 30
    max_retries: int = 3

    def validate_api_key(self) -> bool:
        pattern = r"^errly_[a-z0-9]{4}_[a-f0-9]{64}$"
        return bool(re.match(pattern, self.api_key))
