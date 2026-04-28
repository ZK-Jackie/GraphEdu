"""Unit tests for utility functions."""

import pytest

from graphedu.common.utils.password import hash_password, verify_password
from graphedu.common.utils.token import decode_token, generate_token


@pytest.mark.unit
class TestPasswordUtils:
    """Tests for password utility functions."""

    def test_hash_password_returns_hash(self):
        """Test that hashing a password returns a hash string."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_hash_password_different_hashes(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct_password(self):
        """Test verifying a correct password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test verifying an incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test verifying an empty password."""
        hashed = hash_password("test_password")

        assert verify_password("", hashed) is False


@pytest.mark.unit
class TestTokenUtils:
    """Tests for token utility functions."""

    def test_generate_token_returns_token(self):
        """Test that generating a token returns a token string."""
        data = {"user_id": "test_user_123"}
        token = generate_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_decode_token_roundtrip(self):
        """Test that encoding and decoding a token preserves the data."""
        data = {"user_id": "test_user_123", "exp": 1234567890}
        token = generate_token(data)
        decoded = decode_token(token)

        assert decoded["user_id"] == data["user_id"]

    def test_decode_invalid_token_raises_error(self):
        """Test that decoding an invalid token raises an error."""
        invalid_token = "invalid.token.string"

        with pytest.raises(Exception):
            decode_token(invalid_token)

    def test_decode_expired_token_raises_error(self):
        """Test that decoding an expired token raises an error."""
        import time

        data = {"user_id": "test_user_123", "exp": int(time.time()) - 3600}
        token = generate_token(data)

        with pytest.raises(Exception):
            decode_token(token)


@pytest.mark.unit
class TestStringUtilities:
    """Tests for string utility functions."""

    def test_sanitize_string_removes_dangerous_chars(self):
        """Test that sanitizing a string removes dangerous characters."""
        from graphedu.common.utils.strings import sanitize_string

        dangerous = "<script>alert('xss')</script>"
        sanitized = sanitize_string(dangerous)

        assert "<script>" not in sanitized
        assert "</script>" not in sanitized

    def test_truncate_string(self):
        """Test truncating a string to a maximum length."""
        from graphedu.common.utils.strings import truncate_string

        long_string = "a" * 100
        truncated = truncate_string(long_string, max_length=50)

        assert len(truncated) == 50
        assert truncated.endswith("...")

    def test_generate_random_string(self):
        """Test generating a random string."""
        from graphedu.common.utils.strings import generate_random_string

        random_str = generate_random_string(16)

        assert len(random_str) == 16
        assert random_str.isalnum()


@pytest.mark.unit
@pytest.mark.slow
class TestPerformanceUtilities:
    """Performance tests for utility functions."""

    def test_hash_password_performance(self, benchmark):
        """Benchmark password hashing performance."""
        password = "test_password_123"

        result = benchmark(hash_password, password)

        assert result is not None

    def test_verify_password_performance(self, benchmark):
        """Benchmark password verification performance."""
        password = "test_password_123"
        hashed = hash_password(password)

        result = benchmark(verify_password, password, hashed)

        assert result is True
