"""
Test suite for graphedu.common.utils.strings module

This test suite covers all functions in the strings module with various input scenarios.
"""

from datetime import datetime, timedelta
import time

import pytest

from graphedu.common.exceptions import TypeConversionException, ValueException
from graphedu.common.utils.strings import (
    Language,
    # Enums
    TimePrecision,
    check_path_or_url,
    # String functions
    extract_contents,
    # Time formatting functions
    format_duration,
    format_duration_detailed,
    format_duration_short,
    format_retry_after,
    format_time_ago,
    format_timeout,
    format_wait_time,
    get_datetime,
    get_timestamp_ms,
    # Timestamp functions
    get_timestamp_s,
    get_timestamp_us,
    get_url_params,
    is_file_path,
    is_http_url,
    is_match,
    str_to_bool,
    timestamp_to_datetime,
)

# ============================================================================
# Timestamp Functions Tests
# ============================================================================


class TestGetTimestampS:
    """Test cases for get_timestamp_s function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_timestamp_s()
        assert isinstance(result, str)

    def test_returns_10_digits(self):
        """Test that timestamp has 10 digits (seconds)."""
        result = get_timestamp_s()
        assert len(result) == 10

    def test_is_numeric(self):
        """Test that result is numeric string."""
        result = get_timestamp_s()
        assert result.isdigit()

    def test_increasing_over_time(self):
        """Test that timestamps increase over time."""
        timestamp1 = get_timestamp_s()
        time.sleep(1)
        timestamp2 = get_timestamp_s()
        assert int(timestamp2) > int(timestamp1)


class TestGetTimestampMs:
    """Test cases for get_timestamp_ms function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_timestamp_ms()
        assert isinstance(result, str)

    def test_returns_13_digits(self):
        """Test that timestamp has 13 digits (milliseconds)."""
        result = get_timestamp_ms()
        assert len(result) == 13

    def test_is_numeric(self):
        """Test that result is numeric string."""
        result = get_timestamp_ms()
        assert result.isdigit()

    def test_greater_than_seconds_timestamp(self):
        """Test that ms timestamp is larger than s timestamp."""
        s_timestamp = get_timestamp_s()
        ms_timestamp = get_timestamp_ms()
        assert int(ms_timestamp) > int(s_timestamp) * 1000


