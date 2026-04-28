"""测试 AI Agent 配置。"""

from typing import Literal

import pytest
from pydantic import PostgresDsn, ValidationError


class TestAgentConfig:
    """测试 AgentConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig()

        assert config.checkpoint_provider == "postgresql"
        assert str(config.dsn) == "postgresql://postgres:postgres@localhost:5432/graphedu"
        assert config.checkpoint_collection_name == "checkpoints"
        assert config.writes_collection_name == "checkpoint_writes"

    def test_custom_checkpoint_provider_postgresql(self):
        """测试自定义检查点存储提供商（PostgreSQL）。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(checkpoint_provider="postgresql")

        assert config.checkpoint_provider == "postgresql"

    def test_custom_checkpoint_provider_mongodb(self):
        """测试自定义检查点存储提供商（MongoDB）。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(checkpoint_provider="mongodb")

        assert config.checkpoint_provider == "mongodb"

    def test_invalid_checkpoint_provider(self):
        """测试无效的检查点存储提供商。"""
        from graphedu.common.config.modules.agent import AgentConfig

        with pytest.raises(ValidationError):
            AgentConfig(checkpoint_provider="redis")  # type: ignore

    def test_custom_dsn(self):
        """测试自定义 DSN。"""
        from graphedu.common.config.modules.agent import AgentConfig

        custom_dsn = "postgresql://user:password@db.example.com:5432/agent_db"
        config = AgentConfig(dsn=custom_dsn)

        assert str(config.dsn) == custom_dsn

    def test_custom_checkpoint_collection_name(self):
        """测试自定义检查点集合名称。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(checkpoint_collection_name="my_checkpoints")

        assert config.checkpoint_collection_name == "my_checkpoints"

    def test_custom_writes_collection_name(self):
        """测试自定义写入记录集合名称。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(writes_collection_name="my_writes")

        assert config.writes_collection_name == "my_writes"

    def test_dsn_with_different_components(self):
        """测试不同组件的 DSN。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            dsn="postgresql://admin:admin123@postgres-server:5432/agent_production"
        )

        assert "admin" in str(config.dsn)
        assert "postgres-server" in str(config.dsn)
        assert "agent_production" in str(config.dsn)

    def test_dsn_with_connection_params(self):
        """测试带连接参数的 DSN。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            dsn="postgresql://user:pass@localhost:5432/db?sslmode=require"
        )

        assert "sslmode" in str(config.dsn)

    def test_collection_name_with_prefix(self):
        """测试带前缀的集合名称。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_collection_name="agent_checkpoints",
            writes_collection_name="agent_writes"
        )

        assert config.checkpoint_collection_name == "agent_checkpoints"
        assert config.writes_collection_name == "agent_writes"

    def test_collection_name_with_underscores(self):
        """测试带下划线的集合名称。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_collection_name="check_points_v1",
            writes_collection_name="write_records_v1"
        )

        assert "check_points_v1" in config.checkpoint_collection_name
        assert "write_records_v1" in config.writes_collection_name

    def test_mongodb_provider_config(self):
        """测试 MongoDB 提供商配置。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_provider="mongodb",
            checkpoint_collection_name="agent_checkpoints",
            writes_collection_name="agent_writes"
        )

        assert config.checkpoint_provider == "mongodb"

    def test_postgresql_provider_config(self):
        """测试 PostgreSQL 提供商配置。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_provider="postgresql",
            dsn="postgresql://postgres:postgres@localhost:5432/graphedu"
        )

        assert config.checkpoint_provider == "postgresql"
        assert "graphedu" in str(config.dsn)

    def test_dsn_type_validation(self):
        """测试 DSN 类型验证。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(dsn="postgresql://user:pass@localhost:5432/db")
        assert isinstance(config.dsn, PostgresDsn)

    def test_checkpoint_provider_literal_type(self):
        """测试 checkpoint_provider 字面类型。"""
        from graphedu.common.config.modules.agent import AgentConfig

        # 有效值
        valid_providers: list[Literal["mongodb", "postgresql"]] = [
            "mongodb",
            "postgresql"
        ]

        for provider in valid_providers:
            config = AgentConfig(checkpoint_provider=provider)
            assert config.checkpoint_provider == provider

    def test_config_serialization(self):
        """测试配置序列化。"""
        import warnings
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_provider="postgresql",
            checkpoint_collection_name="checkpoints",
            writes_collection_name="writes"
        )

        # 忽略 Pydantic 序列化警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config_dict = config.model_dump(mode="json")

        assert config_dict["checkpoint_provider"] == "postgresql"
        assert config_dict["checkpoint_collection_name"] == "checkpoints"
        assert config_dict["writes_collection_name"] == "writes"

    def test_config_json(self):
        """测试 JSON 序列化。"""
        import warnings
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(checkpoint_provider="mongodb")

        # 忽略 Pydantic 序列化警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            json_str = config.model_dump_json()

        assert "mongodb" in json_str

    def test_collection_names_empty_string(self):
        """测试空集合名称（有效，虽然不推荐）。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_collection_name="",
            writes_collection_name=""
        )

        assert config.checkpoint_collection_name == ""
        assert config.writes_collection_name == ""

    def test_collection_names_with_numbers(self):
        """测试包含数字的集合名称。"""
        from graphedu.common.config.modules.agent import AgentConfig

        config = AgentConfig(
            checkpoint_collection_name="checkpoints_v1",
            writes_collection_name="writes_2024"
        )

        assert "v1" in config.checkpoint_collection_name
        assert "2024" in config.writes_collection_name

    def test_different_database_names(self):
        """测试不同数据库名称。"""
        from graphedu.common.config.modules.agent import AgentConfig

        databases = [
            "agent_db",
            "langgraph_db",
            "checkpoints",
            "production"
        ]

        for db_name in databases:
            dsn = f"postgresql://postgres:postgres@localhost:5432/{db_name}"
            config = AgentConfig(dsn=dsn)
            assert db_name in str(config.dsn)

    def test_checkpoint_for_different_agents(self):
        """测试不同 Agent 的检查点配置。"""
        from graphedu.common.config.modules.agent import AgentConfig

        # Research Agent
        research_config = AgentConfig(
            checkpoint_collection_name="research_checkpoints",
            writes_collection_name="research_writes"
        )

        # Code Agent
        code_config = AgentConfig(
            checkpoint_collection_name="code_checkpoints",
            writes_collection_name="code_writes"
        )

        assert "research" in research_config.checkpoint_collection_name
        assert "code" in code_config.checkpoint_collection_name
