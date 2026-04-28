"""Integration tests for database operations."""

from motor.motor_asyncio import AsyncIOMotorClient
import pytest

from graphedu.common.config import Config


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    async def test_db_config(self):
        """Create test database configuration."""
        return Config.from_dict(
            {
                "database": {
                    "url": "mongodb://localhost:27017",
                    "name": "test_graphedu",
                },
                "app": {
                    "name": "graphedu",
                    "debug": True,
                },
            }
        )

    @pytest.fixture
    async def db_client(self, test_db_config):
        """Create a test database client."""
        client = AsyncIOMotorClient(test_db_config.database.url)

        yield client

        # Cleanup
        await client.drop_database(test_db_config.database.name)
        client.close()

    @pytest.fixture
    async def db(self, db_client, test_db_config):
        """Get the test database."""
        return db_client[test_db_config.database.name]

    async def test_database_connection(self, db_client, test_db_config):
        """Test that we can connect to the database."""
        # Ping the database
        result = await db_client.admin.command("ping")

        assert result["ok"] == 1

    async def test_create_collection(self, db):
        """Test creating a collection."""
        collection = db["test_collection"]

        # Insert a document
        result = await collection.insert_one({"name": "test", "value": 123})

        assert result.inserted_id is not None

        # Verify the document was inserted
        document = await collection.find_one({"name": "test"})

        assert document is not None
        assert document["value"] == 123

    async def test_query_documents(self, db):
        """Test querying documents from the database."""
        collection = db["test_query"]

        # Insert multiple documents
        await collection.insert_many(
            [
                {"name": "doc1", "value": 1},
                {"name": "doc2", "value": 2},
                {"name": "doc3", "value": 3},
            ]
        )

        # Query documents
        cursor = collection.find({"value": {"$gt": 1}})
        results = await cursor.to_list(length=10)

        assert len(results) == 2
        assert all(doc["value"] > 1 for doc in results)

    async def test_update_document(self, db):
        """Test updating a document."""
        collection = db["test_update"]

        # Insert a document
        result = await collection.insert_one({"name": "test", "value": 1})
        doc_id = result.inserted_id

        # Update the document
        await collection.update_one({"_id": doc_id}, {"$set": {"value": 2}})

        # Verify the update
        updated_doc = await collection.find_one({"_id": doc_id})

        assert updated_doc["value"] == 2

    async def test_delete_document(self, db):
        """Test deleting a document."""
        collection = db["test_delete"]

        # Insert a document
        result = await collection.insert_one({"name": "test", "value": 1})
        doc_id = result.inserted_id

        # Delete the document
        delete_result = await collection.delete_one({"_id": doc_id})

        assert delete_result.deleted_count == 1

        # Verify the document was deleted
        deleted_doc = await collection.find_one({"_id": doc_id})

        assert deleted_doc is None

    async def test_transaction_operations(self, db):
        """Test database transactions."""
        collection = db["test_transactions"]

        # Start a session
        async with await db.client.start_session() as session, session.start_transaction():
            # Insert documents within transaction
            await collection.insert_many(
                [
                    {"name": "doc1", "value": 1},
                    {"name": "doc2", "value": 2},
                ],
                session=session,
            )

            # Verify documents within transaction
            count = await collection.count_documents({}, session=session)

            assert count == 2

                # Transaction will be committed on exit

        # Verify documents after transaction
        count = await collection.count_documents({})

        assert count == 2

    async def test_index_creation(self, db):
        """Test creating indexes."""
        collection = db["test_indexes"]

        # Create an index
        await collection.create_index([("name", 1)], unique=True)

        # Get index information
        indexes = await collection.index_information()

        assert "name_1" in indexes

    async def test_aggregation_pipeline(self, db):
        """Test aggregation pipeline."""
        collection = db["test_aggregation"]

        # Insert test data
        await collection.insert_many(
            [
                {"category": "A", "value": 10},
                {"category": "A", "value": 20},
                {"category": "B", "value": 30},
            ]
        )

        # Run aggregation
        pipeline = [
            {"$group": {"_id": "$category", "total": {"$sum": "$value"}}},
            {"$sort": {"_id": 1}},
        ]

        results = await collection.aggregate(pipeline).to_list(length=10)

        assert len(results) == 2
        assert results[0]["total"] == 30
        assert results[1]["total"] == 30


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
class TestRedisIntegration:
    """Integration tests for Redis operations."""

    @pytest.fixture
    async def redis_client(self):
        """Create a test Redis client."""
        import redis.asyncio as redis

        client = redis.Redis(host="localhost", port=6379, db=15, decode_responses=True)

        # Clear the test database
        await client.flushdb()

        yield client

        await client.close()

    async def test_redis_connection(self, redis_client):
        """Test that we can connect to Redis."""
        result = await redis_client.ping()

        assert result is True

    async def test_set_and_get(self, redis_client):
        """Test setting and getting values."""
        await redis_client.set("test_key", "test_value")

        value = await redis_client.get("test_key")

        assert value == "test_value"

    async def test_set_with_expiry(self, redis_client):
        """Test setting a value with expiration."""
        await redis_client.setex("expiring_key", 1, "test_value")

        # Value should exist immediately
        value = await redis_client.get("expiring_key")

        assert value is not None

        # Wait for expiration
        import asyncio

        await asyncio.sleep(1.1)

        # Value should be expired
        value = await redis_client.get("expiring_key")

        assert value is None

    async def test_delete(self, redis_client):
        """Test deleting keys."""
        await redis_client.set("test_key", "test_value")

        result = await redis_client.delete("test_key")

        assert result == 1

        value = await redis_client.get("test_key")

        assert value is None

    async def test_list_operations(self, redis_client):
        """Test Redis list operations."""
        # Push values to list
        await redis_client.rpush("test_list", "value1", "value2", "value3")

        # Get list length
        length = await redis_client.llen("test_list")

        assert length == 3

        # Get range of values
        values = await redis_client.lrange("test_list", 0, -1)

        assert values == ["value1", "value2", "value3"]

    async def test_hash_operations(self, redis_client):
        """Test Redis hash operations."""
        # Set hash fields
        await redis_client.hset("test_hash", "field1", "value1")
        await redis_client.hset("test_hash", "field2", "value2")

        # Get single field
        value = await redis_client.hget("test_hash", "field1")

        assert value == "value1"

        # Get all fields
        all_fields = await redis_client.hgetall("test_hash")

        assert len(all_fields) == 2
        assert all_fields["field1"] == "value1"
        assert all_fields["field2"] == "value2"