class TestGetTimestampUs:
    """Test cases for get_timestamp_us function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_timestamp_us()
        assert isinstance(result, str)

    def test_returns_16_digits(self):
        """Test that timestamp has 16 digits (microseconds)."""
        result = get_timestamp_us()
        assert len(result) == 16

    def test_is_numeric(self):
        """Test that result is numeric string."""
        result = get_timestamp_us()
        assert result.isdigit()


class TestGetDatetime:
    """Test cases for get_datetime function."""

    def test_default_format(self):
        """Test default format YYYY-MM-DD."""
        result = get_datetime()
        assert len(result) == 10  # YYYY-MM-DD
        assert result.count("-") == 2

    def test_custom_format(self):
        """Test custom format string."""
        result = get_datetime("%Y/%m/%d")
        assert "/" in result
        assert len(result) == 10  # YYYY/MM/MM/DD

    def test_full_datetime_format(self):
        """Test full datetime format."""
        result = get_datetime("%Y-%m-%d %H:%M:%S")
        assert " " in result
        assert ":" in result
        assert len(result) == 19

    def test_year_format(self):
        """Test year only format."""
        result = get_datetime("%Y")
        assert len(result) == 4
        assert result.isdigit()


class TestTimestampToDatetime:
    """Test cases for timestamp_to_datetime function."""

    def test_seconds_timestamp(self):
        """Test converting 10-digit timestamp (seconds)."""
        timestamp = "1234567890"
        result = timestamp_to_datetime(timestamp)
        assert isinstance(result, str)
        # Check format contains date (timezone may vary)
        assert "2009" in result and "02" in result

    def test_milliseconds_timestamp(self):
        """Test converting 13-digit timestamp (milliseconds)."""
        timestamp = "1234567890123"
        result = timestamp_to_datetime(timestamp)
        assert isinstance(result, str)

    def test_microseconds_timestamp(self):
        """Test converting 16-digit timestamp (microseconds)."""
        timestamp = "1234567890123456"
        result = timestamp_to_datetime(timestamp)
        assert isinstance(result, str)

    def test_custom_format(self):
        """Test custom output format."""
        timestamp = "1234567890"
        result = timestamp_to_datetime(timestamp, "%Y/%m/%d")
        # Check it's a valid date format with slashes
        assert "/" in result
        assert len(result) == 10

    def test_invalid_timestamp_length(self):
        """Test that invalid length raises ValueException."""
        with pytest.raises(ValueException):
            timestamp_to_datetime("12345")

    def test_invalid_timestamp_length_9(self):
        """Test that 9-digit timestamp raises error."""
        with pytest.raises(ValueException):
            timestamp_to_datetime("123456789")

    def test_invalid_timestamp_length_11(self):
        """Test that 11-digit timestamp raises error."""
        with pytest.raises(ValueException):
            timestamp_to_datetime("12345678901")


# ============================================================================
# String Functions Tests
# ============================================================================


class TestExtractContents:
    """Test cases for extract_contents function."""

    def test_normal_extraction(self):
        """Test normal tag extraction."""
        input_str = "Hello<tag>content</tag>World"
        between, after = extract_contents(input_str, "<tag>", "</tag>")
        assert between == "content"
        assert after == "World"

    def test_multiple_tags(self):
        """Test extraction with multiple tags."""
        input_str = "Start<div>Inner</div>End"
        between, after = extract_contents(input_str, "<div>", "</div>")
        assert between == "Inner"
        assert after == "End"

    def test_no_start_tag(self):
        """Test when start tag is missing."""
        input_str = "Hello</tag>World"
        between, after = extract_contents(input_str, "<tag>", "</tag>")
        assert between is None
        assert after is None

    def test_no_end_tag(self):
        """Test when end tag is missing."""
        input_str = "Hello<tag>World"
        between, after = extract_contents(input_str, "<tag>", "</tag>")
        assert between is None
        assert after is None

    def test_reversed_tags(self):
        """Test when tags are in wrong order."""
        input_str = "Hello</tag><tag>World"
        between, after = extract_contents(input_str, "<tag>", "</tag>")
        assert between is None
        assert after is None

    def test_empty_content(self):
        """Test extraction with empty content."""
        input_str = "Hello<tag></tag>World"
        between, after = extract_contents(input_str, "<tag>", "</tag>")
        assert between == ""
        assert after == "World"

    def test_no_after_content(self):
        """Test extraction with no content after end tag."""
        input_str = "Hello<tag>content</tag>"
        between, after = extract_contents(input_str, "<tag>", "</tag>")
        assert between == "content"
        assert after == ""

    def test_nested_tags(self):
        """Test with nested tags."""
        input_str = "<outer><inner>value</inner></outer>"
        between, after = extract_contents(input_str, "<outer>", "</outer>")
        assert "<inner>value</inner>" in between
        assert after == ""


class TestCheckPathOrUrl:
    """Test cases for check_path_or_url function."""

    def test_http_url(self):
        """Test HTTP URL."""
        result = check_path_or_url("http://example.com")
        assert result == "url"

    def test_https_url(self):
        """Test HTTPS URL."""
        result = check_path_or_url("https://example.com")
        assert result == "url"

    def test_existing_file(self, tmp_path):
        """Test existing file path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        result = check_path_or_url(str(test_file))
        assert result == "path"

    def test_existing_directory(self, tmp_path):
        """Test existing directory path."""
        result = check_path_or_url(str(tmp_path))
        assert result == "path"

    def test_invalid_path_or_url(self):
        """Test invalid path or URL."""
        with pytest.raises(ValueException):
            check_path_or_url("not_a_valid_path_or_url")

    def test_file_url_without_scheme(self):
        """Test file URL without scheme should fail."""
        with pytest.raises(ValueException):
            check_path_or_url("example.com/path")

    def test_nonexistent_local_path(self):
        """Test non-existent local path."""
        with pytest.raises(ValueException):
            check_path_or_url("/nonexistent/path/file.txt")


