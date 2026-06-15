import http
import unittest
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.http_content_type import HttpContentType


class TestMicroserviceBaseApiRoute(unittest.TestCase):

    def setUp(self) -> None:
        self._route = BaseApiRoute()

    def test_validate_json_body_with_none_returns_bad_request(self):
        response = self._route.validate_json_body(None)

        self.assertEqual(
            http.HTTPStatus.BAD_REQUEST,
            response.status_code
        )

        self.assertEqual(
            BaseApiRoute.ERR_MSG_MISSING_INVALID_JSON_BODY,
            response.exception_msg
        )

        self.assertEqual(
            HttpContentType.TEXT,
            response.content_type
        )

    def test_validate_json_body_with_empty_string_returns_bad_request(self):
        response = self._route.validate_json_body("")

        self.assertEqual(
            http.HTTPStatus.BAD_REQUEST,
            response.status_code
        )

        self.assertEqual(
            BaseApiRoute.ERR_MSG_MISSING_INVALID_JSON_BODY,
            response.exception_msg
        )

    def test_validate_json_body_with_invalid_json_returns_bad_request(self):
        response = self._route.validate_json_body("{invalid json}")

        self.assertEqual(
            http.HTTPStatus.BAD_REQUEST,
            response.status_code
        )

        self.assertEqual(
            BaseApiRoute.ERR_MSG_INVALID_BODY_TYPE,
            response.exception_msg
        )

    def test_validate_json_body_with_invalid_type_returns_bad_request(self):
        response = self._route.validate_json_body(123)

        self.assertEqual(
            http.HTTPStatus.BAD_REQUEST,
            response.status_code
        )

        self.assertEqual(
            BaseApiRoute.ERR_MSG_INVALID_BODY_TYPE,
            response.exception_msg
        )

    def test_validate_json_body_with_valid_json_returns_ok(self):
        response = self._route.validate_json_body(
            '{"username": "paul"}'
        )

        self.assertEqual(
            http.HTTPStatus.OK,
            response.status_code
        )

        self.assertEqual(
            {"username": "paul"},
            response.body
        )

        self.assertEqual(
            HttpContentType.JSON,
            response.content_type
        )

    def test_validate_json_body_with_valid_bytes_returns_ok(self):
        response = self._route.validate_json_body(
            b'{"username": "paul"}'
        )

        self.assertEqual(
            http.HTTPStatus.OK,
            response.status_code
        )

        self.assertEqual(
            {"username": "paul"},
            response.body
        )

    def test_validate_json_body_with_valid_schema_returns_ok(self):
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string"}
            },
            "required": ["username"]
        }

        response = self._route.validate_json_body(
            '{"username": "paul"}',
            json_schema=schema
        )

        self.assertEqual(
            http.HTTPStatus.OK,
            response.status_code
        )

        self.assertEqual(
            {"username": "paul"},
            response.body
        )

    def test_validate_json_body_with_schema_mismatch_returns_bad_request(
            self):
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string"}
            },
            "required": ["username"]
        }

        response = self._route.validate_json_body(
            '{"age": 42}',
            json_schema=schema
        )

        self.assertEqual(
            http.HTTPStatus.BAD_REQUEST,
            response.status_code
        )

        self.assertEqual(
            BaseApiRoute.ERR_MSG_BODY_SCHEMA_MISMATCH,
            response.exception_msg
        )

        self.assertEqual(
            HttpContentType.TEXT,
            response.content_type
        )

    def test_validate_json_body_with_malformed_schema_returns_bad_request(
            self):
        schema = {"type": "not-a-valid-type"}

        response = self._route.validate_json_body(
            '{"username": "paul"}',
            json_schema=schema
        )

        self.assertEqual(
            http.HTTPStatus.BAD_REQUEST,
            response.status_code
        )

        self.assertEqual(
            BaseApiRoute.ERR_MSG_BODY_SCHEMA_MISMATCH,
            response.exception_msg
        )

        self.assertEqual(
            HttpContentType.TEXT,
            response.content_type
        )
