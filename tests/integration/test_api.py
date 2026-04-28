"""Integration tests for API endpoints."""

from httpx import AsyncClient
import pytest


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    async def app(self):
        """Create the FastAPI application for testing."""
        from graphedu.api.app import create_app

        config = {
            "app": {
                "name": "graphedu",
                "debug": True,
            },
            "database": {
                "url": "mongodb://localhost:27017/test_graphedu",
            },
        }

        return create_app(config)

    @pytest.fixture
    async def client(self, app):
        """Create an async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_health_check(self, client):
        """Test the health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "healthy"

    async def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200

        data = response.json()

        assert "name" in data
        assert "version" in data

    async def test_create_user(self, client):
        """Test creating a new user via API."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
        }

        response = await client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201

        data = response.json()

        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "password" not in data  # Password should not be returned

    async def test_get_user(self, client):
        """Test retrieving a user via API."""
        # First create a user
        user_data = {
            "username": "getuser",
            "email": "getuser@example.com",
            "password": "password123",
        }

        create_response = await client.post("/api/v1/users", json=user_data)

        assert create_response.status_code == 201

        user_id = create_response.json()["id"]

        # Now retrieve the user
        response = await client.get(f"/api/v1/users/{user_id}")

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == user_id
        assert data["username"] == "getuser"

    async def test_update_user(self, client):
        """Test updating a user via API."""
        # Create a user
        user_data = {
            "username": "updateuser",
            "email": "updateuser@example.com",
            "password": "password123",
        }

        create_response = await client.post("/api/v1/users", json=user_data)

        user_id = create_response.json()["id"]

        # Update the user
        update_data = {"email": "newemail@example.com"}

        response = await client.patch(f"/api/v1/users/{user_id}", json=update_data)

        assert response.status_code == 200

        data = response.json()

        assert data["email"] == "newemail@example.com"
        assert data["username"] == "updateuser"  # Username unchanged

    async def test_delete_user(self, client):
        """Test deleting a user via API."""
        # Create a user
        user_data = {
            "username": "deleteuser",
            "email": "deleteuser@example.com",
            "password": "password123",
        }

        create_response = await client.post("/api/v1/users", json=user_data)

        user_id = create_response.json()["id"]

        # Delete the user
        response = await client.delete(f"/api/v1/users/{user_id}")

        assert response.status_code == 204

        # Verify user is deleted
        get_response = await client.get(f"/api/v1/users/{user_id}")

        assert get_response.status_code == 404

    async def test_list_users(self, client):
        """Test listing users via API."""
        # Create multiple users
        for i in range(3):
            user_data = {
                "username": f"listuser{i}",
                "email": f"listuser{i}@example.com",
                "password": "password123",
            }

            await client.post("/api/v1/users", json=user_data)

        # List users
        response = await client.get("/api/v1/users")

        assert response.status_code == 200

        data = response.json()

        assert "users" in data
        assert len(data["users"]) >= 3

    async def test_authentication(self, client):
        """Test user authentication via API."""
        # Create a user
        user_data = {
            "username": "authuser",
            "email": "authuser@example.com",
            "password": "password123",
        }

        await client.post("/api/v1/users", json=user_data)

        # Login
        login_data = {"username": "authuser", "password": "password123"}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200

        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_invalid_credentials(self, client):
        """Test authentication with invalid credentials."""
        login_data = {"username": "nonexistent", "password": "wrongpassword"}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_protected_endpoint_without_auth(self, client):
        """Test accessing a protected endpoint without authentication."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_protected_endpoint_with_auth(self, client):
        """Test accessing a protected endpoint with authentication."""
        # Create and login a user
        user_data = {
            "username": "protecteduser",
            "email": "protecteduser@example.com",
            "password": "password123",
        }

        await client.post("/api/v1/users", json=user_data)

        login_data = {"username": "protecteduser", "password": "password123"}

        login_response = await client.post("/api/v1/auth/login", json=login_data)

        token = login_response.json()["access_token"]

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200

        data = response.json()

        assert data["username"] == "protecteduser"

    async def test_validation_error(self, client):
        """Test input validation on API endpoints."""
        invalid_data = {
            "username": "",  # Empty username
            "email": "invalid-email",  # Invalid email format
            "password": "short",  # Password too short
        }

        response = await client.post("/api/v1/users", json=invalid_data)

        assert response.status_code == 422

        data = response.json()

        assert "detail" in data


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
class TestLLMIntegration:
    """Integration tests for LLM functionality."""

    @pytest.fixture
    async def llm_client(self):
        """Create an LLM client for testing."""
        from graphedu.common.utils.llm import get_llm_client

        config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "test-key",
                "temperature": 0.7,
            }
        }

        return get_llm_client(config)

    async def test_llm_generate(self, llm_client):
        """Test LLM text generation."""
        from unittest.mock import AsyncMock, patch

        # Mock the LLM call
        with patch.object(llm_client, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "Test response"

            response = await llm_client.ainvoke("Test prompt")

            assert response == "Test response"
            mock_invoke.assert_called_once()

    async def test_llm_stream(self, llm_client):
        """Test LLM streaming response."""
        from unittest.mock import AsyncMock, patch

        async def mock_stream():
            chunks = ["Hello", " world", "!"]
            for chunk in chunks:
                yield chunk

        with patch.object(llm_client, "astream", new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = mock_stream()

            chunks = []
            async for chunk in llm_client.astream("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]
