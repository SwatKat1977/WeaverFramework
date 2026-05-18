import unittest
from weaver_framework.microservice.api_response import ApiResponse


class TestMicroserviceApiResponse(unittest.TestCase):

    def test_default_values(self):
        response = ApiResponse()

        self.assertEqual(0, response.status_code)
        self.assertIsNone(response.headers)
        self.assertIsNone(response.body)
        self.assertIsNone(response.content_type)
        self.assertIsNone(response.exception_msg)

    def test_custom_values(self):
        response = ApiResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={"username": "paul"},
            content_type="application/json",
            exception_msg="error"
        )

        self.assertEqual(200, response.status_code)

        self.assertEqual(
            {"Content-Type": "application/json"},
            response.headers
        )

        self.assertEqual(
            {"username": "paul"},
            response.body
        )

        self.assertEqual(
            "application/json",
            response.content_type
        )

        self.assertEqual(
            "error",
            response.exception_msg
        )

    def test_success_returns_true_for_200(self):
        response = ApiResponse(status_code=200)
        self.assertTrue(response.success)

    def test_success_returns_true_for_299(self):
        response = ApiResponse(status_code=299)
        self.assertTrue(response.success)

    def test_success_returns_false_for_199(self):
        response = ApiResponse(status_code=199)
        self.assertFalse(response.success)

    def test_success_returns_false_for_300(self):
        response = ApiResponse(status_code=300)
        self.assertFalse(response.success)

    def test_success_returns_false_for_500(self):
        response = ApiResponse(status_code=500)
        self.assertFalse(response.success)
