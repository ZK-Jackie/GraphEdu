"""Pytest configuration and shared fixtures."""

from datetime import UTC
from unittest.mock import MagicMock

from httpx import ASGITransport, AsyncClient
import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """Create an instance of the default event loop policy."""
    import asyncio

    return (
        asyncio.WindowsSelectorEventLoopPolicy()
        if hasattr(asyncio, "WindowsSelectorEventLoopPolicy")
        else asyncio.DefaultEventLoopPolicy()
    )


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-1",
        "username": "testuser",
        "email": "test@example.com",
    }


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary for testing."""
    return {
        "app": {
            "name": "graphedu",
            "version": "0.1.0",
            "debug": True,
        },
        "database": {
            "url": "mongodb://localhost:27017/test_db",
        },
        "redis": {
            "url": "redis://localhost:6379/0",
        },
    }


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    import logging

    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    import tempfile

    fd, path = tempfile.mkstemp(dir=tmp_path)
    yield path
    import os

    os.close(fd)
    os.remove(path)


@pytest.fixture
def mock_async_client():
    """Mock async HTTP client for testing API endpoints."""
    return AsyncClient(transport=ASGITransport(app=None), base_url="http://test")


@pytest.fixture
async def async_client():
    """Async HTTP client for integration tests."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def mock_mongo():
    """Mock MongoDB connection for testing."""
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    mock.database.name = "test_db"
    mock.client.close = AsyncMock()
    return mock


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis connection for testing."""
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture(scope="function")
def mock_llm():
    """Mock LLM client for testing."""
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value="Test response")
    mock.abatch = AsyncMock(return_value=["Test response"])
    return mock


@pytest.fixture
def faker():
    """Faker instance for generating test data."""
    from faker import Faker

    return Faker()


@pytest.fixture
def freeze_time(monkeypatch):
    """Fixture to freeze time for testing."""

    class FrozenTime:
        def __init__(self):
            from datetime import datetime

            self.frozen_time = datetime.now(UTC)

        def now(self, tz=None):
            return self.frozen_time if tz is None else self.frozen_time

    frozen = FrozenTime()

    import time

    original_time = time.time
    original_datetime = __import__("datetime").datetime

    monkeypatch.setattr(time, "time", lambda: original_time())
    monkeypatch.setattr(original_datetime, "now", lambda tz=None: frozen.frozen_time)

    return frozen


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    yield
    # Cleanup code here if needed


@pytest.fixture
def capture_logs(caplog):
    """Capture logs for testing."""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog
