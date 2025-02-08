from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    endpoint: str
    client_id: str
    client_secret: str
