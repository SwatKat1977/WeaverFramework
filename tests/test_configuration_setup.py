import unittest
from veil.common.configuration_system.configuration_setup import (
    ConfigItemDataType,
    ConfigurationSetup,
    ConfigurationSetupItem
)


class TestConfigItemDataType(unittest.TestCase):
    """Tests for ConfigItemDataType."""

    def test_enum_contains_expected_values(self):
        """Test enum contains expected configuration types."""

        self.assertIn(
            ConfigItemDataType.BOOLEAN,
            ConfigItemDataType)

        self.assertIn(
            ConfigItemDataType.INTEGER,
            ConfigItemDataType)

        self.assertIn(
            ConfigItemDataType.STRING,
            ConfigItemDataType)

        self.assertIn(
            ConfigItemDataType.PATH,
            ConfigItemDataType)

        self.assertIn(
            ConfigItemDataType.FILE,
            ConfigItemDataType)

        self.assertIn(
            ConfigItemDataType.DIRECTORY,
            ConfigItemDataType)


class TestConfigurationSetupItem(unittest.TestCase):
    """Tests for ConfigurationSetupItem."""

    def test_create_setup_item(self):
        """Test setup item fields are stored correctly."""

        item = ConfigurationSetupItem(
            item_name="host",
            item_type=ConfigItemDataType.STRING,
            valid_values=["localhost", "example.com"],
            is_required=True,
            default_value="localhost",
            create_if_missing=True
        )

        self.assertEqual(item.item_name, "host")

        self.assertEqual(
            item.item_type,
            ConfigItemDataType.STRING)

        self.assertEqual(
            item.valid_values,
            ["localhost", "example.com"])

        self.assertTrue(item.is_required)

        self.assertEqual(
            item.default_value,
            "localhost")

        self.assertTrue(item.create_if_missing)

    def test_defaults(self):
        """Test optional fields use expected defaults."""

        item = ConfigurationSetupItem(
            item_name="port",
            item_type=ConfigItemDataType.INTEGER
        )

        self.assertIsNone(item.valid_values)
        self.assertFalse(item.is_required)
        self.assertIsNone(item.default_value)
        self.assertFalse(item.create_if_missing)

    def test_dataclass_is_frozen(self):
        """Test setup item is immutable."""

        item = ConfigurationSetupItem(
            item_name="test",
            item_type=ConfigItemDataType.STRING
        )

        with self.assertRaises(AttributeError):
            item.item_name = "modified"


class TestConfigurationSetup(unittest.TestCase):
    """Tests for ConfigurationSetup."""

    def setUp(self):
        """Create reusable configuration setup."""

        self.host_item = ConfigurationSetupItem(
            item_name="host",
            item_type=ConfigItemDataType.STRING
        )

        self.port_item = ConfigurationSetupItem(
            item_name="port",
            item_type=ConfigItemDataType.INTEGER
        )

        self.setup = ConfigurationSetup({
            "network": [
                self.host_item,
                self.port_item
            ],
            "logging": []
        })

    def test_get_sections(self):
        """Test section names are returned."""

        sections = self.setup.get_sections()

        self.assertEqual(
            sorted(sections),
            ["logging", "network"])

    def test_get_section(self):
        """Test retrieving a valid section."""

        section = self.setup.get_section("network")

        self.assertEqual(
            section,
            [self.host_item, self.port_item])

    def test_get_empty_section(self):
        """Test retrieving an empty section."""

        section = self.setup.get_section("logging")

        self.assertEqual(section, [])

    def test_get_invalid_section_raises(self):
        """Test invalid section raises KeyError."""

        with self.assertRaises(KeyError):
            self.setup.get_section("invalid")
