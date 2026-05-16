import unittest

from weaver_framework import build_version_string


class TestVersion(unittest.TestCase):
    """Tests for version handling."""

    def test_release_version(self) -> None:
        """Test standard release version formatting."""
        self.assertEqual(
            build_version_string(0, 1, 0),
            "0.1.0",
        )

    def test_alpha_version(self) -> None:
        """Test alpha prerelease formatting."""
        self.assertEqual(
            build_version_string(0, 1, 0, "a1"),
            "0.1.0a1",
        )

    def test_beta_version(self) -> None:
        """Test beta prerelease formatting."""
        self.assertEqual(
            build_version_string(0, 1, 0, "b1"),
            "0.1.0b1",
        )
