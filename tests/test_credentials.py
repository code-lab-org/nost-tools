"""
Tests for Credentials validation with basic auth, user account, and service account modes.
"""

import unittest
from pydantic import ValidationError
from nost_tools.schemas import Credentials


class TestCredentials(unittest.TestCase):
    """Test Credentials authentication mode validation."""

    def test_basic_auth_mode_valid(self):
        """Test that basic auth mode works with only username and password (localhost)."""
        creds = Credentials(
            username="testuser",
            password="testpass"
        )
        self.assertEqual(creds.username, "testuser")
        self.assertEqual(creds.password, "testpass")
        self.assertIsNone(creds.client_id)
        self.assertIsNone(creds.client_secret_key)

    def test_service_account_mode_valid(self):
        """Test that service account mode works with only client credentials."""
        creds = Credentials(
            client_id="service-account-id",
            client_secret_key="service-account-secret"
        )
        self.assertEqual(creds.client_id, "service-account-id")
        self.assertEqual(creds.client_secret_key, "service-account-secret")
        self.assertIsNone(creds.username)
        self.assertIsNone(creds.password)

    def test_keycloak_user_account_mode_valid(self):
        """Test that Keycloak user account mode works with all credentials."""
        creds = Credentials(
            username="testuser",
            password="testpass",
            client_id="client-id",
            client_secret_key="client-secret"
        )
        self.assertEqual(creds.username, "testuser")
        self.assertEqual(creds.password, "testpass")
        self.assertEqual(creds.client_id, "client-id")
        self.assertEqual(creds.client_secret_key, "client-secret")

    def test_missing_client_id_fails(self):
        """Test that missing client_id raises validation error."""
        with self.assertRaises(ValidationError) as context:
            Credentials(
                client_secret_key="client-secret"
            )
        self.assertIn("client_id and client_secret_key must be provided together", str(context.exception))

    def test_missing_client_secret_fails(self):
        """Test that missing client_secret_key raises validation error."""
        with self.assertRaises(ValidationError) as context:
            Credentials(
                client_id="client-id"
            )
        self.assertIn("client_id and client_secret_key must be provided together", str(context.exception))

    def test_username_without_password_fails(self):
        """Test that username without password raises validation error."""
        with self.assertRaises(ValidationError) as context:
            Credentials(
                username="testuser",
                client_id="client-id",
                client_secret_key="client-secret"
            )
        self.assertIn("username and password must be provided together", str(context.exception))

    def test_password_without_username_fails(self):
        """Test that password without username raises validation error."""
        with self.assertRaises(ValidationError) as context:
            Credentials(
                password="testpass",
                client_id="client-id",
                client_secret_key="client-secret"
            )
        self.assertIn("username and password must be provided together", str(context.exception))

    def test_no_credentials_fails(self):
        """Test that no credentials at all raises validation error."""
        with self.assertRaises(ValidationError) as context:
            Credentials()
        self.assertIn("No credentials provided", str(context.exception))


if __name__ == "__main__":
    unittest.main()