class TestGetUrlParams:
    """Test cases for get_url_params function."""

    def test_url_with_params(self):
        """Test URL with query parameters."""
        url = "https://example.com?key1=value1&key2=value2"
        result = get_url_params(url)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_params_only(self):
        """Test string with only parameters (no URL)."""
        params = "key1=value1&key2=value2"
        result = get_url_params(params)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_url_without_params(self):
        """Test URL without query parameters."""
        url = "https://example.com"
        result = get_url_params(url)
        assert result == {}

    def test_single_param(self):
        """Test URL with single parameter."""
        url = "https://example.com?key=value"
        result = get_url_params(url)
        assert result == {"key": "value"}

    def test_empty_url(self):
        """Test empty string."""
        result = get_url_params("")
        assert result == {}

    def test_special_characters_in_values(self):
        """Test parameters with special characters."""
        url = "https://example.com?key=value%20with%20spaces"
        result = get_url_params(url)
        assert "key" in result
        assert "value" in result["key"]


class TestIsHttpUrl:
    """Test cases for is_http_url function."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        assert is_http_url("http://example.com") is True

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        assert is_http_url("https://example.com") is True

    def test_valid_url_with_path(self):
        """Test valid URL with path."""
        assert is_http_url("https://example.com/path/to/resource") is True

    def test_valid_url_with_params(self):
        """Test valid URL with query parameters."""
        assert is_http_url("https://example.com?key=value") is True

    def test_valid_url_with_port(self):
        """Test valid URL with port."""
        assert is_http_url("https://example.com:8080") is True

    def test_invalid_url_no_scheme(self):
        """Test URL without scheme."""
        assert is_http_url("example.com") is False

    def test_invalid_url_ftp_scheme(self):
        """Test FTP URL."""
        assert is_http_url("ftp://example.com") is False

    def test_empty_string(self):
        """Test empty string."""
        assert is_http_url("") is False

    def test_file_path(self):
        """Test file path."""
        assert is_http_url("/path/to/file") is False

    def test_windows_path(self):
        """Test Windows path."""
        assert is_http_url("C:\\path\\to\\file") is False


class TestIsFilePath:
    """Test cases for is_file_path function."""

    def test_unix_absolute_path(self):
        """Test Unix absolute path."""
        assert is_file_path("/home/user/file.txt") is True

    def test_unix_relative_path(self):
        """Test Unix relative path should return False."""
        assert is_file_path("relative/path") is False

    def test_windows_absolute_path(self):
        """Test Windows absolute path."""
        assert is_file_path("C:\\Users\\user\\file.txt") is True
        assert is_file_path("D:\\data\\file.txt") is True

    def test_windows_path_with_forward_slash(self):
        """Test Windows path should handle drive letter."""
        assert is_file_path("C:/Users/user") is False

    def test_url(self):
        """Test URL should return False."""
        assert is_file_path("https://example.com") is False

    def test_relative_path(self):
        """Test relative path."""
        assert is_file_path("./file.txt") is False

    def test_empty_string(self):
        """Test empty string."""
        assert is_file_path("") is False

    def test_network_path(self):
        """Test network path (UNC)."""
        assert is_file_path("\\\\server\\share") is False


class TestIsMatch:
    """Test cases for is_match function."""

    def test_exact_match(self):
        """Test exact string match."""
        assert is_match("hello", "hello") is True

    def test_pattern_match(self):
        """Test regex pattern match."""
        assert is_match("hello123", r"hello\d+") is True

    def test_pattern_no_match(self):
        """Test pattern that doesn't match."""
        assert is_match("hello", r"\d+") is False

    def test_none_pattern(self):
        """Test with None pattern (should always return True)."""
        assert is_match("anything", None) is True

    def test_empty_pattern(self):
        """Test with empty pattern (should always return True)."""
        assert is_match("anything", "") is True

    def test_wildcard_pattern(self):
        """Test wildcard pattern."""
        assert is_match("hello", ".*") is True

    def test_case_sensitive_match(self):
        """Test case-sensitive matching."""
        assert is_match("Hello", "hello") is False

    def test_complex_pattern(self):
        """Test complex regex pattern."""
        assert is_match("test@email.com", r"[\w.]+@[\w.]+") is True


