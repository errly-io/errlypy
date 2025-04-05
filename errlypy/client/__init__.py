from typing import ClassVar, Optional

import aiohttp

from errlypy.client.urllib import URLLibClient
from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.internal.config import HTTPErrorConfig


class UninitializedHTTPClient:
    @classmethod
    def setup(cls, base_url: str, api_key: str) -> 'HTTPClient':
        return HTTPClient(client=URLLibClient(base_url, api_key))


class HTTPClient:
    _instance: ClassVar[Optional['HTTPClient']] = None
    _client: URLLibClient

    def __new__(cls, *args, **kwargs) -> 'HTTPClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, client: URLLibClient) -> None:
        self._client = client

    @classmethod
    async def send_through_aiohttp(cls, data):
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            session.post(cls.url, json=data)

    def send_through_urllib(self, data):
        self._client.post(
            HTTPErrorConfig.endpoint,
            data.data,
        )

    def notify(self, event: OnDjangoExceptionHasBeenParsedEvent):
        self.send_through_urllib(event)
