import json
import logging
import urllib.request
from typing import Any
from urllib.error import URLError

from errlypy.internal.encoder import DataclassJsonEncoder

logger = logging.getLogger(__file__)


class URLLibClient:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self.setup_dns_cache()

    def get(self, url: str) -> Any:
        with urllib.request.urlopen(url) as response:
            return response.read()

    def post(self, url, data) -> None:
        json_data = json.dumps(data, cls=DataclassJsonEncoder).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/{url}", data=json_data, method="POST"
        )
        request.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(request) as response:
                return response.read().decode("utf-8")
        except URLError as exc:
            logger.warning(f"Unable to post: {exc.reason}")

    def setup_dns_cache(self):
        opener = urllib.request.build_opener()
        urllib.request.install_opener(opener)
