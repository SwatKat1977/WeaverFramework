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
from collections.abc import Mapping
import json
import http
from typing import Any, TypeAlias
import aiohttp
from .api_response import ApiResponse
from .http_content_type import HttpContentType

Headers: TypeAlias = Mapping[str, str]
QueryParams: TypeAlias = Mapping[str, str | int | float]


class RestClient:
    """Asynchronous REST client for executing HTTP API requests.

    This client provides convenience wrappers around common HTTP methods
    using ``aiohttp``. Responses are normalized into ``ApiResponse``
    objects to provide a consistent interface for handling response data,
    status codes, headers, and request errors.

    The client automatically handles:
        * Request timeouts.
        * Connection and client errors.
        * JSON response parsing.
        * Conversion of responses into ``ApiResponse`` objects.

    Attributes:
        _http_session: Underlying ``aiohttp.ClientSession`` used to
            execute HTTP requests.
    """
    __slots__ = ["_http_session"]

    def __init__(self, http_session: aiohttp.ClientSession) -> None:
        self._http_session = http_session

    async def post(self, url: str,
                   json_data: dict | None = None,
                   headers: Headers | None = None,
                   params: QueryParams | None = None,
                   timeout: int = 2) -> ApiResponse:
        """Send an HTTP POST request.

        Args:
            url: Target API endpoint URL.
            json_data: Optional JSON payload to include in the request body.
            headers: Optional HTTP headers to include with the request.
            params: Optional query parameters to include with the request.
            timeout: Total request timeout in seconds.

        Returns:
            Normalized API response.
        """
        return await self._request("POST",
                                   url,
                                   json_data=json_data,
                                   timeout=timeout,
                                   params=params,
                                   headers=headers)

    async def get(self,
                  url: str,
                  headers: Headers | None = None,
                  params: QueryParams | None = None,
                  timeout: int = 2) -> ApiResponse:
        """Send an HTTP GET request.

        Args:
            url: Target API endpoint URL.
            headers: Optional HTTP headers to include with the request.
            params: Optional query parameters to include with the request.
            timeout: Total request timeout in seconds.

        Returns:
            Normalized API response.
        """
        return await self._request("GET",
                                   url,
                                   timeout=timeout,
                                   headers=headers,
                                   params=params)

    async def delete(self,
                     url: str,
                     json_data: dict | None = None,
                     headers: Headers | None = None,
                     params: QueryParams | None = None,
                     timeout: int = 2) -> ApiResponse:
        """Send an HTTP DELETE request.

        Args:
            url: Target API endpoint URL.
            json_data: Optional JSON payload to include in the request body.
            headers: Optional HTTP headers to include with the request.
            params: Optional query parameters to include with the request.
            timeout: Total request timeout in seconds.

        Returns:
            Normalized API response.
        """
        return await self._request("DELETE",
                                   url,
                                   json_data=json_data,
                                   headers=headers,
                                   params=params,
                                   timeout=timeout)

    async def patch(self,
                    url: str,
                    json_data: dict | None = None,
                    headers: Headers | None = None,
                    params: QueryParams | None = None,
                    timeout: int = 2) -> ApiResponse:
        """Send an HTTP PATCH request.

        Args:
            url: Target API endpoint URL.
            json_data: Optional JSON payload to include in the request body.
            headers: Optional HTTP headers to include with the request.
            params: Optional query parameters to include with the request.
            timeout: Total request timeout in seconds.

        Returns:
            Normalized API response.
        """
        return await self._request("PATCH",
                                   url,
                                   json_data=json_data,
                                   headers=headers,
                                   params=params,
                                   timeout=timeout)

    async def put(
            self,
            url: str,
            json_data: dict | None = None,
            headers: Headers | None = None,
            params: QueryParams | None = None,
            timeout: int = 2) -> ApiResponse:
        """Send an HTTP PUT request.

        Args:
            url: Target API endpoint URL.
            json_data: Optional JSON payload to include in the request body.
            headers: Optional HTTP headers to include with the request.
            params: Optional query parameters to include with the request.
            timeout: Total request timeout in seconds.

        Returns:
            Normalized API response.
        """
        return await self._request("PUT",
                                   url,
                                   json_data=json_data,
                                   headers=headers,
                                   timeout=timeout,
                                   params=params)

    async def _request(
            self,
            method: str,
            url: str,
            json_data: dict | None = None,
            headers: Headers | None = None,
            params: QueryParams | None = None,
            timeout: int = 2) -> ApiResponse:
        """Execute an HTTP request and normalize the response.

        Args:
            method: HTTP method to execute.
            url: Target endpoint URL.
            json_data: Optional JSON payload to include in the request body.
            headers: Optional HTTP headers to include with the request.
            params: Optional query parameters to include with the request.
            timeout: Total request timeout in seconds.

        Returns:
            Normalized API response.
        """
        try:
            request_kwargs: dict[str, Any] = {
                "timeout": aiohttp.ClientTimeout(total=timeout)
            }

            if json_data is not None:
                request_kwargs["json"] = json_data

            if headers is not None:
                request_kwargs["headers"] = headers

            if params is not None:
                request_kwargs["params"] = params

            async with self._http_session.request(
                    method,
                    url,
                    **request_kwargs) as response:

                return await self._parse_response(response)

        except (aiohttp.ClientConnectionError,
                aiohttp.ClientError) as ex:

            return ApiResponse(
                status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                exception_msg=str(ex)
            )

        except asyncio.TimeoutError as ex:

            return ApiResponse(
                status_code=http.HTTPStatus.GATEWAY_TIMEOUT,
                exception_msg=str(ex)
            )

    async def _parse_response(
            self,
            response: aiohttp.ClientResponse) -> ApiResponse:
        """Parse an aiohttp response into an ApiResponse object.

        Args:
            response: aiohttp response object to parse.

        Returns:
            Normalized API response.
        """

        try:
            raw_body = await response.text()

            if raw_body == "":
                body = None

            elif HttpContentType.is_json(response.content_type):
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