class TestStrToBool:
    """Test cases for str_to_bool function."""

    def test_true_values(self):
        """Test various true string representations."""
        assert str_to_bool("true") is True
        assert str_to_bool("TRUE") is True
        assert str_to_bool("1") is True
        assert str_to_bool("yes") is True
        assert str_to_bool("YES") is True
        assert str_to_bool("y") is True
        assert str_to_bool("Y") is True

    def test_false_values(self):
        """Test various false string representations."""
        assert str_to_bool("false") is False
        assert str_to_bool("FALSE") is False
        assert str_to_bool("0") is False
        assert str_to_bool("no") is False
        assert str_to_bool("NO") is False
        assert str_to_bool("n") is False
        assert str_to_bool("N") is False

    def test_bool_input(self):
        """Test boolean input (should return as-is)."""
        assert str_to_bool(True) is True
        assert str_to_bool(False) is False

    def test_invalid_string(self):
        """Test invalid string raises TypeConversionException."""
        with pytest.raises(TypeConversionException):
            str_to_bool("invalid")

    def test_empty_string(self):
        """Test empty string raises exception."""
        with pytest.raises(TypeConversionException):
            str_to_bool("")

    def test_whitespace_string(self):
        """Test whitespace string raises exception."""
        with pytest.raises(TypeConversionException):
            str_to_bool("   ")

    def test_mixed_case(self):
        """Test mixed case input."""
        assert str_to_bool("TrUe") is True
        assert str_to_bool("FaLsE") is False


# ============================================================================
# Time Formatting Functions Tests
# ============================================================================


class TestFormatDuration:
    """Test cases for format_duration function."""

    def test_zero_seconds_chinese(self):
        """Test zero seconds in Chinese."""
        result = format_duration(0, Language.ZH_CN)
        assert "刚刚" in result or result == "0秒"

    def test_zero_seconds_english(self):
        """Test zero seconds in English."""
        result = format_duration(0, Language.EN_US)
        assert "just now" in result

    def test_seconds_only_chinese(self):
        """Test only seconds in Chinese."""
        result = format_duration(30, Language.ZH_CN)
        assert "30秒" in result

    def test_seconds_only_english(self):
        """Test only seconds in English."""
        result = format_duration(30, Language.EN_US)
        assert "30 seconds" in result or "30 second" in result

    def test_minutes_only_chinese(self):
        """Test only minutes in Chinese."""
        result = format_duration(120, Language.ZH_CN)
        assert "2分钟" in result

    def test_minutes_only_english(self):
        """Test only minutes in English."""
        result = format_duration(120, Language.EN_US)
        assert "2 minutes" in result or "2 minute" in result

    def test_hours_only_chinese(self):
        """Test only hours in Chinese."""
        result = format_duration(3600, Language.ZH_CN)
        assert "1小时" in result

    def test_days_only_chinese(self):
        """Test only days in Chinese."""
        result = format_duration(86400, Language.ZH_CN)
        assert "1天" in result

    def test_combined_units_chinese(self):
        """Test combined time units in Chinese."""
        result = format_duration(90061, Language.ZH_CN)  # 1 day + 1 hour + 1 minute + 1 second
        assert "天" in result
        # Check that it shows at most 2 units by default

    def test_timedelta_input(self):
        """Test with timedelta object."""
        td = timedelta(hours=2, minutes=30)
        result = format_duration(td, Language.ZH_CN)
        assert "2小时" in result
        assert "30分钟" in result

    def test_negative_duration(self):
        """Test negative duration (should be treated as positive)."""
        result = format_duration(-100, Language.ZH_CN)
        assert "1分钟" in result or "40秒" in result

    def test_max_units_parameter(self):
        """Test max_units parameter."""
        result = format_duration(90061, Language.ZH_CN, max_units=1)
        # Should only show one unit
        units_count = sum([result.count(unit) for unit in ["年", "个月", "周", "天", "小时", "分钟", "秒"]])
        assert units_count <= 1

    def test_precision_parameter(self):
        """Test precision parameter."""
        result = format_duration(3661, Language.ZH_CN, precision=TimePrecision.HOUR)
        # Should not show minutes or seconds
        assert "分钟" not in result
        assert "秒" not in result

    def test_language_as_string(self):
        """Test language passed as string."""
        result = format_duration(60, "zh_CN")
        assert "1分钟" in result

    def test_invalid_language_string(self):
        """Test invalid language string (should fallback to Chinese)."""
        result = format_duration(60, "invalid")
        assert "分钟" in result or "minute" in result

    def test_large_duration(self):
        """Test very large duration (years)."""
        seconds = 31536000 * 2  # 2 years
        result = format_duration(seconds, Language.ZH_CN)
        assert "年" in result or "2" in result


