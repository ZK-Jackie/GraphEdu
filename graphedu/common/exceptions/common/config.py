"""Configuration-related exceptions

Contains exceptions for configuration file reading, parsing, validation, and instantiation.
All exceptions inherit from AppException and support message interpolation.
"""

from graphedu.common.exceptions.base import AppException

# ============================================================================
# Base configuration exception
# ============================================================================


class ConfigurationException(AppException):
    """Base exception for all configuration-related errors"""

    def __init__(self, message: str = None, **kwargs):
        """Initialize configuration exception

        Args:
            message: Error message template (can contain placeholders for formatting)
            **kwargs: Parameters for message interpolation
        """
        self.kwargs = kwargs

        # Format message if kwargs provided
        if message and kwargs:
            try:
                self.message = message.format(**kwargs)
            except (KeyError, ValueError):
                # If formatting fails, use original message
                self.message = message
        else:
            self.message = message or "Configuration operation failed"

        super().__init__(self.message)


# ============================================================================
# Configuration read exceptions
# ============================================================================


class ConfigurationReadException(ConfigurationException):
    """Configuration file read failure"""

    def __init__(self, config_path: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_path and reason:
                message = f"Failed to read configuration file '{config_path}': {reason}"
            elif config_path:
                message = f"Failed to read configuration file '{config_path}'"
            else:
                message = "Failed to read configuration"

        super().__init__(message=message, config_path=config_path, reason=reason, **kwargs)


# ============================================================================
# Configuration write exceptions
# ============================================================================


class ConfigurationWriteException(ConfigurationException):
    """Configuration file write failure"""

    def __init__(self, config_path: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_path and reason:
                message = f"Failed to write configuration file '{config_path}': {reason}"
            elif config_path:
                message = f"Failed to write configuration file '{config_path}'"
            else:
                message = "Failed to write configuration"

        super().__init__(message=message, config_path=config_path, reason=reason, **kwargs)


# ============================================================================
# Configuration parse exceptions
# ============================================================================


class ConfigurationParseException(ConfigurationException):
    """Configuration file parsing failure"""

    def __init__(self, config_path: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_path and reason:
                message = f"Failed to parse configuration file '{config_path}': {reason}"
            elif config_path:
                message = f"Failed to parse configuration file '{config_path}'"
            elif reason:
                message = f"Failed to parse configuration: {reason}"
            else:
                message = "Failed to parse configuration"

        super().__init__(message=message, config_path=config_path, reason=reason, **kwargs)


# ============================================================================
# Configuration instantiation exceptions
# ============================================================================


class ConfigurationInstantiationException(ConfigurationException):
    """Configuration class instantiation failure"""

    def __init__(self, class_name: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if class_name and reason:
                message = f"Failed to instantiate configuration class '{class_name}': {reason}"
            elif class_name:
                message = f"Failed to instantiate configuration class '{class_name}'"
            elif reason:
                message = f"Failed to instantiate configuration: {reason}"
            else:
                message = "Failed to instantiate configuration"

        super().__init__(message=message, class_name=class_name, reason=reason, **kwargs)


# Export all exceptions
__all__ = [
    "ConfigurationException",
    "ConfigurationInstantiationException",
    "ConfigurationParseException",
    "ConfigurationReadException",
    "ConfigurationWriteException",
]
