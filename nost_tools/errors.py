"""
Provides object models for common data structures.
"""

class ConfigurationError(Exception):
    """Configuration error"""


class EnvironmentVariableError(Exception):
    """Environment variable error"""


class ConfigAssertionError(Exception):  # Renamed to avoid shadowing built-in
    """Assertion error for configuration validation"""
