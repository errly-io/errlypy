import atexit
import unittest
from datetime import datetime

import requests
from pact import Consumer, Provider  # type: ignore
from pact.matchers import EachLike, Like, Term  # type: ignore

from errlypy.client.urllib import URLLibClient
from errlypy.models.ingest import ErrorLevel, IngestEvent, IngestRequest

# Test API key constant
TEST_API_KEY = "errly_test_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

# Pact setup
pact = Consumer("ErrlyPythonSDK").has_pact_with(
    Provider("ErrlyGoAPI"), host_name="localhost", port=1234, pact_dir="./pacts"
)

# Start mock server
pact.start_service()
atexit.register(pact.stop_service)


class ErrlySDKPactTest(unittest.TestCase):
    """Consumer tests for Python SDK"""

    def test_successful_event_ingestion(self):
        """Test successful event ingestion"""

        # Expected request body
        expected_body = {
            "events": [
                {
                    "message": "Test error occurred",
                    "environment": "production",
                    "level": "error",
                    "stack_trace": '  File "test.py", line 10, in <module>',
                    "release_version": None,
                    "user_id": None,
                    "user_email": None,
                    "user_ip": None,
                    "browser": None,
                    "os": None,
                    "url": None,
                    "tags": {"component": "test"},
                    "extra": {"user_id": 123},
                    "timestamp": Term(
                        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$",
                        "2024-01-01T10:00:00.000000Z",
                    ),
                }
            ]
        }

        # Expected response
        expected_response = {
            "success": True,
            "message": "Events processed successfully",
            "processed_count": 1,
            "project_id": Term(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                "550e8400-e29b-41d4-a716-446655440000",
            ),
            "timestamp": Like(1234567890),
        }

        # Setup interaction
        (
            pact.given("API key is valid and project exists")
            .upon_receiving("a request to ingest error events")
            .with_request(
                method="POST",
                path="/api/v1/ingest",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": Term(
                        r"^Bearer errly_[a-z0-9]{4}_[a-f0-9]{64}$", f"Bearer {TEST_API_KEY}"
                    ),
                },
                body=expected_body,
            )
            .will_respond_with(
                status=200, headers={"Content-Type": "application/json"}, body=expected_response
            )
        )

        with pact:
            # Create and send event directly through HTTP client
            # (bypass excepthook for test determinism)
            client = URLLibClient(base_url=f"http://localhost:{pact.port}", api_key=TEST_API_KEY)

            # Create event
            event = IngestEvent(
                message="Test error occurred",
                environment="production",
                level=ErrorLevel.ERROR,
                stack_trace='  File "test.py", line 10, in <module>',
                tags={"component": "test"},
                extra={"user_id": 123},
                timestamp=datetime.now(),
            )

            request = IngestRequest(events=[event])

            # Send request
            response = client.post("api/v1/ingest", request)

            # Verify response
            self.assertIsNotNone(response)

    def test_authentication_error(self):
        """Test authentication error"""

        expected_error = {
            "message": "Invalid API key",
            "code": "AUTHENTICATION_ERROR",
            "timestamp": Like(1234567890),
        }

        (
            pact.given("API key is invalid")
            .upon_receiving("a request with invalid API key")
            .with_request(
                method="POST",
                path="/api/v1/ingest",
                headers={"Content-Type": "application/json", "Authorization": "Bearer invalid_key"},
                body={"events": []},
            )
            .will_respond_with(
                status=401, headers={"Content-Type": "application/json"}, body=expected_error
            )
        )

        with pact:
            # Test with invalid key
            response = requests.post(
                f"http://localhost:{pact.port}/api/v1/ingest",
                json={"events": []},
                headers={"Content-Type": "application/json", "Authorization": "Bearer invalid_key"},
            )

            self.assertEqual(response.status_code, 401)
            data = response.json()
            self.assertEqual(data["code"], "AUTHENTICATION_ERROR")

    def test_validation_error(self):
        """Test validation error"""

        expected_error = {
            "message": "At least one event is required",
            "code": "VALIDATION_ERROR",
            "timestamp": Like(1234567890),
        }

        (
            pact.given("API key is valid")
            .upon_receiving("a request with empty events array")
            .with_request(
                method="POST",
                path="/api/v1/ingest",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": Term(
                        r"^Bearer errly_[a-z0-9]{4}_[a-f0-9]{64}$", f"Bearer {TEST_API_KEY}"
                    ),
                },
                body={"events": []},
            )
            .will_respond_with(
                status=400, headers={"Content-Type": "application/json"}, body=expected_error
            )
        )

        with pact:
            response = requests.post(
                f"http://localhost:{pact.port}/api/v1/ingest",
                json={"events": []},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {TEST_API_KEY}",
                },
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data["code"], "VALIDATION_ERROR")

    def test_rate_limiting(self):
        """Test rate limiting"""

        expected_error = {
            "message": "Rate limit exceeded",
            "code": "RATE_LIMIT_EXCEEDED",
            "timestamp": Like(1234567890),
        }

        (
            pact.given("Rate limit is exceeded for API key")
            .upon_receiving("a request exceeding rate limit")
            .with_request(
                method="POST",
                path="/api/v1/ingest",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": Term(
                        r"^Bearer errly_[a-z0-9]{4}_[a-f0-9]{64}$", f"Bearer {TEST_API_KEY}"
                    ),
                },
                body={"events": EachLike({"message": "error", "environment": "production"})},
            )
            .will_respond_with(
                status=429,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": "1000",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": Like("1234567890"),
                },
                body=expected_error,
            )
        )

        with pact:
            # Test rate limiting scenario
            response = requests.post(
                f"http://localhost:{pact.port}/api/v1/ingest",
                json={"events": [{"message": "error", "environment": "production"}]},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {TEST_API_KEY}",
                },
            )

            self.assertEqual(response.status_code, 429)
            data = response.json()
            self.assertEqual(data["code"], "RATE_LIMIT_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