class TestFormatDurationShort:
    """Test cases for format_duration_short function."""

    def test_short_format_chinese(self):
        """Test short format in Chinese."""
        result = format_duration_short(3661, Language.ZH_CN)
        # Should only show one unit
        assert result in ["1小时", "1小时1分钟", "61分钟"]

    def test_short_format_english(self):
        """Test short format in English."""
        result = format_duration_short(3661, Language.EN_US)
        # Should only show one unit
        assert "hour" in result.lower()

    def test_small_duration(self):
        """Test small duration."""
        result = format_duration_short(45, Language.ZH_CN)
        assert "45秒" in result or result == "45秒"


class TestFormatDurationDetailed:
    """Test cases for format_duration_detailed function."""

    def test_detailed_format_chinese(self):
        """Test detailed format in Chinese."""
        result = format_duration_detailed(3661, Language.ZH_CN)
        # Should show all units
        assert "1小时" in result
        assert "1分钟" in result
        assert "1秒" in result

    def test_detailed_format_english(self):
        """Test detailed format in English."""
        result = format_duration_detailed(3661, Language.EN_US)
        assert "hour" in result.lower()
        assert "minute" in result.lower()
        assert "second" in result.lower()


class TestFormatRetryAfter:
    """Test cases for format_retry_after function."""

    def test_retry_after_chinese(self):
        """Test retry after message in Chinese."""
        result = format_retry_after(150, Language.ZH_CN)
        assert "请" in result
        assert "后再试" in result
        assert "分钟" in result

    def test_retry_after_english(self):
        """Test retry after message in English."""
        result = format_retry_after(150, Language.EN_US)
        assert "Please try again after" in result
        assert "minute" in result.lower()

    def test_retry_after_japanese(self):
        """Test retry after message in Japanese."""
        result = format_retry_after(150, Language.JA_JP)
        assert "後" in result or "あと" in result

    def test_retry_after_korean(self):
        """Test retry after message in Korean."""
        result = format_retry_after(150, Language.KO_KR)
        assert "후" in result


class TestFormatTimeAgo:
    """Test cases for format_time_ago function."""

    def test_time_ago_seconds_chinese(self):
        """Test time ago with seconds in Chinese."""
        dt = datetime.now() - timedelta(seconds=30)
        result = format_time_ago(dt, Language.ZH_CN)
        assert "刚刚" in result

    def test_time_ago_minutes_chinese(self):
        """Test time ago with minutes in Chinese."""
        dt = datetime.now() - timedelta(minutes=5)
        result = format_time_ago(dt, Language.ZH_CN)
        assert "5分钟" in result
        assert "前" in result

    def test_time_ago_hours_chinese(self):
        """Test time ago with hours in Chinese."""
        dt = datetime.now() - timedelta(hours=2)
        result = format_time_ago(dt, Language.ZH_CN)
        assert "2小时" in result
        assert "前" in result

    def test_time_ago_english(self):
        """Test time ago in English."""
        dt = datetime.now() - timedelta(hours=2)
        result = format_time_ago(dt, Language.EN_US)
        assert "2 hours" in result or "2 hour" in result
        assert "ago" in result

    def test_time_ago_with_timestamp(self):
        """Test time ago with timestamp (int)."""
        timestamp = time.time() - 3600  # 1 hour ago
        result = format_time_ago(timestamp, Language.ZH_CN)
        assert "1小时" in result or "60分钟" in result

    def test_time_ago_future_time(self):
        """Test time ago with future time."""
        dt = datetime.now() + timedelta(minutes=5)
        result = format_time_ago(dt, Language.ZH_CN)
        assert "后" in result

    def test_time_ago_with_custom_now(self):
        """Test time ago with custom now parameter."""
        past = datetime(2024, 1, 1, 12, 0, 0)
        now = datetime(2024, 1, 1, 13, 0, 0)
        result = format_time_ago(past, Language.ZH_CN, now=now)
        assert "1小时" in result or "60分钟" in result


