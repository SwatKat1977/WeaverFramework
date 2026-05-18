import unittest
from weaver_framework.microservice.http_content_type import HttpContentType


class TestMicroserviceHttpContentType(unittest.TestCase):

    def test_json_constant(self):
        self.assertEqual(
            "application/json",
            HttpContentType.JSON
        )

    def test_html_constant(self):
        self.assertEqual(
            "text/html",
            HttpContentType.HTML
        )

    def test_text_constant(self):
        self.assertEqual(
            "text/plain",
            HttpContentType.TEXT
        )

    def test_xml_constant(self):
        self.assertEqual(
            "application/xml",
            HttpContentType.XML
        )

    def test_text_types_contains_text(self):
        self.assertIn(
            HttpContentType.TEXT,
            HttpContentType.TEXT_TYPES
        )

    def test_text_types_contains_html(self):
        self.assertIn(
            HttpContentType.HTML,
            HttpContentType.TEXT_TYPES
        )

    def test_is_json_returns_true_for_standard_json(self):
        self.assertTrue(
            HttpContentType.is_json(
                "application/json"
            )
        )

    def test_is_json_returns_true_for_vendor_json(self):
        self.assertTrue(
            HttpContentType.is_json(
                "application/vnd.api+json"
            )
        )

    def test_is_json_returns_false_for_html(self):
        self.assertFalse(
            HttpContentType.is_json(
                "text/html"
            )
        )

    def test_is_json_returns_false_for_none(self):
        self.assertFalse(
            HttpContentType.is_json(None)
        )

    def test_is_html_returns_true_for_html(self):
        self.assertTrue(
            HttpContentType.is_html(
                "text/html"
            )
        )

    def test_is_html_returns_false_for_json(self):
        self.assertFalse(
            HttpContentType.is_html(
                "application/json"
            )
        )

    def test_is_text_returns_true_for_text(self):
        self.assertTrue(
            HttpContentType.is_text(
                "text/plain"
            )
        )

    def test_is_text_returns_true_for_html(self):
        self.assertTrue(
            HttpContentType.is_text(
                "text/html"
            )
        )

    def test_is_text_returns_false_for_json(self):
        self.assertFalse(
            HttpContentType.is_text(
                "application/json"
            )
        )

    def test_is_xml_returns_true_for_standard_xml(self):
        self.assertTrue(
            HttpContentType.is_xml(
                "application/xml"
            )
        )

    def test_is_xml_returns_true_for_vendor_xml(self):
        self.assertTrue(
            HttpContentType.is_xml(
                "application/problem+xml"
            )
        )

    def test_is_xml_returns_false_for_json(self):
        self.assertFalse(
            HttpContentType.is_xml(
                "application/json"
            )
        )

    def test_is_xml_returns_false_for_none(self):
        self.assertFalse(
            HttpContentType.is_xml(None)
        )

    def test_is_binary_returns_true_for_binary_content(self):
        self.assertTrue(
            HttpContentType.is_binary(
                "application/octet-stream"
            )
        )

    def test_is_binary_returns_true_for_image_content(self):
        self.assertTrue(
            HttpContentType.is_binary(
                "image/png"
            )
        )

    def test_is_binary_returns_false_for_json(self):
        self.assertFalse(
            HttpContentType.is_binary(
                "application/json"
            )
        )

    def test_is_binary_returns_false_for_text(self):
        self.assertFalse(
            HttpContentType.is_binary(
                "text/plain"
            )
        )

    def test_is_binary_returns_false_for_xml(self):
        self.assertFalse(
            HttpContentType.is_binary(
                "application/xml"
            )
        )

    def test_is_binary_returns_false_for_none(self):
        self.assertFalse(
            HttpContentType.is_binary(None)
        )
