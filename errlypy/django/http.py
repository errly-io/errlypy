import aiohttp

from errlypy.client.urllib import URLLibClient
from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.internal.config import HTTPErrorConfig


# FIXME: Problem - cannot validate connection (it's valid or not) on init state, not in runtime
class DjangoHTTPCallbackImpl:
    headers = None
    urllib_client = None

    @classmethod
    def initialize(cls, base_url: str, api_key: str):
        cls.urllib_client = URLLibClient(base_url, api_key)

    @classmethod
    async def send_through_aiohttp(cls, data):
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            session.post(cls.url, json=data)

    @classmethod
    def send_through_urllib(cls, data):
        cls.urllib_client.post(
            HTTPErrorConfig.endpoint,
            {"content": data["error"], "frames": data["frames"]},
        )

    @classmethod
    def notify(cls, event: OnDjangoExceptionHasBeenParsedEvent):
        cls.send_through_urllib(event)
