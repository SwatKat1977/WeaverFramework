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
from dataclasses import dataclass
from weaver_framework.configuration_system.configuration_manager import \
    ConfigurationManager
from weaver_framework.configuration_system.configuration_setup import (
    ConfigItemDataType,
    ConfigurationSetupItem)

DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8000
DEFAULT_SHUTDOWN_TIMEOUT: int = 10


@dataclass(frozen=True, slots=True)
class ServerConfiguration:
    """Settings for the HTTP server run by a QuartMicroservice.

    Attributes:
        host: Address to listen on. Use ``0.0.0.0`` inside containers.
        port: TCP port to listen on (0 lets the operating system choose).
        shutdown_timeout: Seconds that in-flight requests are given to
            finish when the service stops.
        access_log: Whether to log every request.
    """
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    shutdown_timeout: int = DEFAULT_SHUTDOWN_TIMEOUT
    access_log: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.port <= 65535:
            raise ValueError(f"Invalid port {self.port}, must be 0-65535")

        if self.shutdown_timeout < 0:
            raise ValueError("shutdown_timeout cannot be negative")

    @classmethod
    def from_configuration(cls,
                           manager: ConfigurationManager,
                           section: str = "server") -> "ServerConfiguration":
        """Build server settings from a processed ConfigurationManager.

        The configuration layout must include :func:`server_configuration_items`
        under ``section``. Values can then be set with environment variables
        such as ``SERVER_HOST`` and ``SERVER_PORT``, or in the config file.

        Args:
            manager: A ConfigurationManager that has processed its config.
            section: Section holding the server settings.

        Returns:
            The server configuration.
        """
        return cls(host=manager.get_entry(section, "host"),
                   port=manager.get_entry(section, "port"),
                   shutdown_timeout=manager.get_entry(section,
                                                      "shutdown_timeout"),
                   access_log=manager.get_entry(section, "access_log"))


def server_configuration_items() -> list[ConfigurationSetupItem]:
    """Configuration layout items for :class:`ServerConfiguration`.

    Example::

        layout = ConfigurationSetup({"server": server_configuration_items()})

    Returns:
        A new list of configuration items (host, port, shutdown_timeout,
        access_log) with the same defaults as ServerConfiguration.
    """
    return [
        ConfigurationSetupItem(item_name="host",
                               item_type=ConfigItemDataType.STRING,
                               default_value=DEFAULT_HOST),
        ConfigurationSetupItem(item_name="port",
                               item_type=ConfigItemDataType.INTEGER,
                               default_value=DEFAULT_PORT),
        ConfigurationSetupItem(item_name="shutdown_timeout",
                               item_type=ConfigItemDataType.INTEGER,
                               default_value=DEFAULT_SHUTDOWN_TIMEOUT),
        ConfigurationSetupItem(item_name="access_log",
                               item_type=ConfigItemDataType.BOOLEAN,
                               default_value=False),
    ]
