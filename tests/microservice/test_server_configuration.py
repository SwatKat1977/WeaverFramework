import os
import unittest
from unittest.mock import patch
from weaver_framework.configuration_system.configuration_manager import \
    ConfigurationManager
from weaver_framework.configuration_system.configuration_setup import \
    ConfigurationSetup
from weaver_framework.microservice.server_configuration import (
    ServerConfiguration,
    server_configuration_items)


class TestServerConfiguration(unittest.TestCase):

    def test_defaults(self):
        config = ServerConfiguration()

        self.assertEqual("127.0.0.1", config.host)
        self.assertEqual(8000, config.port)
        self.assertEqual(10, config.shutdown_timeout)
        self.assertFalse(config.access_log)

    def test_port_zero_is_allowed(self):
        self.assertEqual(0, ServerConfiguration(port=0).port)

    def test_invalid_port_raises(self):
        for port in (-1, 65536):
            with self.subTest(port=port), self.assertRaises(ValueError):
                ServerConfiguration(port=port)

    def test_negative_shutdown_timeout_raises(self):
        with self.assertRaises(ValueError):
            ServerConfiguration(shutdown_timeout=-1)

    def test_items_cover_every_setting(self):
        names = [item.item_name for item in server_configuration_items()]

        self.assertEqual(["host", "port", "shutdown_timeout", "access_log"],
                         names)

    def test_items_are_a_new_list_each_time(self):
        self.assertIsNot(server_configuration_items(),
                         server_configuration_items())

    @patch.dict(os.environ, {}, clear=True)
    def test_from_configuration_uses_defaults(self):
        manager = ConfigurationManager()
        manager.configure(ConfigurationSetup(
            {"server": server_configuration_items()}))
        manager.process_config()

        self.assertEqual(ServerConfiguration(),
                         ServerConfiguration.from_configuration(manager))

    @patch.dict(os.environ, {"WEB_HOST": "0.0.0.0",
                             "WEB_PORT": "9001",
                             "WEB_SHUTDOWN_TIMEOUT": "3",
                             "WEB_ACCESS_LOG": "true"}, clear=True)
    def test_from_configuration_reads_environment(self):
        manager = ConfigurationManager()
        manager.configure(ConfigurationSetup(
            {"web": server_configuration_items()}))
        manager.process_config()

        config = ServerConfiguration.from_configuration(manager, "web")

        self.assertEqual(ServerConfiguration(host="0.0.0.0", port=9001,
                                             shutdown_timeout=3,
                                             access_log=True), config)
