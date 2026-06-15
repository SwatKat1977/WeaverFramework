import http
import json
import unittest
import quart
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.microservice_decorators import validate_json
from weaver_framework.microservice.http_content_type import HttpContentType


class MockRoute:

    def __init__(self):
        self.validate_json_body_response = None

    def validate_json_body(self, *_args, **_kwargs):
        return self.validate_json_body_response


class TestValidateJsonDecorator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self._app = quart.Quart(__name__)
        self._route = MockRoute()

    async def test_validate_json_success_calls_wrapped_function(self):

        self._route.validate_json_body_response = ApiResponse(
            body={"username": "paul"},
            status_code=http.HTTPStatus.OK,
            content_type=HttpContentType.JSON
        )

        @validate_json({"type": "object"})
        async def test_handler(self, request_msg):
            return quart.Response(
                json.dumps({
                    "status": 1,
                    "username": request_msg.body["username"]
                }),
                status=http.HTTPStatus.OK,
                content_type="application/json"
            )

        async with self._app.test_request_context(
                "/",
                data='{"username":"paul"}'):

            response = await test_handler(self._route)

            self.assertEqual(
                http.HTTPStatus.OK,
                response.status_code
            )

            response_data = json.loads(
                (await response.get_data()).decode()
            )

            self.assertEqual(
                1,
                response_data["status"]
            )

            self.assertEqual(
                "paul",
                response_data["username"]
            )

    async def test_validate_json_validation_failure_returns_bad_request(
            self):

        self._route.validate_json_body_response = ApiResponse(
            exception_msg="Validation failed",
            status_code=http.HTTPStatus.BAD_REQUEST,
            content_type=HttpContentType.TEXT
        )

        @validate_json({"type": "object"})
        async def test_handler(self, request_msg):
            return quart.Response("should never execute")

        async with self._app.test_request_context(
                "/", data='{}'):

            response = await test_handler(self._route)

            self.assertEqual(
                http.HTTPStatus.BAD_REQUEST,
                response.status_code
            )

            response_data = json.loads(
                (await response.get_data()).decode()
            )

            self.assertEqual(
                0,
                response_data["status"]
            )

            self.assertEqual(
                "Validation failed",
                response_data["error"]
            )

    async def test_validate_json_type_error_returns_bad_request(self):

        self._route.validate_json_body_response = ApiResponse(
            body={"username": "paul"},
            status_code=http.HTTPStatus.OK,
            content_type=HttpContentType.JSON
        )

        @validate_json({"type": "object"})
        async def test_handler(self, request_msg):
            raise TypeError("Invalid type")

        async with self._app.test_request_context(
                "/",
                data='{"username":"paul"}'):

            response = await test_handler(self._route)

            self.assertEqual(
                http.HTTPStatus.BAD_REQUEST,
                response.status_code
            )

            response_data = json.loads(
                (await response.get_data()).decode()
            )

            self.assertEqual(
                0,
                response_data["status"]
            )

            self.assertIn(
                "Type error",
                response_data["error"]
            )

    async def test_validate_json_preserves_wrapped_function_name(self):

        @validate_json({"type": "object"})
        async def test_handler(self, request_msg):
            return quart.Response("ok")

        self.assertEqual(
            "test_handler",
            test_handler.__name__
        )