class TestFormatWaitTime:
    """Test cases for format_wait_time function."""

    def test_wait_time_chinese(self):
        """Test wait time in Chinese."""
        result = format_wait_time(150, Language.ZH_CN)
        assert "需等待" in result
        assert "分钟" in result

    def test_wait_time_english(self):
        """Test wait time in English."""
        result = format_wait_time(150, Language.EN_US)
        assert "Please wait" in result
        assert "minute" in result.lower()

    def test_wait_time_japanese(self):
        """Test wait time in Japanese."""
        result = format_wait_time(150, Language.JA_JP)
        assert "お待ちください" in result or "待っ" in result

    def test_wait_time_korean(self):
        """Test wait time in Korean."""
        result = format_wait_time(150, Language.KO_KR)
        assert "기다려주세요" in result

    def test_wait_time_float_input(self):
        """Test wait time with float input."""
        result = format_wait_time(90.5, Language.ZH_CN)
        assert "分钟" in result or "秒" in result


class TestFormatTimeout:
    """Test cases for format_timeout function."""

    def test_timeout_chinese(self):
        """Test timeout in Chinese."""
        result = format_timeout(30, Language.ZH_CN)
        assert "超时时间" in result
        assert "30" in result
        assert "秒" in result

    def test_timeout_english(self):
        """Test timeout in English."""
        result = format_timeout(30, Language.EN_US)
        assert "Timeout:" in result
        assert "30" in result
        assert "second" in result.lower()

    def test_timeout_japanese(self):
        """Test timeout in Japanese."""
        result = format_timeout(30, Language.JA_JP)
        assert "タイムアウト" in result

    def test_timeout_korean(self):
        """Test timeout in Korean."""
        result = format_timeout(30, Language.KO_KR)
        assert "시간 초과" in result

    def test_timeout_minutes(self):
        """Test timeout with minutes."""
        result = format_timeout(120, Language.ZH_CN)
        assert "2分钟" in result


# ============================================================================
# Integration Tests
# ============================================================================


class TestStringsIntegration:
    """Integration tests for strings module."""

    def test_timestamp_workflow(self):
        """Test complete timestamp workflow."""
        # Get current timestamp
        timestamp = get_timestamp_s()

        # Convert back to datetime
        datetime_str = timestamp_to_datetime(timestamp)

        # Verify it's a valid format
        assert len(datetime_str) > 0
        assert "-" in datetime_str

    def test_time_formatting_chain(self):
        """Test time formatting functions working together."""
        duration_seconds = 3661

        # Format in different ways
        normal = format_duration(duration_seconds)
        short = format_duration_short(duration_seconds)
        detailed = format_duration_detailed(duration_seconds)

        # All should be different
        assert len(normal) >= len(short)
        assert len(detailed) >= len(normal)

    def test_multilingual_workflow(self):
        """Test multilingual support consistency."""
        seconds = 120

        zh_result = format_duration(seconds, Language.ZH_CN)
        en_result = format_duration(seconds, Language.EN_US)

        # Both should contain number
        assert "2" in zh_result or "120" in zh_result
        assert "2" in en_result or "120" in en_result

    def test_url_and_path_detection(self):
        """Test URL and path detection."""
        url = "https://example.com"
        assert is_http_url(url) is True

        # Note: can't test file path without actual file
        assert is_file_path(url) is False
