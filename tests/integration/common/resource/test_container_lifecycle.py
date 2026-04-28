"""容器生命周期集成测试。

测试容器在真实环境中的完整生命周期。
"""

import pytest


@pytest.mark.asyncio
async def test_service_lifecycle():
    """测试 Service 模式的完整生命周期。"""
    from graphedu.common.resource import try_get_container, shutdown_container, ContainerMode
    from unittest.mock import patch, MagicMock

    # 创建 mock 配置
    mock_config = MagicMock()
    mock_config.datasource.postgresql.dsn = "postgresql+psycopg://test:test@localhost:5432/test"
    mock_config.datasource.postgresql.echo = False
    mock_config.datasource.redis.url = "redis://localhost:6379/0"
    mock_config.datasource.neo4j.uri = "bolt://localhost:7687"
    mock_config.datasource.neo4j.username = "neo4j"
    mock_config.datasource.neo4j.password = "test"
    mock_config.datasource.oss.provider = "minio"
    mock_config.datasource.oss.endpoint = "http://localhost:9000"
    mock_config.datasource.oss.access_key = "minioadmin"
    mock_config.datasource.oss.secret_key = "minioadmin"
    mock_config.datasource.oss.use_ssl = False
    mock_config.datasource.oss.bucket = "test-bucket"
    mock_config.model.chat.model = "gpt-4"
    mock_config.model.chat.api_key = "test_key"
    mock_config.model.chat.api_base = "http://localhost:11434/v1"
    mock_config.model.chat.temperature = 0.7
    mock_config.model.long.model = "gpt-4-long"
    mock_config.model.long.api_key = "test_key"
    mock_config.model.long.api_base = "http://localhost:11434/v1"
    mock_config.model.long.temperature = 0.5
    mock_config.model.think.model = "gpt-4-think"
    mock_config.model.think.api_key = "test_key"
    mock_config.model.think.api_base = "http://localhost:11434/v1"
    mock_config.model.think.temperature = 0.3
    mock_config.agent.dsn = "postgresql+psycopg://test:test@localhost:5432/test"

    with patch('graphedu.common.resource.container.get_config', return_value=mock_config):
        # Mock 数据库查询以避免真实数据库连接
        with patch('graphedu.common.resource.scheduler.async_scheduler.get_db_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.scalars.return_value.all.return_value = []

            # 初始化
            container = await try_get_container(ContainerMode.SERVICE)
            assert container is not None

            # 验证资源可用
            assert hasattr(container, 'postgresql_client')
            assert hasattr(container, 'redis_client')

            # 关闭
            await shutdown_container()


@pytest.mark.asyncio
async def test_generator_lifecycle():
    """测试 Generator 模式的完整生命周期。"""
    from graphedu.common.resource import try_get_container, shutdown_container, ContainerMode
    from unittest.mock import patch, MagicMock

    # 创建 mock 配置
    mock_config = MagicMock()
    mock_config.datasource.postgresql.dsn = "postgresql+psycopg://test:test@localhost:5432/test"
    mock_config.datasource.postgresql.echo = False

    with patch('graphedu.common.resource.container.get_config', return_value=mock_config):
        # 初始化
        container = await try_get_container(ContainerMode.GENERATOR)
        assert container is not None

        # 验证数据库可用
        assert hasattr(container, 'postgresql_client')

        # 验证 LLM 不可用
        assert not hasattr(container, 'chat_llm')

        # 关闭
        await shutdown_container()


@pytest.mark.asyncio
async def test_cli_lifecycle():
    """测试 CLI 模式的完整生命周期。"""
    from graphedu.common.resource import try_get_container, shutdown_container, ContainerMode

    # 初始化
    container = await try_get_container(ContainerMode.CLI)
    assert container is not None

    # 验证只有 async_executor
    assert hasattr(container, 'async_executor')
    assert not hasattr(container, 'postgresql_client')

    # 关闭
    await shutdown_container()


@pytest.mark.asyncio
async def test_container_singleton():
    """测试容器单例模式。"""
    from graphedu.common.resource import try_get_container, shutdown_container, ContainerMode
    from unittest.mock import patch, MagicMock

    # 创建 mock 配置
    mock_config = MagicMock()
    mock_config.datasource.postgresql.dsn = "postgresql+psycopg://test:test@localhost:5432/test"
    mock_config.datasource.postgresql.echo = False

    with patch('graphedu.common.resource.container.get_config', return_value=mock_config):
        # 第一次初始化
        container1 = await try_get_container(ContainerMode.GENERATOR)
        # 第二次获取
        container2 = await try_get_container(ContainerMode.GENERATOR)

        # 应该是同一个实例
        assert container1 is container2

        # 关闭
        await shutdown_container()


@pytest.mark.asyncio
async def test_multiple_shutdowns():
    """测试多次关闭容器不会报错。"""
    from graphedu.common.resource import try_get_container, shutdown_container, ContainerMode

    # 初始化
    await try_get_container(ContainerMode.CLI)

    # 第一次关闭
    await shutdown_container()

    # 第二次关闭（不应该报错）
    await shutdown_container()
