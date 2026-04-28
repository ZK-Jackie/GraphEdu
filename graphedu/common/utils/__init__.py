"""Common Utility Functions

This module provides a collection of reusable utility functions for:
- File operations
- String manipulation
- Async/concurrent operations
- Object utilities
- LLM-related utilities
- And more...

Usage:
    from graphedu.common.utils import (
        read_yaml,
        is_primitive_type,
        AsyncRateLimiter
    )
"""

# Import exception classes from exceptions module for backward compatibility
from ..exceptions import (
    ConcurrentException,
    ConfigurationException,
    FileException,
    FileParseException,
    FileReadException,
    FileWriteException,
    ImportException,
    JSONException,
    JSONParseException,
    JSONValidationException,
    LLMConnectionException,
    LLMException,
    LLMRateLimitException,
    LLMResponseException,
    LLMTokenLimitException,
    LockException,
    PasswordException,
    RateLimitException,
    TypeConversionException,
    TypeException,
    UtilsException,
    UtilsFileNotFoundException as FileNotFound,
    UtilsTimeoutException as TimeoutException,
    ValidationException,
    ValueException,
    format_exception,
    get_exception_chain,
)
from .concurrent import AsyncRateLimiter

# Core utilities
from .files import (
    async_get_file_md5,
    ensure_path,
    ensure_str_path,
    get_file_md5,
    is_dir,
    is_file,
    is_file_exists,
    list_files,
    read_yaml,
    save_file,
)
from .jsons import serializable, try_parse_ast_to_json, try_parse_json_object
from .objects import (
    cp_dict_attr,
    get_class,
    get_specific_class_from_union,
    import_from_string,
    is_primitive_object,
    is_primitive_type,
)
from .password import PasswordUtil
from .strings import (
    get_datetime,
    get_timestamp_ms,
    get_timestamp_s,
    get_timestamp_us,
    str_to_bool,
    timestamp_to_datetime,
)
from .token import create_token, validate_token
from .uuids import uuid7, uuid7_str

__all__ = [
    # Concurrent utilities
    "AsyncRateLimiter",
    "ConcurrentException",
    "ConfigurationException",
    "FileException",
    "FileNotFound",
    "FileParseException",
    "FileReadException",
    "FileWriteException",
    "ImportException",
    "JSONException",
    "JSONParseException",
    "JSONValidationException",
    "LLMConnectionException",
    "LLMException",
    "LLMRateLimitException",
    "LLMResponseException",
    "LLMTokenLimitException",
    "LockException",
    "PasswordException",
    # Password utilities
    "PasswordUtil",
    "RateLimitException",
    "TimeoutException",
    "TypeConversionException",
    "TypeException",
    # Exceptions
    "UtilsException",
    "ValidationException",
    "ValueException",
    "async_get_file_md5",
    # Object utilities
    "cp_dict_attr",
    # Token utilities
    "create_token",
    # File utilities
    "ensure_path",
    "ensure_str_path",
    "format_exception",
    "get_class",
    "get_datetime",
    "get_exception_chain",
    "get_file_md5",
    "get_specific_class_from_union",
    "get_timestamp_ms",
    # String utilities
    "get_timestamp_s",
    "get_timestamp_us",
    "import_from_string",
    "is_dir",
    "is_file",
    "is_file_exists",
    "is_primitive_object",
    "is_primitive_type",
    "list_files",
    "read_yaml",
    "save_file",
    "serializable",
    "str_to_bool",
    "timestamp_to_datetime",
    "try_parse_ast_to_json",
    # JSON utilities
    "try_parse_json_object",
    "uuid7",
    "uuid7_str",
    "validate_token",
]
