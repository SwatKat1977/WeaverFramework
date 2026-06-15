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
import enum
from dataclasses import dataclass


class ConfigItemDataType(enum.Enum):
    """ Enumeration for configuration item data type """

    # Primitives
    BOOLEAN = enum.auto()
    INTEGER = enum.auto()
    STRING = enum.auto()

    # File System related
    PATH = enum.auto()
    FILE = enum.auto()
    DIRECTORY = enum.auto()


@dataclass(frozen=True, slots=True)
class ConfigurationSetupItem:
    """ Configuration layout class """

    item_name: str
    item_type: ConfigItemDataType
    valid_values: list[str] | None = None
    is_required: bool = False
    default_value: object | None = None
    create_if_missing: bool = False


class ConfigurationSetup:
    """ Class that defines the configuration Format """

    def __init__(
            self,
            setup_items: dict[str,list[ConfigurationSetupItem]]) -> None:
        self._items = setup_items

    def get_sections(self) -> list[str]:
        """
        Get a list of sections available.

        returns:
            List of strings that represent the sections available.
        """
        return list(self._items.keys())

    def get_section(self, name: str) -> list[ConfigurationSetupItem]:
        """
        Get a list of items within a given sections.

        returns:
            List of list of configuration items.
        """
        if name not in self._items:
            raise KeyError(f"Section {name} not available")

        return self._items[name]
