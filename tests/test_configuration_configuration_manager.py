import configparser
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from veil.common.configuration_system.configuration_manager import (
    ConfigurationError,
    ConfigurationManager
)

from veil.common.configuration_system.configuration_setup import (
    ConfigItemDataType,
    ConfigurationSetup,
    ConfigurationSetupItem
)


class TestConfigurationManager(unittest.TestCase):
    """Tests for ConfigurationManager."""

    def setUp(self):
        """Create reusable configuration manager."""

        self.manager = ConfigurationManager()

    def test_configure(self):
        """Test configure stores values correctly."""

        setup = ConfigurationSetup({})

        self.manager.configure(
            layout=setup,
            config_file="test.ini",
            file_required=True
        )

        self.assertEqual(
            self.manager._config_file,
            "test.ini")

        self.assertTrue(
            self.manager._config_file_required)

        self.assertEqual(
            self.manager._layout,
            setup)

    def test_read_string_default(self):
        """Test string default value loading."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="name",
                    item_type=ConfigItemDataType.STRING,
                    default_value="veil"
                )
            ]
        })

        self.manager.configure(setup)

        self.manager.process_config()

        self.assertEqual(
            self.manager.get_entry("app", "name"),
            "veil")

    def test_environment_variable_override(self):
        """Test environment variable overrides defaults."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="name",
                    item_type=ConfigItemDataType.STRING,
                    default_value="default"
                )
            ]
        })

        with patch.dict(
                os.environ,
                {"APP_NAME": "environment"}):

            self.manager.configure(setup)

            self.manager.process_config()

            self.assertEqual(
                self.manager.get_entry("app", "name"),
                "environment")

    def test_required_value_missing(self):
        """Test required value raises error."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="name",
                    item_type=ConfigItemDataType.STRING,
                    is_required=True
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_integer_conversion(self):
        """Test integer conversion."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="port",
                    item_type=ConfigItemDataType.INTEGER,
                    default_value="8080"
                )
            ]
        })

        self.manager.configure(setup)

        self.manager.process_config()

        self.assertEqual(
            self.manager.get_entry("app", "port"),
            8080)

    def test_invalid_integer_raises(self):
        """Test invalid integer raises error."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="port",
                    item_type=ConfigItemDataType.INTEGER,
                    default_value="invalid"
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_boolean_true_values(self):
        """Test boolean true parsing."""

        for value in ["1", "true", "yes", "on"]:

            manager = ConfigurationManager()

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="enabled",
                        item_type=ConfigItemDataType.BOOLEAN,
                        default_value=value
                    )
                ]
            })

            manager.configure(setup)

            manager.process_config()

            self.assertTrue(
                manager.get_entry("app", "enabled"))

    def test_boolean_false_values(self):
        """Test boolean false parsing."""

        for value in ["0", "false", "no", "off"]:

            manager = ConfigurationManager()

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="enabled",
                        item_type=ConfigItemDataType.BOOLEAN,
                        default_value=value
                    )
                ]
            })

            manager.configure(setup)

            manager.process_config()

            self.assertFalse(
                manager.get_entry("app", "enabled"))

    def test_invalid_boolean_raises(self):
        """Test invalid boolean raises error."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="enabled",
                    item_type=ConfigItemDataType.BOOLEAN,
                    default_value="banana"
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_valid_string_values(self):
        """Test valid_values restriction."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="mode",
                    item_type=ConfigItemDataType.STRING,
                    valid_values=["dev", "prod"],
                    default_value="dev"
                )
            ]
        })

        self.manager.configure(setup)

        self.manager.process_config()

        self.assertEqual(
            self.manager.get_entry("app", "mode"),
            "dev")

    def test_invalid_string_value_raises(self):
        """Test invalid valid_values entry raises."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="mode",
                    item_type=ConfigItemDataType.STRING,
                    valid_values=["dev", "prod"],
                    default_value="invalid"
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_path_value(self):
        """Test path values return pathlib.Path."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="path",
                    item_type=ConfigItemDataType.PATH,
                    default_value="."
                )
            ]
        })

        self.manager.configure(setup)

        self.manager.process_config()

        value = self.manager.get_entry("app", "path")

        self.assertIsInstance(value, Path)

    def test_file_value(self):
        """Test file validation."""

        with tempfile.NamedTemporaryFile() as temp_file:

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="file",
                        item_type=ConfigItemDataType.FILE,
                        default_value=temp_file.name
                    )
                ]
            })

            self.manager.configure(setup)

            self.manager.process_config()

            value = self.manager.get_entry("app", "file")

            self.assertTrue(value.is_file())

    def test_missing_file_raises(self):
        """Test missing file raises."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="file",
                    item_type=ConfigItemDataType.FILE,
                    default_value="missing.txt"
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_directory_value(self):
        """Test directory validation."""

        with tempfile.TemporaryDirectory() as temp_dir:

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="directory",
                        item_type=ConfigItemDataType.DIRECTORY,
                        default_value=temp_dir
                    )
                ]
            })

            self.manager.configure(setup)

            self.manager.process_config()

            value = self.manager.get_entry(
                "app",
                "directory")

            self.assertTrue(value.is_dir())

    def test_create_missing_directory(self):
        """Test automatic directory creation."""

        with tempfile.TemporaryDirectory() as temp_dir:

            new_dir = Path(temp_dir) / "created"

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="directory",
                        item_type=ConfigItemDataType.DIRECTORY,
                        default_value=str(new_dir),
                        create_if_missing=True
                    )
                ]
            })

            self.manager.configure(setup)

            self.manager.process_config()

            self.assertTrue(new_dir.exists())
            self.assertTrue(new_dir.is_dir())

    def test_get_invalid_section_raises(self):
        """Test invalid section lookup raises."""

        with self.assertRaises(ConfigurationError):
            self.manager.get_entry("missing", "item")

    def test_get_invalid_item_raises(self):
        """Test invalid item lookup raises."""

        self.manager._config_items = {
            "app": {}
        }

        with self.assertRaises(ConfigurationError):
            self.manager.get_entry("app", "missing")

    def test_config_file_loading(self):
        """Test loading values from config file."""

        with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False) as temp_file:

            temp_file.write(
                "[app]\n"
                "name=veil\n"
            )

            temp_file.flush()

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="name",
                        item_type=ConfigItemDataType.STRING
                    )
                ]
            })

            self.manager.configure(
                setup,
                config_file=temp_file.name
            )

            self.manager.process_config()

            self.assertEqual(
                self.manager.get_entry("app", "name"),
                "veil")

        os.unlink(temp_file.name)

    def test_required_config_file_missing_raises(self):
        """Test missing required config file raises."""

        setup = ConfigurationSetup({})

        self.manager.configure(
            setup,
            config_file="missing.ini",
            file_required=True
        )

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_invalid_config_file_raises(self):
        """Test invalid config file syntax raises."""

        with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False) as temp_file:

            temp_file.write("[invalid")

            temp_file.flush()

            setup = ConfigurationSetup({})

            self.manager.configure(
                setup,
                config_file=temp_file.name
            )

            with self.assertRaises(ConfigurationError):
                self.manager.process_config()

        os.unlink(temp_file.name)

    def test_unsupported_configuration_type_raises(self):
        """Test unsupported configuration type raises."""

        class FakeType:
            pass

        item = ConfigurationSetupItem(
            item_name="bad",
            item_type=FakeType()
        )

        setup = ConfigurationSetup({
            "app": [item]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_integer_none_returns_none(self):
        """Test integer config returns None."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="port",
                    item_type=ConfigItemDataType.INTEGER
                )
            ]
        })

        self.manager.configure(setup)

        self.manager.process_config()

        self.assertIsNone(
            self.manager.get_entry("app", "port"))

    def test_boolean_native_bool(self):
        """Test native bool passes through."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="enabled",
                    item_type=ConfigItemDataType.BOOLEAN,
                    default_value=True
                )
            ]
        })

        self.manager.configure(setup)

        self.manager.process_config()

        self.assertTrue(
            self.manager.get_entry("app", "enabled"))

    def test_path_non_string_raises(self):
        """Test non-string path raises."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="path",
                    item_type=ConfigItemDataType.PATH,
                    default_value=123
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_empty_path_raises(self):
        """Test empty path raises."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="path",
                    item_type=ConfigItemDataType.PATH,
                    default_value=""
                )
            ]
        })

        self.manager.configure(setup)

        with self.assertRaises(ConfigurationError):
            self.manager.process_config()

    def test_directory_as_file_raises(self):
        """Test directory passed to FILE raises."""

        with tempfile.TemporaryDirectory() as temp_dir:

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="file",
                        item_type=ConfigItemDataType.FILE,
                        default_value=temp_dir
                    )
                ]
            })

            self.manager.configure(setup)

            with self.assertRaises(ConfigurationError):
                self.manager.process_config()

    def test_directory_creation_oserror_raises(self):
        """Test directory creation failure raises."""

        setup = ConfigurationSetup({
            "app": [
                ConfigurationSetupItem(
                    item_name="directory",
                    item_type=ConfigItemDataType.DIRECTORY,
                    default_value="new_dir",
                    create_if_missing=True
                )
            ]
        })

        self.manager.configure(setup)

        with patch(
                "pathlib.Path.mkdir",
                side_effect=OSError("failure")):

            with self.assertRaises(ConfigurationError):
                self.manager.process_config()

    def test_file_as_directory_raises(self):
        """Test file passed as DIRECTORY raises."""

        with tempfile.NamedTemporaryFile() as temp_file:

            setup = ConfigurationSetup({
                "app": [
                    ConfigurationSetupItem(
                        item_name="directory",
                        item_type=ConfigItemDataType.DIRECTORY,
                        default_value=temp_file.name
                    )
                ]
            })

            self.manager.configure(setup)

            with self.assertRaises(ConfigurationError):
                self.manager.process_config()

    def test_read_str_non_string_raises(self):
        """Test _read_str rejects non-string values."""

        fmt = ConfigurationSetupItem(
            item_name="name",
            item_type=ConfigItemDataType.STRING,
            default_value=123
        )

        with self.assertRaises(ConfigurationError):
            self.manager._read_str("app", fmt)

    def test_read_bool_none_returns_none(self):
        """Test _read_bool returns None."""

        fmt = ConfigurationSetupItem(
            item_name="enabled",
            item_type=ConfigItemDataType.BOOLEAN
        )

        result = self.manager._read_bool("app", fmt)

        self.assertIsNone(result)

    def test_read_str_returns_none(self):
        """Test _read_str returns None."""

        fmt = ConfigurationSetupItem(
            item_name="name",
            item_type=ConfigItemDataType.STRING
        )

        result = self.manager._read_str("app", fmt)

        self.assertIsNone(result)


    def test_read_bool_native_bool_false(self):
        """Test native False bool branch."""

        fmt = ConfigurationSetupItem(
            item_name="enabled",
            item_type=ConfigItemDataType.BOOLEAN,
            default_value=False
        )

        result = self.manager._read_bool("app", fmt)

        self.assertFalse(result)


    def test_read_path_environment_expansion(self):
        """Test environment variable expansion in paths."""

        with patch.dict(os.environ, {"TEST_ROOT": "example"}):

            path = self.manager._normalise_path(
                "$TEST_ROOT/test")

            self.assertIn(
                "example",
                str(path))


    def test_read_file_returns_none(self):
        """Test _read_file returns None branch."""

        fmt = ConfigurationSetupItem(
            item_name="file",
            item_type=ConfigItemDataType.FILE
        )

        result = self.manager._read_file("app", fmt)

        self.assertIsNone(result)


    def test_read_directory_returns_none(self):
        """Test _read_directory returns None branch."""

        fmt = ConfigurationSetupItem(
            item_name="directory",
            item_type=ConfigItemDataType.DIRECTORY
        )

        result = self.manager._read_directory("app", fmt)

        self.assertIsNone(result)


    def test_read_raw_value_from_default(self):
        """Test _read_raw_value default branch."""

        fmt = ConfigurationSetupItem(
            item_name="value",
            item_type=ConfigItemDataType.STRING,
            default_value="default"
        )

        result = self.manager._read_raw_value(
            "app",
            "value",
            fmt
        )

        self.assertEqual(result, "default")

    def test_read_directory_missing_without_create_raises(self):
        """Test missing directory without auto-create raises."""

        missing_path = "definitely_missing_directory_12345"

        fmt = ConfigurationSetupItem(
            item_name="directory",
            item_type=ConfigItemDataType.DIRECTORY,
            default_value=missing_path,
            create_if_missing=False
        )

        with self.assertRaises(ConfigurationError):
            self.manager._read_directory("app", fmt)

    def test_read_raw_value_missing_config_option(self):
        """Test missing config option branch."""

        fmt = ConfigurationSetupItem(
            item_name="missing",
            item_type=ConfigItemDataType.STRING
        )

        self.manager._has_config_file = True

        with patch.object(
                self.manager._parser,
                "get",
                side_effect=configparser.NoOptionError(
                    "missing",
                    "app")):

            result = self.manager._read_raw_value(
                "app",
                "missing",
                fmt
            )

            self.assertIsNone(result)
