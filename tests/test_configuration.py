"""
Tests for YAML configuration loading, server settings, and TLS verification fields.
"""

import os
import tempfile
import unittest

from nost_tools.configuration import ConnectionConfig
from nost_tools.errors import ConfigurationError
from nost_tools.schemas import KeycloakConfig, RabbitMQConfig

MINIMAL_YAML = """
info:
  title: Test configuration
  version: '1.0.0'
  description: Minimal configuration for tests
servers:
  rabbitmq:
    keycloak_authentication: False
    host: "localhost"
    port: 5672
    tls: False
    virtual_host: "/"
execution:
  general:
    prefix: test
"""


def write_yaml(contents):
    """Writes contents to a temporary YAML file and returns its path."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    handle.write(contents)
    handle.close()
    return handle.name


class TestYamlLoading(unittest.TestCase):
    def setUp(self):
        # ConnectionConfig reads credentials from the environment for non-Keycloak
        # servers, so provide them rather than depending on the developer's shell
        self._saved = {k: os.environ.get(k) for k in ("USERNAME", "PASSWORD")}
        os.environ["USERNAME"] = "testuser"
        os.environ["PASSWORD"] = "testpass"
        self.paths = []

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for path in self.paths:
            os.unlink(path)

    def load(self, contents):
        path = write_yaml(contents)
        self.paths.append(path)
        return ConnectionConfig(yaml_file=path)

    def test_loads_server_settings_from_yaml(self):
        config = self.load(MINIMAL_YAML)
        rabbitmq = config.rc.server_configuration.servers.rabbitmq
        self.assertEqual(rabbitmq.host, "localhost")
        self.assertEqual(rabbitmq.port, 5672)
        self.assertFalse(rabbitmq.tls)
        self.assertFalse(rabbitmq.keycloak_authentication)

    def test_credentials_are_read_from_the_environment(self):
        config = self.load(MINIMAL_YAML)
        self.assertEqual(config.rc.credentials.username, "testuser")
        self.assertEqual(config.rc.credentials.password, "testpass")

    def test_missing_file_raises(self):
        with self.assertRaises(Exception):
            ConnectionConfig(yaml_file="/nonexistent/path/to/config.yaml")

    def test_malformed_yaml_raises(self):
        with self.assertRaises(Exception):
            self.load("servers:\n  rabbitmq:\n    host: [unclosed\n")

    def test_unspecified_fields_take_schema_defaults(self):
        config = self.load(MINIMAL_YAML)
        rabbitmq = config.rc.server_configuration.servers.rabbitmq
        self.assertEqual(rabbitmq.virtual_host, "/")
        self.assertEqual(rabbitmq.frame_max, 131072)
        self.assertEqual(rabbitmq.queue_max_size, 5000)


class TestTlsVerificationFields(unittest.TestCase):
    """
    Covers the certificate verification settings added in 3.2.0.

    An unset tls_ca_cert means the system trust store is used, which is what every
    deployment against a publicly-trusted broker relies on.
    """

    def test_rabbitmq_defaults_to_the_system_trust_store(self):
        self.assertIsNone(RabbitMQConfig().tls_ca_cert)

    def test_keycloak_defaults_to_the_system_trust_store(self):
        self.assertIsNone(KeycloakConfig().tls_ca_cert)

    def test_rabbitmq_accepts_a_certificate_path(self):
        config = RabbitMQConfig(tls_ca_cert="/etc/certs/broker.pem")
        self.assertEqual(config.tls_ca_cert, "/etc/certs/broker.pem")

    def test_keycloak_accepts_a_certificate_path(self):
        config = KeycloakConfig(tls_ca_cert="/etc/certs/keycloak.pem")
        self.assertEqual(config.tls_ca_cert, "/etc/certs/keycloak.pem")

    def test_certificate_paths_are_configured_per_server(self):
        """
        A self-hosted broker and a NASA-hosted Keycloak are configured
        independently, so setting one must not affect the other.
        """
        rabbitmq = RabbitMQConfig(tls_ca_cert="/etc/certs/broker.pem")
        keycloak = KeycloakConfig()
        self.assertEqual(rabbitmq.tls_ca_cert, "/etc/certs/broker.pem")
        self.assertIsNone(keycloak.tls_ca_cert)

    def test_tls_defaults_to_disabled(self):
        self.assertFalse(RabbitMQConfig().tls)
        self.assertFalse(KeycloakConfig().tls)


if __name__ == "__main__":
    unittest.main()
