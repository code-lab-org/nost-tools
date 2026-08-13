"""
Provides object models for common data structures.
"""

class ConfigurationError(Exception):
    """Configuration error"""


class EnvironmentVariableError(Exception):
    """Environment variable error"""


class ConfigAssertionError(Exception):  # Renamed to avoid shadowing built-in
    """Assertion error for configuration validation"""


class ConnectionTimeoutError(ConnectionError):
    """
    Raised when a connection and channel do not open within the configured time.

    Subclasses the built-in ConnectionError so existing handlers catching that
    continue to work.
    """
