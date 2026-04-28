"""
Test suite for graphedu.common.utils.password module

This test suite covers all functions in the PasswordUtil class with various input scenarios.
"""
import pytest

from graphedu.common.exceptions import PasswordException
from graphedu.common.utils.password import PasswordUtil


class TestHashPassword:
    """Test cases for PasswordUtil.hash_password method."""

    def test_hash_password_with_valid_password(self):
        """Test hashing a valid password."""
        password = "MySecurePassword123!"
        hashed = PasswordUtil.hash_password(password)

        # Should return a string
        assert isinstance(hashed, str)
        # Should start with bcrypt prefix
        assert hashed.startswith("$2b$")
        # Should be different each time due to random salt
        hashed2 = PasswordUtil.hash_password(password)
        assert hashed != hashed2

    def test_hash_password_with_minimum_length(self):
        """Test hashing a password with exactly 6 characters."""
        password = "123456"
        hashed = PasswordUtil.hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_strong_password(self):
        """Test hashing a strong password."""
        password = "StrongP@ssw0rd!2024"
        hashed = PasswordUtil.hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_password_with_special_characters(self):
        """Test hashing a password with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = PasswordUtil.hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_unicode_characters(self):
        """Test hashing a password with unicode characters."""
        password = "密码123!中文"
        hashed = PasswordUtil.hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_empty_string_raises_error(self):
        """Test that empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            PasswordUtil.hash_password("")

    def test_hash_password_with_weak_password_logs_warning(self, caplog):
        """Test that weak password logs warning but still works."""
        import logging
        password = "12345"  # Less than 6 characters
        with caplog.at_level(logging.WARNING):
            hashed = PasswordUtil.hash_password(password)
        assert isinstance(hashed, str)
        assert "Password is too weak" in caplog.text

    def test_hash_password_with_very_long_password(self):
        """Test hashing a very long password exceeds bcrypt limit."""
        password = "a" * 1000
        # bcrypt has a 72-byte limit, should raise PasswordException
        with pytest.raises(PasswordException):
            PasswordUtil.hash_password(password)

    def test_hash_password_consistency_with_same_password_and_salt(self):
        """Test that same password with verification works correctly."""
        password = "TestPassword123!"
        hashed = PasswordUtil.hash_password(password)
        # Even though hashes differ, verification should work
        assert PasswordUtil.verify_password(password, hashed)


