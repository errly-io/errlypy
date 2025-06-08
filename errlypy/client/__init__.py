from datetime import datetime
from typing import ClassVar, Optional

import aiohttp

from errlypy.client.urllib import URLLibClient
from errlypy.django.events import OnDjangoExceptionHasBeenParsedEvent
from errlypy.internal.config import HTTPErrorConfig
from errlypy.models.ingest import ErrorLevel, IngestEvent, IngestRequest


class UninitializedHTTPClient:
    @classmethod
    def setup(cls, base_url: str, api_key: str, environment: str = "production") -> "HTTPClient":
        return HTTPClient(client=URLLibClient(base_url, api_key), environment=environment)


class HTTPClient:
    _instance: ClassVar[Optional["HTTPClient"]] = None
    _client: URLLibClient
    _environment: str

    def __new__(cls, *args, **kwargs) -> "HTTPClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, client: URLLibClient, environment: str = "production") -> None:
        self._client = client
        self._environment = environment

    @classmethod
    async def send_through_aiohttp(cls, data):
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            session.post(cls.url, json=data)

    def send_through_urllib(self, data):
        if hasattr(data, "data"):  # OnDjangoExceptionHasBeenParsedEvent
            parsed_exception = data.data
            ingest_event = self._transform_to_ingest_event(parsed_exception)
            ingest_request = IngestRequest(events=[ingest_event])

            self._client.post(
                HTTPErrorConfig.endpoint,
                ingest_request,
            )
        else:
            # Backward compatibility
            self._client.post(
                HTTPErrorConfig.endpoint,
                data,
            )

    def _transform_to_ingest_event(self, parsed_exception) -> IngestEvent:
        """Transform ParsedExceptionDto to IngestEvent"""
        # Collect stack trace from frames
        stack_trace_lines = []
        for frame in parsed_exception.frames:
            line = f'  File "{frame.filename}", line {frame.lineno}, in {frame.function}'
            stack_trace_lines.append(line)
            if frame.line:
                stack_trace_lines.append(f"    {frame.line}")

        stack_trace = "\n".join(stack_trace_lines) if stack_trace_lines else None

        # Extract additional information from frames
        tags = {}
        if parsed_exception.frames:
            # First and last files as tags
            tags["first_file"] = parsed_exception.frames[0].filename
            tags["last_file"] = parsed_exception.frames[-1].filename
            tags["error_function"] = parsed_exception.frames[-1].function

        return IngestEvent(
            message=parsed_exception.content,
            environment=self._environment,  # Use from configuration
            level=ErrorLevel.ERROR,
            stack_trace=stack_trace,
            tags=tags,
            extra={"frame_count": len(parsed_exception.frames)},
            timestamp=datetime.now(),
        )

    def notify(self, event: OnDjangoExceptionHasBeenParsedEvent):
        self.send_through_urllib(event)
