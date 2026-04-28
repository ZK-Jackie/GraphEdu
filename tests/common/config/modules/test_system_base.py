"""测试系统级配置。"""

import pytest

from graphedu.common.config.modules.system import SystemConfig


class TestSystemConfig:
    """测试 SystemConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = SystemConfig()

        assert config.timezone == "UTC"
        assert config.location_query is True

    def test_custom_timezone_utc(self):
        """测试自定义时区（UTC）。"""
        config = SystemConfig(timezone="UTC")

        assert config.timezone == "UTC"

    def test_custom_timezone_shanghai(self):
        """测试自定义时区（上海）。"""
        config = SystemConfig(timezone="Asia/Shanghai")

        assert config.timezone == "Asia/Shanghai"

    def test_custom_timezone_new_york(self):
        """测试自定义时区（纽约）。"""
        config = SystemConfig(timezone="America/New_York")

        assert config.timezone == "America/New_York"

    def test_custom_timezone_london(self):
        """测试自定义时区（伦敦）。"""
        config = SystemConfig(timezone="Europe/London")

        assert config.timezone == "Europe/London"

    def test_custom_timezone_tokyo(self):
        """测试自定义时区（东京）。"""
        config = SystemConfig(timezone="Asia/Tokyo")

        assert config.timezone == "Asia/Tokyo"

    def test_custom_timezone_sydney(self):
        """测试自定义时区（悉尼）。"""
        config = SystemConfig(timezone="Australia/Sydney")

        assert config.timezone == "Australia/Sydney"

    def test_timezone_with_offset(self):
        """测试带偏移的时区。"""
        config = SystemConfig(timezone="Etc/GMT+8")

        assert config.timezone == "Etc/GMT+8"

    def test_location_query_enabled(self):
        """测试启用 IP 地址位置查询。"""
        config = SystemConfig(location_query=True)

        assert config.location_query is True

    def test_location_query_disabled(self):
        """测试禁用 IP 地址位置查询。"""
        config = SystemConfig(location_query=False)

        assert config.location_query is False

    def test_common_timezones(self):
        """测试常见时区。"""
        common_timezones = [
            "UTC",
            "Asia/Shanghai",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "America/Los_Angeles",
            "Europe/Paris",
            "Asia/Dubai",
            "Pacific/Auckland"
        ]

        for tz in common_timezones:
            config = SystemConfig(timezone=tz)
            assert config.timezone == tz

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = SystemConfig(
            timezone="Asia/Shanghai",
            location_query=True
        )

        config_dict = config.model_dump()

        assert config_dict["timezone"] == "Asia/Shanghai"
        assert config_dict["location_query"] is True

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = SystemConfig(timezone="UTC")

        json_str = config.model_dump_json()

        assert "UTC" in json_str

    def test_timezone_case_sensitive(self):
        """测试时区大小写敏感。"""
        config1 = SystemConfig(timezone="Asia/Shanghai")
        config2 = SystemConfig(timezone="asia/shanghai")

        # 时区名称是大小写敏感的
        assert config1.timezone == "Asia/Shanghai"
        assert config2.timezone == "asia/shanghai"

    def test_all_fields_custom(self):
        """测试所有字段自定义。"""
        config = SystemConfig(
            timezone="America/Chicago",
            location_query=False
        )

        assert config.timezone == "America/Chicago"
        assert config.location_query is False

    def test_timezone_with_seconds_offset(self):
        """测试带秒偏移的时区（罕见但有效）。"""
        config = SystemConfig(timezone="Etc/GMT-5")

        assert config.timezone == "Etc/GMT-5"

    def test_china_timezones(self):
        """测试中国时区。"""
        china_timezones = [
            "Asia/Shanghai",
            "Asia/Chongqing",
            "Asia/Harbin",
            "Asia/Urumqi"
        ]

        for tz in china_timezones:
            config = SystemConfig(timezone=tz)
            assert config.timezone == tz

    def test_us_timezones(self):
        """测试美国时区。"""
        us_timezones = [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Phoenix",
            "America/Anchorage"
        ]

        for tz in us_timezones:
            config = SystemConfig(timezone=tz)
            assert config.timezone == tz

    def test_european_timezones(self):
        """测试欧洲时区。"""
        european_timezones = [
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/Moscow",
            "Europe/Rome",
            "Europe/Madrid"
        ]

        for tz in european_timezones:
            config = SystemConfig(timezone=tz)
            assert config.timezone == tz

    def test_asian_timezones(self):
        """测试亚洲时区。"""
        asian_timezones = [
            "Asia/Shanghai",
            "Asia/Tokyo",
            "Asia/Seoul",
            "Asia/Singapore",
            "Asia/Dubai",
            "Asia/Kolkata",
            "Asia/Bangkok",
            "Asia/Jakarta"
        ]

        for tz in asian_timezones:
            config = SystemConfig(timezone=tz)
            assert config.timezone == tz

    def test_location_query_for_privacy(self):
        """测试位置查询禁用（隐私考虑）。"""
        config = SystemConfig(
            timezone="Europe/Berlin",
            location_query=False
        )

        assert config.location_query is False
