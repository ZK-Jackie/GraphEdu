"""测试 Neo4j 配置。"""

import pytest
from pydantic import ValidationError

from graphedu.common.config.modules.datasource.neo4j import Neo4jConfig, Neo4jDsn


class TestNeo4jDsn:
    """测试 Neo4jDsn 自定义类型。"""

    def test_bolt_protocol(self):
        """测试 bolt 协议。"""
        dsn = Neo4jDsn("bolt://localhost:7687")
        assert str(dsn) == "bolt://localhost:7687"

    def test_bolt_secure_protocol(self):
        """测试 bolt+s 协议（安全）。"""
        dsn = Neo4jDsn("bolt+s://localhost:7687")
        assert str(dsn) == "bolt+s://localhost:7687"

    def test_bolt_self_signed_protocol(self):
        """测试 bolt+ssc 协议（自签名证书）。"""
        dsn = Neo4jDsn("bolt+ssc://localhost:7687")
        assert str(dsn) == "bolt+ssc://localhost:7687"

    def test_neo4j_protocol(self):
        """测试 neo4j 协议。"""
        dsn = Neo4jDsn("neo4j://localhost:7687")
        assert str(dsn) == "neo4j://localhost:7687"

    def test_neo4j_secure_protocol(self):
        """测试 neo4j+s 协议（安全）。"""
        dsn = Neo4jDsn("neo4j+s://localhost:7687")
        assert str(dsn) == "neo4j+s://localhost:7687"

    def test_neo4j_self_signed_protocol(self):
        """测试 neo4j+ssc 协议（自签名证书）。"""
        dsn = Neo4jDsn("neo4j+ssc://localhost:7687")
        assert str(dsn) == "neo4j+ssc://localhost:7687"

    def test_custom_host(self):
        """测试自定义主机。"""
        dsn = Neo4jDsn("bolt://neo4j.example.com:7687")
        assert "neo4j.example.com" in str(dsn)

    def test_custom_port(self):
        """测试自定义端口。"""
        dsn = Neo4jDsn("bolt://localhost:7688")
        assert "7688" in str(dsn)

    def test_ipv4_host(self):
        """测试 IPv4 地址。"""
        dsn = Neo4jDsn("bolt://192.168.1.100:7687")
        assert "192.168.1.100" in str(dsn)

    def test_ipv6_host(self):
        """测试 IPv6 地址。"""
        dsn = Neo4jDsn("bolt://[::1]:7687")
        assert "::1" in str(dsn)

    def test_invalid_scheme(self):
        """测试无效的协议。"""
        with pytest.raises(ValidationError):
            Neo4jDsn("http://localhost:7687")

    def test_missing_host(self):
        """测试缺少主机。"""
        with pytest.raises(ValidationError):
            Neo4jDsn("bolt://")


class TestNeo4jConfig:
    """测试 Neo4jConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = Neo4jConfig()

        assert str(config.dsn) == "bolt://localhost:7687"
        assert config.auth == ["neo4j:password"]
        assert config.timeout == 30

    def test_custom_dsn(self):
        """测试自定义 DSN。"""
        config = Neo4jConfig(dsn="bolt+s://neo4j.example.com:7687")

        assert str(config.dsn) == "bolt+s://neo4j.example.com:7687"

    def test_custom_auth(self):
        """测试自定义认证信息。"""
        config = Neo4jConfig(auth=["admin:secret"])

        assert config.auth == ["admin:secret"]

    def test_custom_timeout(self):
        """测试自定义超时时间。"""
        config = Neo4jConfig(timeout=60)

        assert config.timeout == 60

    def test_timeout_validation_positive(self):
        """测试超时时间验证（正数）。"""
        config = Neo4jConfig(timeout=1)

        assert config.timeout == 1

    def test_timeout_validation_zero(self):
        """测试超时时间验证（零应失败）。"""
        with pytest.raises(ValidationError):
            Neo4jConfig(timeout=0)

    def test_timeout_validation_negative(self):
        """测试超时时间验证（负数应失败）。"""
        with pytest.raises(ValidationError):
            Neo4jConfig(timeout=-10)

    def test_get_auth_tuples_default(self):
        """测试获取默认认证元组。"""
        config = Neo4jConfig()

        username, password = config.get_auth_tuples()

        assert username == "neo4j"
        assert password == "password"

    def test_get_auth_tuples_custom(self):
        """测试获取自定义认证元组。"""
        config = Neo4jConfig(auth=["admin:admin123"])

        username, password = config.get_auth_tuples()

        assert username == "admin"
        assert password == "admin123"

    def test_get_auth_tuples_special_chars(self):
        """测试包含特殊字符的认证。"""
        config = Neo4jConfig(auth=["user:p@ss:w0rd"])

        username, password = config.get_auth_tuples()

        assert username == "user"
        assert password == "p@ss:w0rd"

    def test_get_auth_tuples_empty_auth(self):
        """测试空认证列表。"""
        config = Neo4jConfig(auth=[])

        with pytest.raises(ValueError, match="Auth list cannot be empty"):
            config.get_auth_tuples()

    def test_get_auth_tuples_invalid_format(self):
        """测试无效的认证格式。"""
        config = Neo4jConfig(auth=["invalid_format"])

        with pytest.raises(ValueError, match="must be in the format"):
            config.get_auth_tuples()

    def test_get_auth_tuples_no_colon(self):
        """测试没有冒号的认证字符串。"""
        config = Neo4jConfig(auth=["usernameonly"])

        with pytest.raises(ValueError, match="must be in the format"):
            config.get_auth_tuples()

    def test_get_auth_tuples_multiple_colons(self):
        """测试包含多个冒号的认证字符串（密码中包含冒号）。"""
        config = Neo4jConfig(auth=["user:pass:word"])

        username, password = config.get_auth_tuples()

        assert username == "user"
        assert password == "pass:word"

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = Neo4jConfig(
            dsn="bolt+s://neo4j.example.com:7687",
            auth=["admin:secret"],
            timeout=45
        )

        config_dict = config.model_dump(mode="json")

        assert "bolt+s" in config_dict["dsn"]
        assert config_dict["auth"] == ["admin:secret"]
        assert config_dict["timeout"] == 45

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = Neo4jConfig(dsn="bolt://localhost:7687")

        json_str = config.model_dump_json()

        assert "bolt" in json_str
        assert "7687" in json_str

    def test_dsn_type_validation(self):
        """测试 DSN 类型验证。"""
        config = Neo4jConfig(dsn="bolt://localhost:7687")
        assert isinstance(config.dsn, Neo4jDsn)

    def test_auth_with_multiple_entries(self):
        """测试认证列表有多条记录（只取第一条）。"""
        config = Neo4jConfig(auth=["user1:pass1", "user2:pass2"])

        username, password = config.get_auth_tuples()

        # 应该只使用第一条
        assert username == "user1"
        assert password == "pass1"

    def test_secure_connection_config(self):
        """测试安全连接配置。"""
        config = Neo4jConfig(dsn="bolt+s://secure.neo4j.com:7687")

        assert "bolt+s" in str(config.dsn)
        assert "secure" in str(config.dsn)

    def test_connection_routing_context(self):
        """测试连接路由上下文。"""
        config = Neo4jConfig(
            dsn="bolt://localhost:7687/?routing=mycontext"
        )

        assert "routing" in str(config.dsn)
