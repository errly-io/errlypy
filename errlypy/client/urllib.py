import json
import logging
import urllib.request
from typing import Any
from urllib.error import HTTPError, URLError

from errlypy.internal.encoder import DataclassJsonEncoder

logger = logging.getLogger(__file__)


class URLLibClient:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url.rstrip("/")  # Remove trailing slash
        self._api_key = api_key
        self.setup_dns_cache()

    def get(self, url: str) -> Any:
        with urllib.request.urlopen(url) as response:
            return response.read()

    def post(self, url, data) -> None:
        json_data = json.dumps(data, cls=DataclassJsonEncoder).encode("utf-8")

        # Debug logging only if DEBUG level is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Sending POST to {self._base_url}/{url}")
            logger.debug(f"Data: {json_data.decode('utf-8')}")

        request = urllib.request.Request(
            f"{self._base_url}/{url}",
            data=json_data,
            headers=self.headers(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode("utf-8")
                return response_data
        except HTTPError as e:
            # Read error body only once
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                error_body = "Unable to read error body"

            logger.error(f"HTTP Error {e.code}: {error_body}")
        except URLError as exc:
            logger.warning(f"Unable to post to Errly: {exc.reason}")
            # Don't interrupt application due to network errors

    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    def setup_dns_cache(self):
        opener = urllib.request.build_opener()
        urllib.request.install_opener(opener)
