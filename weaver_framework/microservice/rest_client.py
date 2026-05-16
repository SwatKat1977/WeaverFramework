"""
Copyright 2026 Weaver Framework Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import asyncio
import json
import http
import aiohttp
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.http_content_type import HttpContentType


class RestClient:
    """Asynchronous REST client for making HTTP API requests.

    This client provides convenience wrappers around common HTTP methods
    (GET, POST, PATCH, and DELETE) using ``aiohttp``. Responses are
    normalized into ``ApiResponse`` objects to provide a consistent
    interface for handling response data, status codes, headers, and
    request errors.

    The client automatically handles:
        * Request timeouts.
        * Connection and client errors.
        * JSON response parsing.
        * Conversion of responses into ``ApiResponse`` objects.

    Attributes:
        _http_session: The underlying ``aiohttp.ClientSession`` used for
            executing HTTP requests.
    """
    __slots__ = ["_http_session"]

    def __init__(self, http_session: aiohttp.ClientSession) -> None:
        self._http_session = http_session

    async def call_api_post(self, url: str,
                            json_data: dict | None = None,
                            timeout: int = 2) -> ApiResponse:
        """Send an asynchronous HTTP POST request to an API endpoint.

        Args:
            url: The target API endpoint URL.
            json_data: Optional JSON payload to include in the request body.
            timeout: Total request timeout in seconds.

        Returns:
            An ``ApiResponse`` object containing the parsed response data
            or exception details if the request failed.

        Raises:
            This method does not raise exceptions directly. Connection and
            timeout errors are caught and returned inside the ``ApiResponse``.
        """

        try:
            async with self._http_session.post(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    json=json_data) as response:
                return await self._parse_response(response)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            return ApiResponse(status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                               exception_msg=str(ex))

        except asyncio.TimeoutError as ex:
            return ApiResponse(status_code=http.HTTPStatus.GATEWAY_TIMEOUT,
                               exception_msg=str(ex))

    async def call_api_get(self, url: str,
                           timeout: int = 2) -> ApiResponse:
        """
        Make an API call using the GET method.

        Args:
            url: URL of the endpoint.
            timeout: Total request timeout in seconds.

        Returns:
            ApiResponse which will contain response data or just
            exception_msg if something went wrong.
        """

        try:

            async with self._http_session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return await self._parse_response(response)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            return ApiResponse(status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                               exception_msg=str(ex))

        except asyncio.TimeoutError as ex:
            return ApiResponse(status_code=http.HTTPStatus.GATEWAY_TIMEOUT,
                               exception_msg=str(ex))

    async def call_api_delete(self, url: str,
                              json_data: dict | None = None,
                              timeout: int = 2) -> ApiResponse:
        """
        Make an API call using the DELETE method.

        Args:
            url: URL of the endpoint
            json_data: Optional Json body.
            timeout: Total request timeout in seconds.

        Returns:
            ApiResponse which will contain response data or just
            exception_msg if something went wrong.
        """

        try:
            async with self._http_session.delete(
                    url,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return await self._parse_response(response)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            return ApiResponse(status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                               exception_msg=str(ex))

        except asyncio.TimeoutError as ex:
            return ApiResponse(status_code=http.HTTPStatus.GATEWAY_TIMEOUT,
                               exception_msg=str(ex))

    async def call_api_patch(self, url: str,
                             json_data: dict | None = None,
                             timeout: int = 2) -> ApiResponse:
        """
        Make an API call using the PATCH method.

        Args:
            url: URL of the endpoint
            json_data: Optional Json body.
            timeout: Total request timeout in seconds.

        Returns:
            ApiResponse which will contain response data or just
            exception_msg if something went wrong.
        """

        try:
            async with self._http_session.patch(
                    url,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return await self._parse_response(response)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            return ApiResponse(status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                               exception_msg=str(ex))

        except asyncio.TimeoutError as ex:
            return ApiResponse(status_code=http.HTTPStatus.GATEWAY_TIMEOUT,
                               exception_msg=str(ex))

    async def _parse_response(
            self,
            response: aiohttp.ClientResponse) -> ApiResponse:
        """
        Parse an aiohttp response into a standard ApiResponse object.

        Args:
            response:
                The aiohttp response object.

        Returns:
            ApiResponse containing the parsed response data.
        """

        try:
            raw_body = await response.text()

            if raw_body == "":
                body = None

            elif HttpContentType.JSON in response.content_type:
                body = json.loads(raw_body)

            else:
                body = raw_body

        except (
                aiohttp.ClientError,
                aiohttp.ContentTypeError,
                json.JSONDecodeError) as ex:

            return ApiResponse(
                status_code=response.status,
                headers=dict(response.headers),
                exception_msg=str(ex),
                content_type=response.content_type)

        return ApiResponse(
            status_code=response.status,
            headers=dict(response.headers),
            body=body,
            content_type=response.content_type)
