"""Utility exceptions

Contains exceptions for utility operations including file handling, concurrent operations,
LLM interactions, JSON processing, type conversions, and more.

All exceptions inherit from UtilsException (which inherits from AppException) and
support message interpolation.
"""

from typing import Any

from graphedu.common.exceptions.base import AppException

# ============================================================================
# Base utility exception
# ============================================================================


class UtilsException(AppException):
    """Base exception for all utility-related errors"""

    def __init__(self, message: str = None, **kwargs):
        """Initialize utility exception

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
            self.message = message or "Utility operation failed"

        super().__init__(self.message)


# ============================================================================
# File Related Exceptions
# ============================================================================


class FileException(UtilsException):
    """Base exception for file-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "File operation failed"
        super().__init__(message=message, **kwargs)


class UtilsFileNotFoundException(FileException):
    """File or directory not found error"""

    def __init__(self, path: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"File not found: {path}" if path else "File not found"

        super().__init__(message=message, path=path, **kwargs)


class FileReadException(FileException):
    """File read failure"""

    def __init__(self, path: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if path and reason:
                message = f"Failed to read file '{path}': {reason}"
            elif path:
                message = f"Failed to read file '{path}'"
            else:
                message = "Failed to read file"

        super().__init__(message=message, path=path, reason=reason, **kwargs)


class FileWriteException(FileException):
    """File write failure"""

    def __init__(self, path: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if path and reason:
                message = f"Failed to write file '{path}': {reason}"
            elif path:
                message = f"Failed to write file '{path}'"
            else:
                message = "Failed to write file"

        super().__init__(message=message, path=path, reason=reason, **kwargs)


class FileParseException(FileException):
    """File parsing failure"""

    def __init__(self, path: str = None, format: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if path and format:
                message = f"Failed to parse {format} file '{path}'"
            elif path:
                message = f"Failed to parse file '{path}'"
            elif reason:
                message = f"Failed to parse file: {reason}"
            else:
                message = "Failed to parse file"

        super().__init__(message=message, path=path, format=format, reason=reason, **kwargs)


# ============================================================================
# Concurrent/Async Related Exceptions
# ============================================================================


class ConcurrentException(UtilsException):
    """Base exception for concurrent/async-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Concurrent operation failed"
        super().__init__(message=message, **kwargs)


class RateLimitException(ConcurrentException):
    """Rate limit exceeded"""

    def __init__(self, rate_limit: float = None, retry_after: float = None, message: str = None, **kwargs):
        if message is None:
            if rate_limit and retry_after:
                message = f"Rate limit exceeded (limit: {rate_limit}, retry after: {retry_after}s)"
            elif retry_after:
                message = f"Rate limit exceeded, retry after {retry_after}s"
            else:
                message = "Rate limit exceeded"

        super().__init__(message=message, rate_limit=rate_limit, retry_after=retry_after, **kwargs)


class UtilsTimeoutException(ConcurrentException):
    """Operation timeout"""

    def __init__(self, timeout: float = None, operation: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and timeout:
                message = f"Operation '{operation}' timed out after {timeout}s"
            elif operation:
                message = f"Operation '{operation}' timed out"
            elif timeout:
                message = f"Operation timed out after {timeout}s"
            else:
                message = "Operation timed out"

        super().__init__(message=message, timeout=timeout, operation=operation, **kwargs)


class LockException(ConcurrentException):
    """Lock operation failure"""

    def __init__(self, lock_name: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if lock_name and reason:
                message = f"Lock '{lock_name}' operation failed: {reason}"
            elif lock_name:
                message = f"Lock '{lock_name}' operation failed"
            else:
                message = "Lock operation failed"

        super().__init__(message=message, lock_name=lock_name, reason=reason, **kwargs)


# ============================================================================
# LLM/AI Related Exceptions
# ============================================================================


class LLMException(UtilsException):
    """Base exception for LLM/AI-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "LLM operation failed"
        super().__init__(message=message, **kwargs)


class LLMConnectionException(LLMException):
    """LLM API connection failure"""

    def __init__(self, api_base: str = None, model: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if api_base and model:
                message = f"Failed to connect to LLM API '{api_base}' for model '{model}'"
            elif api_base:
                message = f"Failed to connect to LLM API '{api_base}'"
            elif reason:
                message = f"Failed to connect to LLM API: {reason}"
            else:
                message = "Failed to connect to LLM API"

        super().__init__(message=message, api_base=api_base, model=model, reason=reason, **kwargs)


class LLMRateLimitException(LLMException):
    """LLM API rate limit exceeded"""

    def __init__(self, model: str = None, retry_after: float = None, message: str = None, **kwargs):
        if message is None:
            if model and retry_after:
                message = f"LLM rate limit exceeded for model '{model}', retry after {retry_after}s"
            elif model:
                message = f"LLM rate limit exceeded for model '{model}'"
            else:
                message = "LLM rate limit exceeded"

        super().__init__(message=message, model=model, retry_after=retry_after, **kwargs)


class LLMTokenLimitException(LLMException):
    """Input exceeds token limit"""

    def __init__(self, tokens: int = None, limit: int = None, message: str = None, **kwargs):
        if message is None:
            if tokens and limit:
                message = f"Token limit exceeded: {tokens} tokens (limit: {limit})"
            else:
                message = "Token limit exceeded"

        super().__init__(message=message, tokens=tokens, limit=limit, **kwargs)


class LLMResponseException(LLMException):
    """Invalid or malformed LLM response"""

    def __init__(self, response: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"Invalid LLM response: {reason}" if reason else "Invalid LLM response"

        super().__init__(message=message, response=response, reason=reason, **kwargs)


# ============================================================================
# Import Related Exceptions
# ============================================================================


class ImportException(UtilsException):
    """Dynamic import failure"""

    def __init__(self, module_path: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if module_path and reason:
                message = f"Failed to import module '{module_path}': {reason}"
            elif module_path:
                message = f"Failed to import module '{module_path}'"
            else:
                message = "Failed to import module"

        super().__init__(message=message, module_path=module_path, reason=reason, **kwargs)


# ============================================================================
# Validation Related Exceptions
# ============================================================================


class ValidationException(UtilsException):
    """Validation failure"""

    def __init__(self, field: str = None, value: Any = None, constraint: str = None, message: str = None, **kwargs):
        if message is None:
            if field and constraint:
                message = f"Validation failed for field '{field}': {constraint}"
            elif field:
                message = f"Validation failed for field '{field}'"
            else:
                message = "Validation failed"

        super().__init__(message=message, field=field, value=value, constraint=constraint, **kwargs)


# ============================================================================
# Type Related Exceptions
# ============================================================================


class TypeException(UtilsException):
    """Base exception for type-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Type operation failed"
        super().__init__(message=message, **kwargs)


class TypeConversionException(TypeException):
    """Type conversion failure"""

    def __init__(self, value: Any = None, target_type: type = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if value and target_type and reason:
                message = f"Failed to convert {value!r} to {target_type.__name__}: {reason}"
            elif value and target_type:
                message = f"Failed to convert {value!r} to {target_type.__name__}"
            else:
                message = "Type conversion failed"

        super().__init__(message=message, value=value, target_type=target_type, reason=reason, **kwargs)


# ============================================================================
# JSON Related Exceptions
# ============================================================================


class JSONException(UtilsException):
    """Base exception for JSON-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "JSON operation failed"
        super().__init__(message=message, **kwargs)


class JSONParseException(JSONException):
    """JSON parsing failure"""

    def __init__(self, input_str: str = None, reason: str = None, attempt: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"Failed to parse JSON: {reason}" if reason else "Failed to parse JSON"

        super().__init__(message=message, input_str=input_str, reason=reason, attempt=attempt, **kwargs)


class JSONValidationException(JSONException):
    """JSON validation failure"""

    def __init__(
        self, json_obj: Any = None, expected_type: str = None, actual_type: str = None, message: str = None, **kwargs
    ):
        if message is None:
            if expected_type and actual_type:
                message = f"JSON validation failed: expected {expected_type}, got {actual_type}"
            else:
                message = "JSON validation failed"

        super().__init__(
            message=message, json_obj=json_obj, expected_type=expected_type, actual_type=actual_type, **kwargs
        )


# ============================================================================
# Password Related Exceptions
# ============================================================================


class PasswordException(UtilsException):
    """Password operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Password {operation} failed: {reason}"
            elif operation:
                message = f"Password {operation} failed"
            else:
                message = "Password operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


# ============================================================================
# Value/Validation Related Exceptions
# ============================================================================


class ValueException(UtilsException):
    """Invalid value error"""

    def __init__(self, value: Any = None, field: str = None, constraint: str = None, message: str = None, **kwargs):
        if message is None:
            if field and constraint:
                message = f"Invalid value for field '{field}': {constraint}"
            elif field:
                message = f"Invalid value for field '{field}'"
            else:
                message = "Invalid value"

        super().__init__(message=message, value=value, field=field, constraint=constraint, **kwargs)


# ============================================================================
# Utility Functions
# ============================================================================


def format_exception(exc: Exception) -> str:
    """Format an exception into a readable string

    Args:
        exc: The exception to format

    Returns:
        A formatted error message string
    """
    if isinstance(exc, UtilsException):
        return f"{exc.__class__.__name__}: {exc.message}"
    return f"{exc.__class__.__name__}: {exc!s}"


def get_exception_chain(exc: Exception) -> list[Exception]:
    """Get the chain of exceptions (for exception chaining)

    Args:
        exc: The exception to get the chain from

    Returns:
        List of exceptions in the chain
    """
    chain = []
    current = exc
    while current:
        chain.append(current)
        current = current.__cause__ if hasattr(current, "__cause__") else None
    return chain


# Export all exceptions
__all__ = [
    # Concurrent/Async related
    "ConcurrentException",
    # File related
    "FileException",
    "FileParseException",
    "FileReadException",
    "FileWriteException",
    # Import related
    "ImportException",
    # JSON related
    "JSONException",
    "JSONParseException",
    "JSONValidationException",
    "LLMConnectionException",
    # LLM related
    "LLMException",
    "LLMRateLimitException",
    "LLMResponseException",
    "LLMTokenLimitException",
    "LockException",
    # Password related
    "PasswordException",
    "RateLimitException",
    "TypeConversionException",
    # Type related
    "TypeException",
    # Base
    "UtilsException",
    "UtilsFileNotFoundException",
    "UtilsTimeoutException",
    # Validation related
    "ValidationException",
    # Value related
    "ValueException",
    # Utility functions
    "format_exception",
    "get_exception_chain",
]