class TestVerifyPassword:
    """Test cases for PasswordUtil.verify_password method."""

    def test_verify_password_with_correct_password(self):
        """Test verifying a correct password."""
        password = "CorrectPassword123!"
        hashed = PasswordUtil.hash_password(password)
        assert PasswordUtil.verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test verifying an incorrect password."""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = PasswordUtil.hash_password(password)
        assert PasswordUtil.verify_password(wrong_password, hashed) is False

    def test_verify_password_with_none_values(self):
        """Test verifying with None values returns False."""
        assert PasswordUtil.verify_password(None, "somehash") is False
        assert PasswordUtil.verify_password("password", None) is False
        assert PasswordUtil.verify_password(None, None) is False

    def test_verify_password_with_empty_strings(self):
        """Test verifying with empty strings returns False."""
        assert PasswordUtil.verify_password("", "somehash") is False
        assert PasswordUtil.verify_password("password", "") is False
        assert PasswordUtil.verify_password("", "") is False

    def test_verify_password_with_invalid_hash_format(self):
        """Test that invalid hash format raises PasswordException."""
        with pytest.raises(PasswordException, match="Invalid hashed password format"):
            PasswordUtil.verify_password("password", "invalid_hash")

    def test_verify_password_with_non_string_types_raises_error(self):
        """Test that non-string types raise PasswordException."""
        hashed = PasswordUtil.hash_password("password123")

        with pytest.raises(PasswordException, match="Invalid parameter type"):
            PasswordUtil.verify_password(123, hashed)

        with pytest.raises(PasswordException, match="Invalid parameter type"):
            PasswordUtil.verify_password("password", 123)

        with pytest.raises(PasswordException, match="Invalid parameter type"):
            PasswordUtil.verify_password(["password"], hashed)

    def test_verify_password_case_sensitivity(self):
        """Test that password verification is case-sensitive."""
        password = "Password123!"
        hashed = PasswordUtil.hash_password(password)
        assert PasswordUtil.verify_password(password, hashed) is True
        assert PasswordUtil.verify_password(password.lower(), hashed) is False
        assert PasswordUtil.verify_password(password.upper(), hashed) is False

    def test_verify_password_with_unicode(self):
        """Test verifying password with unicode characters."""
        password = "密码123!中文"
        hashed = PasswordUtil.hash_password(password)
        assert PasswordUtil.verify_password(password, hashed) is True
        assert PasswordUtil.verify_password("密码123", hashed) is False

    def test_verify_password_with_whitespace_sensitivity(self):
        """Test that password verification is whitespace-sensitive."""
        password = "Password123!"
        password_with_space = "Password123! "
        hashed = PasswordUtil.hash_password(password)
        assert PasswordUtil.verify_password(password, hashed) is True
        assert PasswordUtil.verify_password(password_with_space, hashed) is False

    def test_verify_password_with_multiple_hashes_of_same_password(self):
        """Test verification works with different hashes of same password."""
        password = "TestPassword123!"
        hash1 = PasswordUtil.hash_password(password)
        hash2 = PasswordUtil.hash_password(password)
        # Hashes should be different
        assert hash1 != hash2
        # But both should verify correctly
        assert PasswordUtil.verify_password(password, hash1) is True
        assert PasswordUtil.verify_password(password, hash2) is True


class TestCheckPasswordStrength:
    """Test cases for PasswordUtil.check_password_strength method."""

    def test_check_strength_perfect_password(self):
        """Test password with all requirements met."""
        password = "StrongP@ssw0rd"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is True
        assert result['score'] == 5  # Length + lower + upper + digit + special
        assert len(result['issues']) == 0

    def test_check_strength_too_short(self):
        """Test password that's too short."""
        password = "Ab1@"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 4  # Upper + lower + digit + special (no length)
        assert "密码长度至少8个字符" in result['issues']

    def test_check_strength_exactly_8_chars(self):
        """Test password with exactly 8 characters."""
        password = "Abcdef1@"
        result = PasswordUtil.check_password_strength(password)
        assert result['score'] >= 1  # Should get point for length

    def test_check_strength_no_lowercase(self):
        """Test password without lowercase letters."""
        password = "ABCDEFGH1@"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 4  # Length + upper + digit + special (no lower)
        assert "密码应包含小写字母" in result['issues']

    def test_check_strength_no_uppercase(self):
        """Test password without uppercase letters."""
        password = "abcdefgh1@"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 4  # Length + lower + digit + special (no upper)
        assert "密码应包含大写字母" in result['issues']

    def test_check_strength_no_digits(self):
        """Test password without digits."""
        password = "Abcdefgh@"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 4  # Length + lower + upper + special (no digit)
        assert "密码应包含数字" in result['issues']

    def test_check_strength_no_special_characters(self):
        """Test password without special characters."""
        password = "Abcdefgh1"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 4  # Length + lower + upper + digit (no special)
        assert "密码应包含特殊字符" in result['issues']

    def test_check_strength_all_lowercase(self):
        """Test password with only lowercase letters."""
        password = "abcdefgh"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 2  # Length + lowercase (no upper, no digit, no special)
        assert len(result['issues']) == 3  # Upper, digit, special

    def test_check_strength_empty_password(self):
        """Test empty password strength."""
        password = ""
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 0
        assert "密码长度至少8个字符" in result['issues']
        assert "密码应包含大写字母" in result['issues']
        assert "密码应包含数字" in result['issues']
        assert "密码应包含特殊字符" in result['issues']

    def test_check_strength_score_1(self):
        """Test password with score of 2."""
        password = "abcdefgh"  # Only has lowercase
        result = PasswordUtil.check_password_strength(password)
        assert result['score'] == 2  # Length + lowercase
        # Actually: has lower (yes), length >= 8 (yes), no upper, no digit, no special

    def test_check_strength_all_special_characters(self):
        """Test password with only special characters."""
        password = "!@#$%^&*"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is False
        assert result['score'] == 2  # Length + special (no lower, no upper, no digit)

    def test_check_strength_common_patterns_weak(self):
        """Test that common weak patterns are detected."""
        password = "Password1"
        result = PasswordUtil.check_password_strength(password)
        # Has upper, lower, digit, length=8, no special
        assert result['score'] == 4  # Length + lower + upper + digit (no special)
        assert result['is_strong'] is False

    def test_check_strength_very_strong_password(self):
        """Test a very strong password."""
        password = "MyV3ryStr0ng!Pass@2024"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is True
        assert result['score'] == 5  # Length + lower + upper + digit + special

    def test_check_strength_with_extended_special_chars(self):
        """Test with various special characters."""
        password = "Password1!@#$"
        result = PasswordUtil.check_password_strength(password)
        assert result['is_strong'] is True
        assert result['score'] == 5  # Length + lower + upper + digit + special

    def test_check_strength_return_structure(self):
        """Test that return value has correct structure."""
        password = "Test123@"
        result = PasswordUtil.check_password_strength(password)
        assert isinstance(result, dict)
        assert 'is_strong' in result
        assert 'score' in result
        assert 'issues' in result
        assert isinstance(result['is_strong'], bool)
        assert isinstance(result['score'], int)
        assert isinstance(result['issues'], list)
        assert all(isinstance(issue, str) for issue in result['issues'])


