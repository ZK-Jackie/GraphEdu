"""
测试配置模块

提供测试用的配置对象工厂函数和模拟配置。
"""

from typing import Literal

from graphedu.common.config.modules.datasource.base import PoolConfig
from graphedu.common.config.modules.datasource.mysql import MysqlConfig
from graphedu.common.config.modules.datasource.neo4j import Neo4jConfig
from graphedu.common.config.modules.datasource.oss import OssConfig
from graphedu.common.config.modules.datasource.postgresql import PostgresqlConfig
from graphedu.common.config.modules.datasource.redis import RedisConfig


class TestConfigs:
    """测试配置工厂类"""

    # ========== PostgreSQL 配置 ==========

    @staticmethod
    def postgresql_config(
        dsn: str | None = None,
        echo: bool = False,
        pool_size: int = 5,
    ) -> PostgresqlConfig:
        """
        创建测试用的 PostgreSQL 配置

        Args:
            dsn: 数据库连接字符串
            echo: 是否打印 SQL 语句
            pool_size: 连接池大小

        Returns:
            PostgresqlConfig: PostgreSQL 配置对象
        """
        return PostgresqlConfig(
            dsn=dsn or "postgresql://test:test@localhost:5432/test_db",
            echo=echo,
            pool=PoolConfig(
                pool_size=pool_size,
                pool_recycle=3600,
                pool_timeout=30,
                pool_pre_ping=True,
            ),
        )

    # ========== MySQL 配置 ==========

    @staticmethod
    def mysql_config(
        dsn: str | None = None,
        echo: bool = False,
        pool_size: int = 5,
    ) -> MysqlConfig:
        """
        创建测试用的 MySQL 配置

        Args:
            dsn: 数据库连接字符串
            echo: 是否打印 SQL 语句
            pool_size: 连接池大小

        Returns:
            MysqlConfig: MySQL 配置对象
        """
        return MysqlConfig(
            dsn=dsn or "mysql://test:test@localhost:3306/test_db",
            echo=echo,
            pool=PoolConfig(pool_size=pool_size),
        )

    # ========== Redis 配置 ==========

    @staticmethod
    def redis_config(
        dsn: str | None = None,
    ) -> RedisConfig:
        """
        创建测试用的 Redis 配置

        Args:
            dsn: Redis 连接字符串

        Returns:
            RedisConfig: Redis 配置对象
        """
        return RedisConfig(
            dsn=dsn or "redis://localhost:6379/0",
        )

    # ========== Neo4j 配置 ==========

    @staticmethod
    def neo4j_config(
        dsn: str | None = None,
        auth: list[str] | None = None,
        timeout: int = 30,
    ) -> Neo4jConfig:
        """
        创建测试用的 Neo4j 配置

        Args:
            dsn: Neo4j 连接地址
            auth: 认证信息列表，格式为 ['username:password']
            timeout: 连接超时时间（秒）

        Returns:
            Neo4jConfig: Neo4j 配置对象
        """
        return Neo4jConfig(
            dsn=dsn or "bolt://localhost:7687",
            auth=auth or ["neo4j:test_password"],
            timeout=timeout,
        )

    # ========== OSS/S3 配置 ==========

    @staticmethod
    def oss_config(
        provider: Literal["aws", "aliyun", "minio", "rustfs", "cloudflare", "tencent", "generic"] = "minio",
        endpoint: str | None = None,
        access_key: str = "test_access_key",
        secret_key: str = "test_secret_key",
        use_ssl: bool = False,
        bucket: str = "test-bucket",
        upload_from: str = "/tmp/test_upload",
        download_to: str = "/tmp/test_download",
    ) -> OssConfig:
        """
        创建测试用的 OSS/S3 配置

        Args:
            provider: OSS 服务提供商
            endpoint: OSS 端点
            access_key: 访问密钥
            secret_key: 密钥
            use_ssl: 是否使用 SSL
            bucket: 存储桶名称
            upload_from: 上传目录
            download_to: 下载目录

        Returns:
            OssConfig: OSS 配置对象
        """
        return OssConfig(
            provider=provider,
            endpoint=endpoint or "http://localhost:9000",
            access_key=access_key,
            secret_key=secret_key,
            use_ssl=use_ssl,
            bucket=bucket,
            upload_from=upload_from,
            download_to=download_to,
        )


class InvalidTestConfigs:
    """无效测试配置工厂类 - 用于测试错误处理"""

    @staticmethod
    def invalid_postgresql_dsn() -> PostgresqlConfig:
        """创建无效的 PostgreSQL DSN 配置"""
        return PostgresqlConfig.model_construct(
            dsn="invalid://dsn",
            echo=False,
            pool=PoolConfig(),
        )

    @staticmethod
    def invalid_redis_url() -> RedisConfig:
        """创建无效的 Redis URL 配置"""
        return RedisConfig.model_construct(
            dsn="invalid://redis:url",
        )

    @staticmethod
    def invalid_neo4j_uri() -> Neo4jConfig:
        """创建无效的 Neo4j URI 配置"""
        return Neo4jConfig.model_construct(
            dsn="invalid://neo4j:9999",
            auth=["neo4j:test"],
            timeout=30,
        )

    @staticmethod
    def invalid_s3_endpoint() -> OssConfig:
        """创建无效的 S3 端点配置"""
        return OssConfig.model_construct(
            provider="minio",
            endpoint="http://invalid-endpoint:9999",
            access_key="invalid",
            secret_key="invalid",
            bucket="invalid-bucket",
            use_ssl=False,
            upload_from="/tmp/test_upload",
            download_to="/tmp/test_download",
        )
