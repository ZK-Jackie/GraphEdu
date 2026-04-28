"""
Resource 模块测试配置文件

该文件包含所有 resource 模块测试共享的 pytest fixtures 和配置。
"""

import asyncio
from collections.abc import Generator
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from _pytest.fixtures import FixtureRequest
from dependency_injector import containers, providers
from neo4j import AsyncDriver, Driver
import pytest
from pytest_mock import MockerFixture
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from graphedu.common.resource import AsyncExecutor, MysqlClient

# 配置测试日志
logging.basicConfig(level=logging.DEBUG)


# =============================================================================
# 直接定义测试配置辅助函数，避免循环导入
# =============================================================================

def get_test_postgresql_config():
    """获取测试用的 PostgreSQL 配置"""
    from graphedu.common.config.modules.datasource.base import PoolConfig
    from graphedu.common.config.modules.datasource.postgresql import PostgresqlConfig
    return PostgresqlConfig(
        dsn='postgresql://test_user:test_pass@localhost:5432/test_graphedu',
        echo=False,
        pool=PoolConfig(
            pool_size=5,
            pool_recycle=3600,
            pool_timeout=30,
            pool_pre_ping=True,
        ),
    )


def get_test_mysql_config():
    """获取测试用的 MySQL 配置"""
    from graphedu.common.config.modules.datasource.base import PoolConfig
    from graphedu.common.config.modules.datasource.mysql import MysqlConfig
    return MysqlConfig(
        dsn='mysql://test_user:test_pass@localhost:3306/test_graphedu',
        echo=False,
        pool=PoolConfig(pool_size=5),
    )


def get_test_redis_config():
    """获取测试用的 Redis 配置"""
    from graphedu.common.config.modules.datasource.redis import RedisConfig
    return RedisConfig(
        dsn='redis://localhost:6379/0',
    )


def get_test_neo4j_config():
    """获取测试用的 Neo4j 配置"""
    from graphedu.common.config.modules.datasource.neo4j import Neo4jConfig
    return Neo4jConfig(
        dsn='bolt://localhost:7687',
        auth=['neo4j:test_password'],
        timeout=30,
    )


def get_test_oss_config():
    """获取测试用的 OSS/S3 配置"""
    from graphedu.common.config.modules.datasource.oss import OssConfig
    return OssConfig(
        provider='minio',
        endpoint='http://localhost:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        use_ssl=False,
        bucket='test-graphedu',
        upload_from='/tmp/graphedu/test_upload',
        download_to='/tmp/graphedu/test_download',
    )


def get_test_db_dsn(db_type: str = "postgresql") -> str:
    """获取测试数据库的 DSN 连接字符串（Pydantic 兼容格式）"""
    configs = {
        "postgresql": "postgresql://test_user:test_pass@localhost:5432/test_graphedu",
        "mysql": "mysql://test_user:test_pass@localhost:3306/test_graphedu",
    }
    if db_type not in configs:
        raise ValueError(f"不支持的数据库类型: {db_type}")
    return configs[db_type]


def get_test_redis_url(db: int = 0) -> str:
    """获取测试 Redis 的连接 URL"""
    return f"redis://localhost:6379/{db}"


def get_test_mongodb_config():
    """获取测试用的 MongoDB 配置"""
    from graphedu.common.config.modules.datasource.mongodb import MongodbConfig
    return MongodbConfig(
        url='mongodb://localhost:27017',
        db_name='test_graphedu',
    )


def get_test_s3_endpoint() -> str:
    """获取测试 S3 服务的端点地址"""
    return "http://localhost:9000"


# =============================================================================
# 配置 Fixtures - 使用测试配置辅助模块
# =============================================================================

@pytest.fixture(scope="session")
def test_config():
    """加载测试配置"""
    # 返回一个简单的配置对象，避免循环导入
    class SimpleConfig:
        mode = "test"
        datasource = type('obj', (object,), {
            'postgresql': get_test_postgresql_config(),
            'mysql': get_test_mysql_config(),
            'redis': get_test_redis_config(),
            'neo4j': get_test_neo4j_config(),
            'oss': get_test_oss_config(),
            'mongodb': get_test_mongodb_config(),
        })
    return SimpleConfig()


@pytest.fixture
def test_pg_dsn() -> str:
    """提供测试用的 PostgreSQL DSN"""
    return get_test_db_dsn("postgresql")


@pytest.fixture
def test_mysql_dsn() -> str:
    """提供测试用的 MySQL DSN"""
    return get_test_db_dsn("mysql")


@pytest.fixture
def test_redis_url() -> str:
    """提供测试用的 Redis URL"""
    return get_test_redis_url(0)


@pytest.fixture
def test_neo4j_uri() -> str:
    """提供测试用的 Neo4j URI"""
    return "bolt://localhost:7687"


@pytest.fixture
def test_s3_endpoint() -> str:
    """提供测试用的 S3 端点"""
    return get_test_s3_endpoint()


# =============================================================================
# 配置对象 Fixtures - 使用测试配置辅助模块
# =============================================================================

