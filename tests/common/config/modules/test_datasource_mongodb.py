"""测试 MongoDB 配置。"""

import pytest
from pydantic import MongoDsn, ValidationError

from graphedu.common.config.modules.datasource import MongodbConfig


class TestMongodbConfig:
    """测试 MongodbConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = MongodbConfig()

        assert str(config.url) == "mongodb://localhost:27017"
        assert config.db_name == "graphedu"

    def test_custom_url(self):
        """测试自定义 URL。"""
        custom_url = "mongodb://mongo.example.com:27018"
        config = MongodbConfig(url=custom_url)

        assert str(config.url) == custom_url

    def test_custom_db_name(self):
        """测试自定义数据库名称。"""
        config = MongodbConfig(db_name="production_db")

        assert config.db_name == "production_db"

    def test_url_with_auth(self):
        """测试带认证的 URL。"""
        config = MongodbConfig(url="mongodb://admin:password@localhost:27017")

        assert "admin" in str(config.url)
        assert "password" in str(config.url)

    def test_url_with_multiple_hosts(self):
        """测试多主机 URL（副本集）。"""
        config = MongodbConfig(
            url="mongodb://host1:27017,host2:27017,host3:27017"
        )

        assert "host1" in str(config.url)
        assert "host2" in str(config.url)
        assert "host3" in str(config.url)

    def test_url_with_replica_set(self):
        """测试副本集配置。"""
        config = MongodbConfig(
            url="mongodb://localhost:27017/?replicaSet=myReplicaSet"
        )

        assert "replicaSet" in str(config.url)

    def test_url_with_auth_source(self):
        """测试认证源配置。"""
        config = MongodbConfig(
            url="mongodb://user:pass@localhost:27017/?authSource=admin"
        )

        assert "authSource" in str(config.url)

    def test_url_with_ssl(self):
        """测试 SSL 连接。"""
        config = MongodbConfig(url="mongodb://localhost:27017/?tls=true")

        assert "tls" in str(config.url)

    def test_url_with_srv_record(self):
        """测试 SRV 记录连接。"""
        config = MongodbConfig(url="mongodb+srv://example.com")

        assert "mongodb+srv" in str(config.url)

    def test_url_type_validation(self):
        """测试 URL 类型验证。"""
        config = MongodbConfig(url="mongodb://localhost:27017")
        assert isinstance(config.url, MongoDsn)

    def test_invalid_url(self):
        """测试无效的 URL。"""
        # 无效的协议应该抛出 ValidationError
        with pytest.raises(ValidationError):
            MongodbConfig(url="http://localhost:27017")

    def test_db_name_validation(self):
        """测试数据库名称验证。"""
        # 有效的数据库名称
        valid_names = ["test", "test_db", "test-db", "test123"]
        for name in valid_names:
            config = MongodbConfig(db_name=name)
            assert config.db_name == name

    def test_db_name_empty(self):
        """测试空数据库名称。"""
        # 空字符串是有效的（虽然不推荐）
        config = MongodbConfig(db_name="")
        assert config.db_name == ""

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = MongodbConfig(
            url="mongodb://mongo.example.com:27018",
            db_name="production"
        )

        config_dict = config.model_dump(mode="json")

        assert config_dict["url"] == "mongodb://mongo.example.com:27018"
        assert config_dict["db_name"] == "production"

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = MongodbConfig(url="mongodb://localhost:27017", db_name="test")

        json_str = config.model_dump_json()

        assert "mongodb" in json_str
        assert "test" in json_str

    def test_url_with_write_concern(self):
        """测试写入关注点配置。"""
        config = MongodbConfig(
            url="mongodb://localhost:27017/?w=majority&wtimeoutMS=5000"
        )

        assert "w" in str(config.url)

    def test_url_with_read_preference(self):
        """测试读取偏好配置。"""
        config = MongodbConfig(
            url="mongodb://localhost:27017/?readPreference=secondaryPreferred"
        )

        assert "readPreference" in str(config.url)

    def test_url_with_max_pool_size(self):
        """测试连接池大小配置。"""
        config = MongodbConfig(
            url="mongodb://localhost:27017/?maxPoolSize=100&minPoolSize=10"
        )

        assert "maxPoolSize" in str(config.url)
        assert "minPoolSize" in str(config.url)

    def test_url_with_compression(self):
        """测试压缩配置。"""
        config = MongodbConfig(url="mongodb://localhost:27017/?compressors=snappy,zlib")

        assert "compressors" in str(config.url)
