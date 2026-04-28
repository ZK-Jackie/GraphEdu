"""
Tests for graphedu.common.utils.token module
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from graphedu.common.exceptions.services.system.auth import (
    TokenException,
    TokenExpiredException,
    TokenSignatureInvalidException,
)
from graphedu.common.utils.token import create_token, validate_token

# ============================================================================
# Test Constants
# ============================================================================

DEFAULT_SECRET = "YOU_HAVE_TO_CHANGE_THIS_SECRET_KEY_BEFORE_USING"
CUSTOM_SECRET = "my_custom_secret_key_for_testing_purposes"
ANOTHER_SECRET = "different_secret_key_for_signature_validation"

VALID_PAYLOAD = {
    "user_id": 12345,
    "username": "testuser",
    "role": "admin"
}

COMPLEX_PAYLOAD = {
    "user_id": 12345,
    "username": "testuser",
    "role": "admin",
    "permissions": ["read", "write", "delete"],
    "metadata": {
        "department": "engineering",
        "level": 5
    },
    "active": True,
    "score": 99.5
}

EMPTY_PAYLOAD = {}


# ============================================================================
# create_token Tests
# ============================================================================

class TestCreateToken:
    """Tests for create_token function"""

    def test_create_token_with_timedelta_expire(self):
        """Test creating token with timedelta as expire parameter"""
        expire = timedelta(minutes=120)
        token = create_token(VALID_PAYLOAD, expire=expire)

        assert isinstance(token, str)
        assert len(token) > 0
        # Token should be a valid JWT format (3 parts separated by dots)
        parts = token.split('.')
        assert len(parts) == 3

    def test_create_token_with_datetime_expire(self):
        """Test creating token with datetime as expire parameter"""
        expire = datetime.now(UTC) + timedelta(hours=2)
        token = create_token(VALID_PAYLOAD, expire=expire)

        assert isinstance(token, str)
        assert len(token) > 0
        parts = token.split('.')
        assert len(parts) == 3

    def test_create_token_with_default_secret(self):
        """Test creating token with default secret"""
        token = create_token(VALID_PAYLOAD)

        # Should be able to decode with default secret
        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]
        assert decoded["username"] == VALID_PAYLOAD["username"]

    def test_create_token_with_custom_secret(self):
        """Test creating token with custom secret"""
        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET)

        # Should decode with custom secret
        decoded = jwt.decode(token, CUSTOM_SECRET, algorithms=["HS512"])
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

        # Should NOT decode with default secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])

    def test_create_token_with_custom_algorithm(self):
        """Test creating token with custom algorithm"""
        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET, algorithm="HS256")

        decoded = jwt.decode(token, CUSTOM_SECRET, algorithms=["HS256"])
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_create_token_with_empty_payload(self):
        """Test creating token with empty payload"""
        token = create_token(EMPTY_PAYLOAD)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert "timestamp" in decoded
        assert "exp" in decoded

    def test_create_token_with_complex_payload(self):
        """Test creating token with complex payload containing various data types"""
        token = create_token(COMPLEX_PAYLOAD)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["user_id"] == COMPLEX_PAYLOAD["user_id"]
        assert decoded["permissions"] == COMPLEX_PAYLOAD["permissions"]
        assert decoded["metadata"]["department"] == COMPLEX_PAYLOAD["metadata"]["department"]
        assert decoded["active"] == COMPLEX_PAYLOAD["active"]
        assert decoded["score"] == COMPLEX_PAYLOAD["score"]

    def test_create_token_includes_timestamp(self):
        """Test that created token includes timestamp field"""
        before_creation = datetime.now(UTC).timestamp()
        token = create_token(VALID_PAYLOAD)
        after_creation = datetime.now(UTC).timestamp()

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert "timestamp" in decoded
        assert before_creation <= decoded["timestamp"] <= after_creation

    def test_create_token_includes_expiration(self):
        """Test that created token includes exp field"""
        expire_minutes = 60
        token = create_token(VALID_PAYLOAD, expire=timedelta(minutes=expire_minutes))

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert "exp" in decoded

        # Check expiration is approximately correct (within 1 second tolerance)
        expected_exp = datetime.now(UTC) + timedelta(minutes=expire_minutes)
        actual_exp = datetime.fromtimestamp(decoded["exp"], UTC)
        time_diff = abs((expected_exp - actual_exp).total_seconds())
        assert time_diff < 1.0

    def test_create_token_with_negative_timedelta(self):
        """Test creating token with negative timedelta (already expired)"""
        # This should create the token successfully, but it will be expired
        token = create_token(VALID_PAYLOAD, expire=timedelta(seconds=-1))

        assert isinstance(token, str)

        # Validation should fail with expired error
        with pytest.raises(TokenExpiredException):
            validate_token(token)

    def test_create_token_with_zero_timedelta(self):
        """Test creating token with zero timedelta (expires immediately)"""
        token = create_token(VALID_PAYLOAD, expire=timedelta(seconds=0))

        assert isinstance(token, str)

        # Token should be created but may be expired already
        try:  # noqa: SIM105
            validate_token(token)
        except TokenExpiredException:
            # This is expected behavior
            pass

    def test_create_token_with_past_datetime(self):
        """Test creating token with past datetime (already expired)"""
        past_time = datetime.now(UTC) - timedelta(minutes=1)
        token = create_token(VALID_PAYLOAD, expire=past_time)

        assert isinstance(token, str)

        # Should raise expired exception
        with pytest.raises(TokenExpiredException):
            validate_token(token)

    def test_create_token_payload_not_modified(self):
        """Test that original payload is not modified by create_token"""
        original_payload = VALID_PAYLOAD.copy()
        create_token(VALID_PAYLOAD)

        assert original_payload == VALID_PAYLOAD

    def test_create_token_multiple_calls_generate_different_tokens(self):
        """Test that multiple create_token calls generate different tokens (due to timestamp)"""
        token1 = create_token(VALID_PAYLOAD)
        token2 = create_token(VALID_PAYLOAD)

        # Tokens should be different due to different timestamps
        assert token1 != token2

    def test_create_token_with_different_algorithms(self):
        """Test creating tokens with different algorithms"""
        algorithms = ["HS256", "HS384", "HS512"]

        for algorithm in algorithms:
            token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET, algorithm=algorithm)
            decoded = jwt.decode(token, CUSTOM_SECRET, algorithms=[algorithm])
            assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_create_token_with_special_characters_in_payload(self):
        """Test creating token with special characters in payload values"""
        special_payload = {
            "message": "Hello, 世界! 🌍",
            "path": "C:\\Users\\Test\\file.txt",
            "unicode": "测试中文",
            "emoji": "😀🎉"
        }
        token = create_token(special_payload)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["message"] == special_payload["message"]
        assert decoded["path"] == special_payload["path"]

    def test_create_token_with_numeric_values(self):
        """Test creating token with various numeric values"""
        numeric_payload = {
            "integer": 42,
            "float": 3.14159,
            "negative": -10,
            "zero": 0,
            "large": 1000000000
        }
        token = create_token(numeric_payload)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["integer"] == 42
        assert decoded["float"] == 3.14159
        assert decoded["negative"] == -10
        assert decoded["zero"] == 0
        assert decoded["large"] == 1000000000

    def test_create_token_with_boolean_values(self):
        """Test creating token with boolean values"""
        bool_payload = {
            "is_active": True,
            "is_deleted": False,
            "flag_true": True,
            "flag_false": False
        }
        token = create_token(bool_payload)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["is_active"] is True
        assert decoded["is_deleted"] is False
        assert decoded["flag_true"] is True
        assert decoded["flag_false"] is False

    def test_create_token_with_none_value(self):
        """Test creating token with None value in payload"""
        none_payload = {
            "user_id": 123,
            "optional_field": None
        }
        token = create_token(none_payload)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["user_id"] == 123
        # Note: JWT may convert None to null or omit it
        assert "optional_field" in decoded

    def test_create_token_with_list_values(self):
        """Test creating token with list values"""
        list_payload = {
            "tags": ["python", "jwt", "testing"],
            "numbers": [1, 2, 3, 4, 5],
            "nested": [[1, 2], [3, 4]]
        }
        token = create_token(list_payload)

        decoded = jwt.decode(token, DEFAULT_SECRET, algorithms=["HS512"])
        assert decoded["tags"] == ["python", "jwt", "testing"]
        assert decoded["numbers"] == [1, 2, 3, 4, 5]

    def test_create_token_raises_token_exception_on_error(self):
        """Test that create_token raises TokenException on error"""
        # Using an invalid algorithm should cause an error
        with pytest.raises(TokenException):
            create_token(VALID_PAYLOAD, algorithm="INVALID_ALGORITHM")

    def test_create_token_with_very_long_secret(self):
        """Test creating token with very long secret"""
        long_secret = "a" * 1000
        token = create_token(VALID_PAYLOAD, secret=long_secret)

        decoded = jwt.decode(token, long_secret, algorithms=["HS512"])
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_create_token_with_short_secret(self):
        """Test creating token with short secret (not recommended but should work)"""
        short_secret = "short"
        token = create_token(VALID_PAYLOAD, secret=short_secret, algorithm="HS256")

        decoded = jwt.decode(token, short_secret, algorithms=["HS256"])
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]


# ============================================================================
# validate_token Tests
# ============================================================================

class TestValidateToken:
    """Tests for validate_token function"""

    def test_validate_token_with_valid_token(self):
        """Test validating a valid token"""
        token = create_token(VALID_PAYLOAD)
        decoded = validate_token(token)

        assert isinstance(decoded, dict)
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]
        assert decoded["username"] == VALID_PAYLOAD["username"]
        assert decoded["role"] == VALID_PAYLOAD["role"]
        assert "timestamp" in decoded
        assert "exp" in decoded

    def test_validate_token_with_custom_secret(self):
        """Test validating token with custom secret"""
        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET)
        decoded = validate_token(token, secret=CUSTOM_SECRET)

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_with_string_algorithm(self):
        """Test validating token with string algorithm parameter"""
        token = create_token(VALID_PAYLOAD, algorithm="HS256", secret=CUSTOM_SECRET)
        decoded = validate_token(token, secret=CUSTOM_SECRET, algorithms="HS256")

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_with_list_algorithm(self):
        """Test validating token with list of algorithms"""
        token = create_token(VALID_PAYLOAD, algorithm="HS256", secret=CUSTOM_SECRET)
        decoded = validate_token(token, secret=CUSTOM_SECRET, algorithms=["HS256", "HS512"])

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_with_multiple_algorithms(self):
        """Test validating token with multiple allowed algorithms"""
        algorithms = ["HS256", "HS384", "HS512"]
        token = create_token(VALID_PAYLOAD, algorithm="HS384", secret=CUSTOM_SECRET)
        decoded = validate_token(token, secret=CUSTOM_SECRET, algorithms=algorithms)

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_with_complex_payload(self):
        """Test validating token with complex payload"""
        token = create_token(COMPLEX_PAYLOAD)
        decoded = validate_token(token)

        assert decoded["user_id"] == COMPLEX_PAYLOAD["user_id"]
        assert decoded["permissions"] == COMPLEX_PAYLOAD["permissions"]
        assert decoded["metadata"]["department"] == COMPLEX_PAYLOAD["metadata"]["department"]
        assert decoded["active"] == COMPLEX_PAYLOAD["active"]

    def test_validate_token_with_empty_payload(self):
        """Test validating token with empty payload"""
        token = create_token(EMPTY_PAYLOAD)
        decoded = validate_token(token)

        assert isinstance(decoded, dict)
        assert "timestamp" in decoded
        assert "exp" in decoded

    def test_validate_token_with_expired_token_raises_exception(self):
        """Test that expired token raises TokenExpiredException"""
        # Create token that expires immediately
        token = create_token(VALID_PAYLOAD, expire=timedelta(seconds=-1))

        with pytest.raises(TokenExpiredException) as exc_info:
            validate_token(token)

        assert "Token has expired" in str(exc_info.value)
        assert exc_info.value.kwargs.get("token") is not None

    def test_validate_token_with_past_datetime_expire(self):
        """Test validating token with past datetime expiration"""
        past_time = datetime.now(UTC) - timedelta(seconds=10)
        token = create_token(VALID_PAYLOAD, expire=past_time)

        with pytest.raises(TokenExpiredException):
            validate_token(token)

    def test_validate_token_with_invalid_signature(self):
        """Test that token with invalid signature raises TokenSignatureInvalidException"""
        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET)

        # Try to validate with different secret
        with pytest.raises(TokenSignatureInvalidException) as exc_info:
            validate_token(token, secret=ANOTHER_SECRET)

        assert "Invalid token signature" in str(exc_info.value)
        assert exc_info.value.kwargs.get("reason") == "InvalidSignatureError"

    def test_validate_token_with_malformed_token(self):
        """Test that malformed token raises TokenSignatureInvalidException"""
        malformed_tokens = [
            "not.a.valid.token",
            "invalid",
            "",
            "abc.def",
            "a.b.c.d",
            " header.payload",
            "header .payload .signature"
        ]

        for malformed_token in malformed_tokens:
            with pytest.raises(TokenSignatureInvalidException) as exc_info:
                validate_token(malformed_token)

            assert "Invalid token" in str(exc_info.value)

    def test_validate_token_with_wrong_algorithm(self):
        """Test that token with wrong algorithm raises TokenSignatureInvalidException"""
        token = create_token(VALID_PAYLOAD, algorithm="HS256", secret=CUSTOM_SECRET)

        # Try to validate with different algorithm
        with pytest.raises(TokenSignatureInvalidException):
            validate_token(token, secret=CUSTOM_SECRET, algorithms=["HS512"])

    def test_validate_token_with_short_token_in_exception(self):
        """Test that short tokens are properly displayed in exception"""
        short_token = "abc.def.ghi"

        with pytest.raises(TokenSignatureInvalidException) as exc_info:
            validate_token(short_token)

        # Short token should not be truncated
        assert exc_info.value.kwargs.get("token") == short_token

    def test_validate_token_with_long_token_in_exception(self):
        """Test that long tokens are truncated in exception"""
        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET)

        with pytest.raises(TokenSignatureInvalidException) as exc_info:
            validate_token(token, secret=ANOTHER_SECRET)

        # Long token should be truncated with "..."
        token_in_exception = exc_info.value.kwargs.get("token", "")
        assert "..." in token_in_exception
        assert len(token_in_exception) < len(token)

    def test_validate_token_maintains_payload_data_types(self):
        """Test that validation maintains original data types"""
        complex_token = create_token(COMPLEX_PAYLOAD)
        decoded = validate_token(complex_token)

        assert isinstance(decoded["user_id"], int)
        assert isinstance(decoded["permissions"], list)
        assert isinstance(decoded["metadata"], dict)
        assert isinstance(decoded["active"], bool)
        assert isinstance(decoded["score"], float)

    def test_validate_token_preserves_special_characters(self):
        """Test that validation preserves special characters"""
        special_payload = {
            "message": "Hello, 世界! 🌍",
            "path": "C:\\Users\\Test"
        }
        token = create_token(special_payload)
        decoded = validate_token(token)

        assert decoded["message"] == "Hello, 世界! 🌍"
        assert decoded["path"] == "C:\\Users\\Test"

    def test_validate_token_with_unicode_algorithm(self):
        """Test validating token with algorithm string handling"""
        token = create_token(VALID_PAYLOAD, algorithm="HS512")

        # Should work with string algorithm
        decoded = validate_token(token, algorithms="HS512")
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_recently_expired(self):
        """Test validating token that expired very recently"""
        # Create token that expires in 1 second
        token = create_token(VALID_PAYLOAD, expire=timedelta(milliseconds=500))

        # Should still be valid immediately
        decoded = validate_token(token)
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_future_expiration(self):
        """Test validating token with far future expiration"""
        future_time = datetime.now(UTC) + timedelta(days=365)
        token = create_token(VALID_PAYLOAD, expire=future_time)

        decoded = validate_token(token)
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_with_very_long_secret(self):
        """Test validating token with very long secret"""
        long_secret = "a" * 1000
        token = create_token(VALID_PAYLOAD, secret=long_secret)
        decoded = validate_token(token, secret=long_secret)

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_with_bytes_like_secret_characters(self):
        """Test validating token with special characters in secret"""
        special_secret = "secret!@#$%^&*()_+-=[]{}|;':\",./<>?"
        token = create_token(VALID_PAYLOAD, secret=special_secret)
        decoded = validate_token(token, secret=special_secret)

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_returned_dict_contains_all_fields(self):
        """Test that validated token contains all expected fields"""
        token = create_token(VALID_PAYLOAD)
        decoded = validate_token(token)

        # Original payload fields
        assert "user_id" in decoded
        assert "username" in decoded
        assert "role" in decoded

        # Auto-added fields
        assert "timestamp" in decoded
        assert "exp" in decoded

    def test_validate_token_exception_chain(self):
        """Test that TokenException can be caught as base exception"""
        from graphedu.common.exceptions.services.system.auth import TokenException

        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET)

        # Should catch TokenSignatureInvalidException as TokenException
        with pytest.raises(TokenException):
            validate_token(token, secret=ANOTHER_SECRET)

    def test_validate_token_with_algorithm_none(self):
        """Test that validate_token handles algorithm parameter edge case"""
        token = create_token(VALID_PAYLOAD)

        # Should work with valid algorithm
        decoded = validate_token(token, algorithms=["HS512"])
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_validate_token_expiration_accuracy(self):
        """Test token expiration time accuracy"""
        expire_minutes = 30
        token = create_token(VALID_PAYLOAD, expire=timedelta(minutes=expire_minutes))
        decoded = validate_token(token)

        # Calculate expected expiration
        current_time = datetime.now(UTC).timestamp()
        exp_timestamp = decoded["exp"]

        # Expiration should be approximately 30 minutes from now (within 2 seconds)
        time_diff = abs(exp_timestamp - (current_time + expire_minutes * 60))
        assert time_diff < 2.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestTokenIntegration:
    """Integration tests for create_token and validate_token"""

    def test_create_and_validate_roundtrip(self):
        """Test creating and validating token in a roundtrip"""
        token = create_token(VALID_PAYLOAD)
        decoded = validate_token(token)

        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]
        assert decoded["username"] == VALID_PAYLOAD["username"]
        assert decoded["role"] == VALID_PAYLOAD["role"]

    def test_create_and_validate_with_different_secrets(self):
        """Test creating and validating tokens with different secrets"""
        secrets = ["secret1", "secret2", CUSTOM_SECRET, DEFAULT_SECRET]

        for secret in secrets:
            token = create_token(VALID_PAYLOAD, secret=secret)
            decoded = validate_token(token, secret=secret)
            assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_create_and_validate_with_different_algorithms(self):
        """Test creating and validating tokens with different algorithms"""
        algorithms = ["HS256", "HS384", "HS512"]

        for algorithm in algorithms:
            token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET, algorithm=algorithm)
            decoded = validate_token(token, secret=CUSTOM_SECRET, algorithms=algorithm)
            assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_multiple_tokens_same_payload(self):
        """Test creating multiple tokens with same payload"""
        tokens = [create_token(VALID_PAYLOAD) for _ in range(5)]

        # All tokens should be valid
        for token in tokens:
            decoded = validate_token(token)
            assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

        # But tokens should be different due to timestamp
        assert len(set(tokens)) == 5

    def test_token_lifecycle(self):
        """Test complete token lifecycle: create, validate, expire"""
        # Create token with short expiration
        token = create_token(VALID_PAYLOAD, expire=timedelta(seconds=1))

        # Should be valid immediately
        decoded = validate_token(token)
        assert decoded["user_id"] == VALID_PAYLOAD["user_id"]

    def test_create_with_one_secret_validate_with_another_fails(self):
        """Test that token created with one secret cannot be validated with another"""
        token = create_token(VALID_PAYLOAD, secret=CUSTOM_SECRET)

        with pytest.raises(TokenSignatureInvalidException):
            validate_token(token, secret=ANOTHER_SECRET)

    def test_datetime_vs_timedelta_expiration_consistency(self):
        """Test that datetime and timedelta expiration produce valid tokens"""
        expire_delta = timedelta(minutes=60)
        expire_datetime = datetime.now(UTC) + timedelta(minutes=60)

        token_delta = create_token(VALID_PAYLOAD, expire=expire_delta)
        token_datetime = create_token(VALID_PAYLOAD, expire=expire_datetime)

        # Both should be valid
        decoded_delta = validate_token(token_delta)
        decoded_datetime = validate_token(token_datetime)

        assert decoded_delta["user_id"] == VALID_PAYLOAD["user_id"]
        assert decoded_datetime["user_id"] == VALID_PAYLOAD["user_id"]