@pytest.fixture
def pg_pool_config():
    """PostgreSQL 连接池配置"""
    from graphedu.common.config.modules.datasource.base import PoolConfig
    return PoolConfig(
        pool_size=5,
        pool_recycle=3600,
        pool_timeout=30,
        pool_pre_ping=True,
    )


@pytest.fixture
def pg_config():
    """PostgreSQL 配置"""
    return get_test_postgresql_config()


@pytest.fixture
def mysql_config():
    """MySQL 配置"""
    return get_test_mysql_config()


@pytest.fixture
def redis_config():
    """Redis 配置"""
    return get_test_redis_config()


@pytest.fixture
def neo4j_config():
    """Neo4j 配置"""
    return get_test_neo4j_config()


@pytest.fixture
def oss_config():
    """OSS/S3 配置"""
    return get_test_oss_config()


@pytest.fixture
def http_client_config() -> dict:
    """HTTP 客户端配置"""
    return {
        "timeout": 30.0,
        "headers": {"User-Agent": "TestClient"},
        "verify": False,
    }


# =============================================================================
# Mock 数据库引擎 Fixtures
# =============================================================================

@pytest.fixture
def mock_pg_engine(mocker: MockerFixture):
    """Mock PostgreSQL 引擎"""
    engine = MagicMock()
    engine.connect.return_value = MagicMock()
    return engine


@pytest.fixture
def mock_async_pg_engine(mocker: MockerFixture):
    """Mock 异步 PostgreSQL 引擎"""
    engine = AsyncMock()
    engine.connect.return_value = AsyncMock()
    return engine


@pytest.fixture
def mock_redis_client(mocker: MockerFixture):
    """Mock Redis 客户端"""
    client = MagicMock(spec=Redis)
    client.ping.return_value = True
    client.get.return_value = b"test_value"
    client.set.return_value = True
    client.delete.return_value = 1
    return client


@pytest.fixture
def mock_async_redis_client(mocker: MockerFixture):
    """Mock 异步 Redis 客户端"""
    client = AsyncMock(spec=AsyncRedis)
    client.ping.return_value = True
    client.get.return_value = b"test_value"
    client.set.return_value = True
    client.delete.return_value = 1
    return client


@pytest.fixture
def mock_neo4j_driver(mocker: MockerFixture):
    """Mock Neo4j 驱动"""
    driver = MagicMock(spec=Driver)
    driver.verify_connectivity.return_value = None
    driver.execute_query.return_value = ([], MagicMock(), ["key1", "key2"])
    driver.close.return_value = None
    return driver


@pytest.fixture
def mock_async_neo4j_driver(mocker: MockerFixture):
    """Mock 异步 Neo4j 驱动"""
    driver = AsyncMock(spec=AsyncDriver)
    driver.verify_connectivity.return_value = None
    driver.execute_query.return_value = ([], MagicMock(), ["key1", "key2"])
    driver.close.return_value = None
    return driver


@pytest.fixture
def mock_s3_client(mocker: MockerFixture):
    """Mock S3 客户端"""
    client = MagicMock()
    client.upload_file.return_value = None
    client.download_file.return_value = None
    client.upload_fileobj.return_value = None
    client.delete_object.return_value = None
    client.head_object.return_value = {"ETag": '"test-etag-123"'}
    client.generate_presigned_url.return_value = "http://localhost:9000/bucket/object?params"
    return client


@pytest.fixture
def mock_httpx_client(mocker: MockerFixture):
    """Mock httpx 客户端"""
    client = MagicMock()
    # Mock GET response
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.text = '{"success": true}'
    client.get.return_value = mock_get_response

    # Mock POST response
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post_response.text = '{"created": true}'
    client.post.return_value = mock_post_response

    return client


@pytest.fixture
def mock_async_httpx_client(mocker: MockerFixture):
    """Mock 异步 httpx 客户端"""
    client = AsyncMock()

    # Mock GET response
    mock_get_response = AsyncMock()
    mock_get_response.status_code = 200
    mock_get_response.text = '{"success": true}'
    client.get.return_value = mock_get_response

    # Mock POST response
    mock_post_response = AsyncMock()
    mock_post_response.status_code = 201
    mock_post_response.text = '{"created": true}'
    client.post.return_value = mock_post_response

    return client


# =============================================================================
# 事件循环 Fixtures
# =============================================================================

@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# 测试数据 Fixtures
# =============================================================================

@pytest.fixture
def sample_user_data():
    """测试用的用户数据"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role_id": 2,
    }


@pytest.fixture
def sample_file_content():
    """测试用的文件内容"""
    return b"This is a test file content for S3 upload testing."


@pytest.fixture
def sample_s3_objects():
    """测试用的 S3 对象列表"""
    return ["file1.txt", "file2.pdf", "file3.jpg"]


# =============================================================================
# 测试上下文管理器
# =============================================================================

@pytest.fixture
def temp_upload_dir(tmp_path: Path) -> Path:
    """创建临时上传目录"""
    upload_dir = tmp_path / "upload"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@pytest.fixture
def temp_download_dir(tmp_path: Path) -> Path:
    """创建临时下载目录"""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


# =============================================================================
# 日志捕获 Fixture
# =============================================================================

@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """捕获日志输出用于测试"""
    caplog.set_level(logging.DEBUG)
    return caplog