class TestGenerateRandomPassword:
    """Test cases for PasswordUtil.generate_random_password method."""

    def test_generate_password_default_length(self):
        """Test generating password with default length."""
        password = PasswordUtil.generate_random_password()
        assert len(password) == 12
        assert isinstance(password, str)

    def test_generate_password_custom_length(self):
        """Test generating password with custom length."""
        for length in [8, 12, 16, 20, 24]:
            password = PasswordUtil.generate_random_password(length)
            assert len(password) == length

    def test_generate_password_minimum_length(self):
        """Test generating password with minimum allowed length."""
        password = PasswordUtil.generate_random_password(8)
        assert len(password) == 8

    def test_generate_password_too_short_raises_error(self):
        """Test that length less than 8 raises ValueError."""
        with pytest.raises(ValueError, match="Password length must be at least 8"):
            PasswordUtil.generate_random_password(7)
        with pytest.raises(ValueError, match="Password length must be at least 8"):
            PasswordUtil.generate_random_password(1)
        with pytest.raises(ValueError, match="Password length must be at least 8"):
            PasswordUtil.generate_random_password(0)

    def test_generate_password_contains_lowercase(self):
        """Test that generated password contains lowercase letters."""
        password = PasswordUtil.generate_random_password(12)
        assert any(c.islower() for c in password)

    def test_generate_password_contains_uppercase(self):
        """Test that generated password contains uppercase letters."""
        password = PasswordUtil.generate_random_password(12)
        assert any(c.isupper() for c in password)

    def test_generate_password_contains_digits(self):
        """Test that generated password contains digits."""
        password = PasswordUtil.generate_random_password(12)
        assert any(c.isdigit() for c in password)

    def test_generate_password_contains_special_chars(self):
        """Test that generated password contains special characters."""
        password = PasswordUtil.generate_random_password(12)
        assert any(c in "!@#$%^&*" for c in password)

    def test_generate_password_uniqueness(self):
        """Test that generated passwords are unique."""
        passwords = [PasswordUtil.generate_random_password(12) for _ in range(100)]
        assert len(set(passwords)) == 100  # All should be different

    def test_generate_password_all_requirements_met(self):
        """Test that generated password meets all requirements."""
        password = PasswordUtil.generate_random_password(12)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*" for c in password)

        assert has_lower and has_upper and has_digit and has_special

    def test_generate_password_strong(self):
        """Test that generated password is considered strong."""
        password = PasswordUtil.generate_random_password(12)
        strength = PasswordUtil.check_password_strength(password)
        assert strength['is_strong'] is True
        assert strength['score'] == 5  # Should have all requirements

    def test_generate_password_large_length(self):
        """Test generating a very long password."""
        password = PasswordUtil.generate_random_password(100)
        assert len(password) == 100
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*" for c in password)

    def test_generate_password_characters_from_valid_set(self):
        """Test that generated password only contains valid characters."""
        password = PasswordUtil.generate_random_password(12)
        valid_chars = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "!@#$%^&*"
        )
        assert all(c in valid_chars for c in password)

    def test_generate_password_multiple_calls_all_valid(self):
        """Test that multiple generated passwords are all valid."""
        for _ in range(50):
            password = PasswordUtil.generate_random_password(12)
            strength = PasswordUtil.check_password_strength(password)
            assert strength['is_strong'] is True
            assert len(password) == 12


class TestPasswordIntegration:
    """Integration tests for password utility functions."""

    def test_hash_and_verify_workflow(self):
        """Test complete hash and verify workflow."""
        # Original password
        password = "SecurePassword123!"

        # Hash it
        hashed = PasswordUtil.hash_password(password)
        assert hashed != password

        # Verify correct password
        assert PasswordUtil.verify_password(password, hashed) is True

        # Verify incorrect password
        assert PasswordUtil.verify_password("WrongPassword", hashed) is False

    def test_generate_and_verify_workflow(self):
        """Test generate and verify workflow."""
        # Generate password
        password = PasswordUtil.generate_random_password(16)

        # Check strength
        strength = PasswordUtil.check_password_strength(password)
        assert strength['is_strong'] is True

        # Hash it
        hashed = PasswordUtil.hash_password(password)

        # Verify it
        assert PasswordUtil.verify_password(password, hashed) is True

    def test_generate_hash_verify_multiple_times(self):
        """Test multiple password generations and verifications."""
        for _ in range(20):
            password = PasswordUtil.generate_random_password(12)
            hashed = PasswordUtil.hash_password(password)
            assert PasswordUtil.verify_password(password, hashed) is True

    def test_weak_password_hashing_still_works(self):
        """Test that weak passwords can still be hashed and verified."""
        weak_passwords = ["123456", "password", "abcdef"]
        for password in weak_passwords:
            hashed = PasswordUtil.hash_password(password)
            assert PasswordUtil.verify_password(password, hashed) is True

    def test_password_strength_after_generation(self):
        """Test that generated passwords pass strength check."""
        for length in [8, 12, 16, 20]:
            password = PasswordUtil.generate_random_password(length)
            strength = PasswordUtil.check_password_strength(password)
            assert strength['is_strong'] is True
            assert len(strength['issues']) == 0
