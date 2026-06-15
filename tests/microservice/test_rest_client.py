import asyncio
import http
import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import aiohttp
from weaver_framework.microservice.http_content_type import HttpContentType
from weaver_framework.microservice.rest_client import RestClient


class MockResponse:

    def __init__(
            self,
            *,
            status=http.HTTPStatus.OK,
            body="",
            content_type=HttpContentType.JSON,
            headers=None):

        self.status = status
        self._body = body
        self.content_type = content_type
        self.headers = headers or {}

    async def text(self):
        return self._body


class TestRestClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self._session = MagicMock(spec=aiohttp.ClientSession)

        self._client = RestClient(self._session)

    async def test_get_request_returns_json_response(self):

        response = MockResponse(
            body='{"username": "paul"}',
            content_type=HttpContentType.JSON
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        result = await self._client.get(
            "https://example.com"
        )

        self.assertEqual(
            http.HTTPStatus.OK,
            result.status_code
        )

        self.assertEqual(
            {"username": "paul"},
            result.body
        )

    async def test_get_request_returns_text_response(self):

        response = MockResponse(
            body="hello world",
            content_type=HttpContentType.TEXT
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        result = await self._client.get(
            "https://example.com"
        )

        self.assertEqual(
            "hello world",
            result.body
        )

    async def test_get_request_with_empty_body_returns_none(self):

        response = MockResponse(
            body="",
            content_type=HttpContentType.TEXT
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        result = await self._client.get(
            "https://example.com"
        )

        self.assertIsNone(
            result.body
        )

    async def test_get_request_with_invalid_json_returns_error_response(
            self):

        response = MockResponse(
            body="{invalid json}",
            content_type=HttpContentType.JSON
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        result = await self._client.get(
            "https://example.com"
        )

        self.assertEqual(
            http.HTTPStatus.OK,
            result.status_code
        )

        self.assertIsNotNone(
            result.exception_msg
        )

    async def test_get_request_handles_connection_error(self):

        self._session.request.side_effect = (
            aiohttp.ClientConnectionError("Connection failed")
        )

        result = await self._client.get(
            "https://example.com"
        )

        self.assertEqual(
            http.HTTPStatus.SERVICE_UNAVAILABLE,
            result.status_code
        )

        self.assertIn(
            "Connection failed",
            result.exception_msg
        )

    async def test_get_request_handles_timeout_error(self):

        self._session.request.side_effect = (
            asyncio.TimeoutError("Timed out")
        )

        result = await self._client.get(
            "https://example.com"
        )

        self.assertEqual(
            http.HTTPStatus.GATEWAY_TIMEOUT,
            result.status_code
        )

    async def test_post_request_passes_json_headers_and_params(self):

        response = MockResponse(
            body='{"success": true}',
            content_type=HttpContentType.JSON
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        headers = {
            "Authorization": "Bearer token"
        }

        params = {
            "page": 1
        }

        json_data = {
            "username": "paul"
        }

        await self._client.post(
            "https://example.com",
            json_data=json_data,
            headers=headers,
            params=params,
            timeout=5
        )

        self._session.request.assert_called_once()

        _, kwargs = self._session.request.call_args

        self.assertEqual(
            json_data,
            kwargs["json"]
        )

        self.assertEqual(
            headers,
            kwargs["headers"]
        )

        self.assertEqual(
            params,
            kwargs["params"]
        )

    async def test_put_uses_put_http_method(self):

        response = MockResponse()

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        await self._client.put(
            "https://example.com"
        )

        args, _ = self._session.request.call_args

        self.assertEqual(
            "PUT",
            args[0]
        )

    async def test_patch_uses_patch_http_method(self):

        response = MockResponse()

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        await self._client.patch(
            "https://example.com"
        )

        args, _ = self._session.request.call_args

        self.assertEqual(
            "PATCH",
            args[0]
        )

    async def test_delete_uses_delete_http_method(self):

        response = MockResponse()

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = response

        self._session.request.return_value = mock_context

        await self._client.delete(
            "https://example.com"
        )

        args, _ = self._session.request.call_args

        self.assertEqual(
            "DELETE",
            args[0]
        )
