"""Application-related utility functions.

This module provides utility functions for application-level operations,
including environment detection and request handling.
"""

from starlette.datastructures import Headers


def is_in_openapi(headers: dict[str, str] | Headers) -> bool:
    """Check if the current environment is an OpenAPI environment.

    Returns:
        bool: True if in OpenAPI environment, False otherwise.
    """
    request_from_swagger = headers.get("referer", '').endswith("docs") if headers.get("referer") else False
    request_from_redoc = headers.get("referer", '').endswith("redoc") if headers.get("referer") else False
    return request_from_swagger or request_from_redoc
