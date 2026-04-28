"""测试配置验证器。"""

import warnings
from unittest.mock import patch

import pytest

from graphedu.common.config.core.validators import validate_header_lowercase


class TestValidateHeaderLowercase:
    """测试 validate_header_lowercase 验证器函数。"""

    def test_lowercase_header(self):
        """测试小写 header（不应产生警告）。"""
        header = "authorization"
        result = validate_header_lowercase(header)
        assert result == "authorization"

    def test_uppercase_header(self):
        """测试大写 header（应产生警告并转换）。"""
        header = "Authorization"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_header_lowercase(header)

            # 验证警告产生
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "Token header must be lowercase" in str(w[0].message)
            assert "Authorization" in str(w[0].message)

            # 验证转换结果
            assert result == "authorization"

    def test_mixed_case_header(self):
        """测试混合大小写 header（应产生警告并转换）。"""
        header = "Auth-Token"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_header_lowercase(header)

            # 验证警告产生
            assert len(w) == 1
            assert "Token header must be lowercase" in str(w[0].message)

            # 验证转换结果
            assert result == "auth-token"

    def test_empty_header(self):
        """测试空 header（不应产生警告）。"""
        header = ""
        result = validate_header_lowercase(header)
        assert result == ""

    def test_none_header(self):
        """测试 None header（不应产生警告）。"""
        header = None
        result = validate_header_lowercase(header)
        assert result is None

    def test_header_with_numbers_and_dashes(self):
        """测试包含数字和连字符的 header。"""
        header = "X-Auth-Token-123"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_header_lowercase(header)

            # 验证警告产生
            assert len(w) == 1

            # 验证转换结果（保留数字和连字符）
            assert result == "x-auth-token-123"

    def test_warning_stacklevel(self):
        """测试警告的堆栈级别。"""
        header = "Authorization"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_header_lowercase(header)

            # 验证堆栈级别正确（应指向调用位置）
            assert len(w) == 1
            assert w[0].filename == __file__
