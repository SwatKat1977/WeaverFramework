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
import http
import json
import jsonschema
from .api_response import ApiResponse
from .http_content_type import HttpContentType


class BaseApiRoute:
    """Base API route class."""
    # pylint: disable=too-few-public-methods

    ERR_MSG_INVALID_BODY_TYPE: str = "Invalid body type, not JSON"
    ERR_MSG_MISSING_INVALID_JSON_BODY: str = "Missing/invalid json body"
    ERR_MSG_BODY_SCHEMA_MISMATCH: str = "Message body failed schema validation"

    def validate_json_body(self, data: bytes | str, json_schema: dict = None) \
            -> ApiResponse:
        """
        Validate response body is JSON.

        NOTE: This has not been optimised, it can and should be in the future!

        Args:
            data: Response body to validate.
            json_schema: Optional Json schema to validate the body against.

        Returns:
            ApiResponse : If successful then object is a valid object.
        """

        if not data:
            return ApiResponse(exception_msg=self.ERR_MSG_MISSING_INVALID_JSON_BODY,
                               status_code=http.HTTPStatus.BAD_REQUEST,
                               content_type=HttpContentType.TEXT)

        try:
            json_data = json.loads(data)

        except (TypeError, json.JSONDecodeError):
            return ApiResponse(exception_msg=self.ERR_MSG_INVALID_BODY_TYPE,
                               status_code=http.HTTPStatus.BAD_REQUEST,
                               content_type=HttpContentType.TEXT)

        # If there is a JSON schema then validate that the json body conforms
        # to the expected schema. If the body isn't valid then a 400 error
        # should be generated.
        if json_schema:
            try:
                jsonschema.validate(instance=json_data,
                                    schema=json_schema)

            except jsonschema.exceptions.ValidationError:
                return ApiResponse(exception_msg=self.ERR_MSG_BODY_SCHEMA_MISMATCH,
                                   status_code=http.HTTPStatus.BAD_REQUEST,
                                   content_type=HttpContentType.TEXT)

        return ApiResponse(body=json_data,
                           status_code=http.HTTPStatus.OK,
                           content_type=HttpContentType.JSON)
