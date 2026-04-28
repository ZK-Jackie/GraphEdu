"""JWT token creation and validation utilities.

This module provides functions for creating and validating JWT tokens
with configurable expiration times and algorithms.
"""

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

import jwt

from ..exceptions.services.system.auth import (
    TokenException,
    TokenExpiredException,
    TokenSignatureInvalidException,
)

logger = logging.getLogger(__name__)


def create_token(
    payload: dict[str, Any],
    secret: str = "YOU_HAVE_TO_CHANGE_THIS_SECRET_KEY_BEFORE_USING",
    *,
    expire: timedelta | datetime = timedelta(minutes=120),
    algorithm: str = "HS512",
) -> str | None:
    """Create token with payload

    :param payload: payload dict
    :param secret: secret key, you'd better change it before using, 32 bytes or more for hs512
    :param expire: expiration time in minutes
    :param algorithm: algorithm to use
    :return: token string
    :raises TokenException: token creation fails
    """
    try:
        if isinstance(expire, timedelta):
            return jwt.encode(
                {
                    **payload,
                    "timestamp": datetime.now(UTC).timestamp(),
                    "exp": datetime.now(UTC) + expire,
                },
                secret,
                algorithm=algorithm,
            )
        if isinstance(expire, datetime):
            return jwt.encode(
                {
                    **payload,
                    "timestamp": datetime.now(UTC).timestamp(),
                    "exp": expire,
                },
                secret,
                algorithm=algorithm,
            )
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise TokenException("Failed to create token", reason=str(e)) from None


def validate_token(
    token: str,
    secret: str = "YOU_HAVE_TO_CHANGE_THIS_SECRET_KEY_BEFORE_USING",
    *,
    algorithms: str | list[str] = "HS512",
) -> dict[str, Any]:
    """Validate token and return decoded payload

    :param token: token string
    :param secret: secret key, you'd better change it before using, 32 bytes or more for hs512
    :param algorithms: algorithm to use, default is HS512
    :raises TokenExpiredException: if token is expired
    :raises TokenSignatureInvalidException: if token signature is invalid or token is malformed
    :raises TokenException: for other token-related errors
    :return: decoded payload
    """
    if not isinstance(algorithms, list):
        algorithms = [algorithms]

    try:
        return jwt.decode(token, secret, algorithms=algorithms)
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Token expired: {e}")
        raise TokenExpiredException(
            "Token has expired",
            token=token[:20] + "..." if len(token) > 20 else token,
        ) from None
    except jwt.InvalidSignatureError as e:
        logger.warning(f"Invalid token signature: {e}")
        raise TokenSignatureInvalidException(
            "Invalid token signature",
            token=token[:20] + "..." if len(token) > 20 else token,
            reason="InvalidSignatureError",
        ) from None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise TokenSignatureInvalidException(
            "Invalid token", token=token[:20] + "..." if len(token) > 20 else token, reason=str(e)
        ) from None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise TokenException(
            "Token validation failed", token=token[:20] + "..." if len(token) > 20 else token, reason=str(e)
        ) from None
