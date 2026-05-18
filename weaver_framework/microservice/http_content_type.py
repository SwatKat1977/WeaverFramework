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


class HttpContentType:
    """Common HTTP content type constants and helpers.

    Attributes:
        JSON: Content type for JSON payloads.
        HTML: Content type for HTML documents.
        TEXT: Content type for plain text responses.
        XML: Content type for XML documents.
        TEXT_TYPES: Set of textual content types.
    """
    # pylint: disable=too-few-public-methods

    JSON = "application/json"
    HTML = "text/html"
    TEXT = "text/plain"
    XML = "application/xml"

    TEXT_TYPES = {
        TEXT,
        HTML,
    }

    @staticmethod
    def is_json(content_type: str | None) -> bool:
        """Determine whether a content type represents JSON data.

        Args:
            content_type: HTTP content type value to evaluate.

        Returns:
            True if the content type represents JSON data.
        """

        if content_type is None:
            return False

        return (
            content_type == HttpContentType.JSON or
            content_type.endswith("+json")
        )

    @staticmethod
    def is_html(content_type: str | None) -> bool:
        """Determine whether a content type represents HTML data."""

        return content_type == HttpContentType.HTML

    @staticmethod
    def is_text(content_type: str | None) -> bool:
        """Determine whether a content type represents plain text."""

        return content_type in HttpContentType.TEXT_TYPES

    @staticmethod
    def is_xml(content_type: str | None) -> bool:
        """Determine whether a content type represents XML data."""

        if content_type is None:
            return False

        return (
            content_type == HttpContentType.XML or
            content_type.endswith("+xml")
        )

    @staticmethod
    def is_binary(content_type: str | None) -> bool:
        """Determine whether a content type represents binary data."""

        if content_type is None:
            return False

        return not (
            HttpContentType.is_json(content_type) or
            HttpContentType.is_text(content_type) or
            HttpContentType.is_xml(content_type)
        )
