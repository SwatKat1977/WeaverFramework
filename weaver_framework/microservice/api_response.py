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
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApiResponse:
    """Container for API response data.

    Attributes:
        status_code: HTTP status code returned by the API response.
        headers: Mapping of HTTP response headers. Defaults to ``None`` if
            no headers are present.
        body: Parsed or raw response body returned by the API.
        content_type: MIME type of the response body, such as
            ``"application/json"``.
        exception_msg: Exception or error message associated with the request,
            if one occurred.
    """

    status_code: int = 0
    headers: dict[str, str] | None = None
    body: Any = None
    content_type: str | None = None
    exception_msg: str | None = None

    @property
    def success(self) -> bool:
        """Return whether the response represents a successful request.

        Returns:
            ``True`` if the status code is in the HTTP 2xx range,
            otherwise ``False``.
        """
        return 200 <= self.status_code < 300
