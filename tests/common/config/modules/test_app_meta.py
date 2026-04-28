"""测试应用元数据配置。"""

import pytest

from graphedu.common.config.modules.app.meta import AppMetaConfig


class TestAppMetaConfig:
    """测试 AppMetaConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = AppMetaConfig()

        assert config.name == "graphedu-service"
        assert config.version == "0.0.1"
        assert config.author is None
        assert config.repository is None

    def test_custom_values(self):
        """测试自定义值。"""
        config = AppMetaConfig(
            name="test-app",
            version="1.0.0",
            author="Test Author",
            repository="https://github.com/test/test",
        )

        assert config.name == "test-app"
        assert config.version == "1.0.0"
        assert config.author == "Test Author"
        assert config.repository == "https://github.com/test/test"

    def test_name_field(self):
        """测试 name 字段。"""
        config = AppMetaConfig(name="custom-name")

        assert config.name == "custom-name"

    def test_version_field(self):
        """测试 version 字段。"""
        config = AppMetaConfig(version="2.1.0")

        assert config.version == "2.1.0"

    def test_author_field(self):
        """测试 author 字段。"""
        config = AppMetaConfig(author="Test Author")

        assert config.author == "Test Author"

    def test_author_field_optional(self):
        """测试 author 字段可选。"""
        config = AppMetaConfig()

        assert config.author is None

    def test_repository_field(self):
        """测试 repository 字段。"""
        url = "https://github.com/example/repo"
        config = AppMetaConfig(repository=url)

        assert config.repository == url

    def test_repository_field_optional(self):
        """测试 repository 字段可选。"""
        config = AppMetaConfig()

        assert config.repository is None

    def test_semantic_version(self):
        """测试语义化版本号。"""
        versions = ["1.0.0", "2.1.3", "0.0.1", "10.20.30"]

        for version in versions:
            config = AppMetaConfig(version=version)
            assert config.version == version

    def test_name_with_hyphens(self):
        """测试带连字符的应用名称。"""
        config = AppMetaConfig(name="my-test-app")

        assert config.name == "my-test-app"

    def test_name_with_underscores(self):
        """测试带下划线的应用名称。"""
        config = AppMetaConfig(name="my_test_app")

        assert config.name == "my_test_app"

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = AppMetaConfig(
            name="test",
            version="1.0.0",
            author="Author",
            repository="https://repo.com",
        )

        config_dict = config.model_dump()

        assert config_dict["name"] == "test"
        assert config_dict["version"] == "1.0.0"
        assert config_dict["author"] == "Author"
        assert config_dict["repository"] == "https://repo.com"

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = AppMetaConfig(name="test", version="1.0.0")

        json_str = config.model_dump_json()

        assert "test" in json_str
        assert "1.0.0" in json_str
