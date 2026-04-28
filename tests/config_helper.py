"""
测试配置辅助模块

提供在测试中快速加载和使用测试配置的便利函数。
"""

from pathlib import Path

from pydantic import ValidationError
import pytest

from graphedu.common.config import ServiceConfig, setup_config
from graphedu.common.config.core.graph_db import Neo4jConfig
from graphedu.common.config.core.storage import (
    MysqlConfig,
    OssConfig,
    PoolConfig,
    PostgresqlConfig,
    RedisConfig,
)

# =============================================================================
# 测试配置文件路径
# =============================================================================
TEST_CONFIG_PATH = Path(__file__).parent / "test.config.yaml"


# =============================================================================
# 配置加载函数
# =============================================================================

def load_test_config(config_path: Path | None = None) -> ServiceConfig:
    """
    加载测试配置文件

    Args:
        config_path: 配置文件路径，默认使用 tests/test.config.yaml

    Returns:
        ServiceConfig: 加载的配置对象

    Raises:
        FileNotFoundError: 如果配置文件不存在
        ValidationError: 如果配置格式不正确

    示例:
        >>> config = load_test_config()
        >>> print(config.mode)
        'test'
    """
    if config_path is None:
        config_path = TEST_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(
            f"测试配置文件不存在: {config_path}\n"
            f"请确保测试配置文件已创建。"
        )

    # 设置配置环境
    setup_config(str(config_path))

    # 加载配置
    try:
        return ServiceConfig.auto_load_config()
    except ValidationError as e:
        raise ValueError(
            f"测试配置文件格式错误: {config_path}\n"
            f"验证错误: {e}\n"
            f"请检查配置文件格式是否正确。"
        ) from e


def get_test_postgresql_config() -> PostgresqlConfig:
    """
    获取测试用的 PostgreSQL 配置

    Returns:
        PostgresqlConfig: PostgreSQL 配置对象

    示例:
        >>> config = get_test_postgresql_config()
        >>> print(config.dsn)
        'postgresql+psycopg://test_user:test_pass@localhost:5432/test_graphedu'
    """
    return PostgresqlConfig(
        dsn='postgresql+psycopg://test_user:test_pass@localhost:5432/test_graphedu',
        echo=False,
        pool=PoolConfig(
            pool_size=5,
            pool_recycle=3600,
            pool_timeout=30,
            pool_pre_ping=True,
        ),
    )


def get_test_mysql_config() -> MysqlConfig:
    """
    获取测试用的 MySQL 配置

    Returns:
        MysqlConfig: MySQL 配置对象
    """
    return MysqlConfig(
        url='mysql+pymysql://test_user:test_pass@localhost:3306/test_graphedu',
        echo=False,
        pool={'pool_size': 5},
    )


def get_test_redis_config() -> RedisConfig:
    """
    获取测试用的 Redis 配置

    Returns:
        RedisConfig: Redis 配置对象
    """
    return RedisConfig(
        url='redis://localhost:6379/0',
    )


def get_test_neo4j_config() -> Neo4jConfig:
    """
    获取测试用的 Neo4j 配置

    Returns:
        Neo4jConfig: Neo4j 配置对象
    """
    return Neo4jConfig(
        uri='bolt://localhost:7687',
        username='neo4j',
        password='test_password',
    )


def get_test_oss_config() -> OssConfig:
    """
    获取测试用的 OSS/S3 配置

    Returns:
        OssConfig: OSS 配置对象
    """
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


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_config():
    """
    Session 级别的测试配置 fixture

    在整个测试会话期间只加载一次配置，提高测试效率。

    示例:
        def test_something(test_config):
            assert test_config.mode == 'test'
            assert test_config.database.postgresql.dsn is not None
    """
    return load_test_config()


@pytest.fixture(scope="session")
def test_pg_config(test_config):
    """
    Session 级别的 PostgreSQL 配置 fixture

    示例:
        def test_database(test_pg_config):
            assert test_pg_config.dsn is not None
    """
    return test_config.database.postgresql


@pytest.fixture(scope="session")
def test_mysql_config(test_config):
    """
    Session 级别的 MySQL 配置 fixture
    """
    return test_config.database.mysql


@pytest.fixture(scope="session")
def test_redis_config(test_config):
    """
    Session 级别的 Redis 配置 fixture
    """
    return test_config.database.redis


@pytest.fixture(scope="session")
def test_neo4j_config(test_config):
    """
    Session 级别的 Neo4j 配置 fixture
    """
    return test_config.database.neo4j


@pytest.fixture(scope="session")
def test_oss_config(test_config):
    """
    Session 级别的 OSS 配置 fixture
    """
    return test_config.distribute.oss


# =============================================================================
# 快捷配置获取函数
# =============================================================================

def get_test_db_dsn(db_type: str = "postgresql") -> str:
    """
    获取测试数据库的 DSN 连接字符串

    Args:
        db_type: 数据库类型，支持 'postgresql', 'mysql'

    Returns:
        str: 数据库连接字符串

    示例:
        >>> dsn = get_test_db_dsn('postgresql')
        >>> 'postgresql' in dsn
        True
    """
    configs = {
        "postgresql": "postgresql+psycopg://test_user:test_pass@localhost:5432/test_graphedu",
        "mysql": "mysql+pymysql://test_user:test_pass@localhost:3306/test_graphedu",
    }
    if db_type not in configs:
        raise ValueError(f"不支持的数据库类型: {db_type}")
    return configs[db_type]


def get_test_redis_url(db: int = 0) -> str:
    """
    获取测试 Redis 的连接 URL

    Args:
        db: Redis 数据库编号

    Returns:
        str: Redis 连接 URL

    示例:
        >>> url = get_test_redis_url(0)
        >>> 'redis://localhost:6379/0' == url
        True
    """
    return f"redis://localhost:6379/{db}"


def get_test_s3_endpoint() -> str:
    """
    获取测试 S3 服务的端点地址

    Returns:
        str: S3 端点地址

    示例:
        >>> endpoint = get_test_s3_endpoint()
        >>> 'localhost:9000' in endpoint
        True
    """
    return "http://localhost:9000"


# =============================================================================
# 配置验证函数
# =============================================================================

def validate_test_config() -> bool:
    """
    验证测试配置文件是否有效

    Returns:
        bool: 配置是否有效

    示例:
        >>> is_valid = validate_test_config()
        >>> print(f"配置有效: {is_valid}")
    """
    try:
        config = load_test_config()
        return config is not None and config.mode == 'test'
    except Exception:
        return False


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 测试配置加载
    print("加载测试配置...")
    config = load_test_config()

    print("✅ 配置加载成功!")
    print(f"模式: {config.mode}")
    print(f"PostgreSQL DSN: {config.datasource.postgresql.dsn}")
    print(f"Redis URL: {config.datasource.redis.url}")
    print(f"Neo4j URI: {config.datasource.neo4j.uri}")
    print(f"OSS 端点: {config.datasource.oss.endpoint}")
