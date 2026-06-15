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
import configparser
import os
from pathlib import Path
from typing import Any
from collections.abc import Callable
from .configuration_setup import (ConfigItemDataType,
                                  ConfigurationSetup,
                                  ConfigurationSetupItem)
from weaver_framework.constants import BOOL_TRUE_VALUES, BOOL_FALSE_VALUES


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""


class ConfigurationManager:
    """Manage application configuration from multiple sources.

    This class wraps ``configparser.ConfigParser`` and extends it with
    support for multiple configuration sources, including environment
    variables, configuration files, and default values.

    Configuration values are resolved in the following order:

    1. Environment variables
    2. Configuration file values
    3. Default values from the configuration layout
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self._parser = configparser.ConfigParser()

        self._config_file: str = ''
        self._has_config_file: bool = False
        self._config_file_required: bool = False
        self._layout: ConfigurationSetup | None = None
        self._config_items: dict[str, dict[str, Any]] = {}

        self._type_readers: dict[
            ConfigItemDataType,
            Callable[
                [str, ConfigurationSetupItem],
                Any
            ]
        ] = {
            ConfigItemDataType.INTEGER:
                self._read_int,

            ConfigItemDataType.STRING:
                self._read_str,

            ConfigItemDataType.BOOLEAN:
                self._read_bool,

            ConfigItemDataType.PATH:
                self._read_path,

            ConfigItemDataType.FILE:
                self._read_file,

            ConfigItemDataType.DIRECTORY:
                self._read_directory
        }

    def configure(self,
                  layout: ConfigurationSetup,
                  config_file: str | None = None,
                  file_required: bool = False):
        """Configure the configuration manager.

        Args:
            layout: Configuration layout describing sections, items,
                types, and defaults.
            config_file: Path to the configuration file.
            file_required: Whether the configuration file must exist.

        """
        self._config_file: str = config_file
        self._config_file_required: bool = file_required
        self._layout: ConfigurationSetup = layout

    def process_config(self):
        """Load and process configuration values.

        Reads the configuration file if one is configured and then
        resolves all configuration items defined in the layout.

        Raises:
            ConfigurationError: If the configuration file cannot be
                parsed, required configuration is missing, or validation
                fails.

        """
        if self._config_file:
            try:
                files_read = self._parser.read(self._config_file)

            except configparser.ParsingError as ex:
                raise ConfigurationError(
                    f"Failed to read required config file, reason: {ex}") from ex

            if not files_read and self._config_file_required:
                raise ConfigurationError(
                    f"Failed to open required config file '{self._config_file}'")

            self._has_config_file = bool(files_read)

        self._read_configuration()

    def get_entry(self, section: str, item: str) -> Any:
        """Retrieve a processed configuration value.

        Args:
            section: Configuration section name.
            item: Configuration item name.

        Returns:
            The processed configuration value.

        Raises:
            ConfigurationError: If the section or item does not exist.

        """
        if section not in self._config_items:
            raise ConfigurationError(f"Invalid section '{section}'")

        if item not in self._config_items[section]:
            raise ConfigurationError(f"Invalid config item '{section}::{item}'")

        return self._config_items[section][item]

    def _read_configuration(self):
        """Read and process all configuration items.

        Iterates through all configured sections and items defined
        in the layout and converts values to their expected types.

        Raises:
            ConfigurationError: If a configuration item cannot be
                validated or converted.

        """
        sections = self._layout.get_sections()

        for section_name in sections:
            section_items = self._layout.get_section(section_name)

            self._config_items.setdefault(section_name, {})

            for section_item in section_items:

                reader = self._type_readers.get(
                    section_item.item_type)

                if reader is None:
                    raise ConfigurationError(
                        f"Unsupported configuration item type "
                        f"'{section_item.item_type}'")

                item_value = reader(section_name, section_item)

                self._config_items[section_name][
                    section_item.item_name] = item_value

    def _read_str(self,
                  section: str,
                  fmt: ConfigurationSetupItem) -> str | None:
        """Read and validate a string configuration value.

        Args:
            section: Configuration section name.
            fmt: Configuration item definition.

        Returns:
            The validated string value.

        Raises:
            ConfigurationError: If the value is not within the allowed
                valid values.

        """
        value = self._read_raw_value(section, fmt.item_name, fmt)

        if value is not None and not isinstance(value, str):
            raise ConfigurationError(
                f"Configuration option '{fmt.item_name}' "
                f"must be a string.")

        if value is not None and \
                fmt.valid_values and \
                value not in fmt.valid_values:
            raise ConfigurationError(
                f"Value of '{value}' for {fmt.item_name} is invalid")

        return value

    def _read_int(self, section: str,
                  fmt: ConfigurationSetupItem) -> int | None:
        """Read and convert an integer configuration value.

        Args:
            section: Configuration section name.
            fmt: Configuration item definition.

        Returns:
            The integer value, or ``None`` if no value is defined.

        Raises:
            ConfigurationError: If the value cannot be converted
                to an integer.

        """
        value = self._read_raw_value(section, fmt.item_name, fmt)

        if value is None:
            return None

        try:
            return int(value)

        except ValueError as ex:
            raise ConfigurationError(
                f"Configuration option '{fmt.item_name}' "
                f"with a value of '{value}' is not an int.") from ex

    def _read_bool(
            self,
            section: str,
            fmt: ConfigurationSetupItem) -> bool | None:
        """Read and convert a boolean configuration value.

        Args:
            section: Configuration section name.
            fmt: Configuration item definition.

        Returns:
            The boolean value, or ``None`` if no value is defined.

        Raises:
            ConfigurationError: If the value cannot be interpreted
                as a valid boolean.

        """
        value = self._read_raw_value(
            section,
            fmt.item_name,
            fmt)

        if value is None:
            return None

        if isinstance(value, bool):
            return value

        normalized_value = str(value).strip().lower()

        if normalized_value in BOOL_TRUE_VALUES:
            return True

        if normalized_value in BOOL_FALSE_VALUES:
            return False

        raise ConfigurationError(
            f"Configuration option '{fmt.item_name}' "
            f"with a value of '{value}' is not a valid boolean.")

    def _normalise_path(self, value: str) -> Path:
        """
        Convert a raw string path into a normalised pathlib.Path.

        Expands:
        - ~ home directories
        - environment variables

        Does NOT:
        - require existence
        - resolve symlinks
        """

        expanded_value = os.path.expandvars(value)

        return Path(expanded_value).expanduser()

    def _read_path(
            self,
            section: str,
            fmt: ConfigurationSetupItem) -> Path | None:
        """
        Read a generic path configuration value.

        The path is not required to exist.
        """
        value = self._read_raw_value(
            section,
            fmt.item_name,
            fmt)

        if value is None:
            return None

        if not isinstance(value, str):
            raise ConfigurationError(
                f"Configuration option '{fmt.item_name}' "
                f"must be a string path.")

        if not value.strip():
            raise ConfigurationError(
                f"Configuration option '{fmt.item_name}' "
                f"cannot be empty.")

        return self._normalise_path(value)

    def _read_file(
            self,
            section: str,
            fmt: ConfigurationSetupItem) -> Path | None:
        """
        Read and validate a file configuration value.

        The file must exist.
        """

        path = self._read_path(section, fmt)

        if path is None:
            return None

        if not path.exists():
            raise ConfigurationError(
                f"Configured file does not exist: {path}")

        if not path.is_file():
            raise ConfigurationError(
                f"Configured path is not a file: {path}")

        return path

    def _read_directory(
            self,
            section: str,
            fmt: ConfigurationSetupItem) -> Path | None:
        """
        Read and validate a directory configuration value.
        """

        path = self._read_path(section, fmt)

        if path is None:
            return None

        if not path.exists():

            if fmt.create_if_missing:

                try:
                    path.mkdir(parents=True, exist_ok=True)

                except OSError as ex:
                    raise ConfigurationError(
                        f"Failed to create directory '{path}', "
                        f"reason: {ex}") from ex

            else:
                raise ConfigurationError(
                    f"Configured directory does not exist: {path}")

        if not path.is_dir():
            raise ConfigurationError(
                f"Configured path is not a directory: {path}")

        return path

    def _read_raw_value(self,
                        section: str,
                        option: str,
                        fmt: ConfigurationSetupItem) -> Any:
        """Read a raw configuration value from available sources.

        Values are resolved in the following order:

        1. Environment variables
        2. Configuration file
        3. Default values

        Args:
            section: Configuration section name.
            option: Configuration option name.
            fmt: Configuration item definition.

        Returns:
            The resolved configuration value.

        Raises:
            ConfigurationError: If a required configuration value
                is missing.

        """
        env_variable = f"{section}_{option}".upper()

        value = os.getenv(env_variable)

        if value is None and self._has_config_file:
            try:
                value = self._parser.get(section, option)

            except (
                    configparser.NoOptionError,
                    configparser.NoSectionError):
                value = None

        if value is None:
            value = fmt.default_value

        if value is None and fmt.is_required:
            raise ConfigurationError(
                f"Missing required config option "
                f"'{section}::{fmt.item_name}'")

        return value
