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
from functools import wraps
import http
import json
import quart
from .api_response import ApiResponse


def validate_json(schema: dict):
    """
    Decorator to validate the JSON request body against a given schema.

    This decorator:
    - Extracts and validates the JSON request body using the provided schema.
    - If validation fails, returns an HTTP bad request response with an error
      message.
    - If validation succeeds, passes the validated data (`request_msg`) to the
      wrapped function.

    Args:
        schema (dict): The JSON schema to validate the request body against.

    Returns:
        A Quart Response object in case of validation failure,
        otherwise, the decorated function is called with the validated data.

    Example:
        @validate_json(handshake_api.SCHEMA_BASIC_AUTHENTICATE_REQUEST)
        async def authenticate(self, request_msg: ApiResponse) -> Response:
            return Response(json.dumps({"status": 1, "message": "Success"}),
                            status=HTTPStatus.OK,
                            content_type="application/json")
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                # Validate the JSON body using the provided schema
                request_msg: ApiResponse = self.validate_json_body(
                    await quart.request.get_data(),
                    schema
                )

                # If validation fails, return an error response
                if request_msg.status_code != http.HTTPStatus.OK:
                    response_json = {
                        'status': 0,
                        'error': request_msg.exception_msg
                    }
                    return quart.Response(
                        json.dumps(response_json),
                        status=http.HTTPStatus.BAD_REQUEST,
                        content_type="application/json"
                    )

                # If validation passes, call the original function
                return await func(self, request_msg, *args, **kwargs)

            except TypeError as e:
                error_msg = f"Type error: {str(e)}"

            # Catch specific errors and return an internal server error response
            response_json = {
                'status': 0,
                'error': error_msg
            }
            return quart.Response(
                json.dumps(response_json),
                status=http.HTTPStatus.BAD_REQUEST,
                content_type="application/json"
            )

        return wrapper
    return decorator
