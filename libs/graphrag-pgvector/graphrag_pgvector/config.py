"""Config for pgvector vector store."""
from graphrag_storage import StorageConfig
from graphrag_vectors import VectorStoreConfig
import psycopg
from pydantic import ConfigDict


class PgVectorStoreConfig(VectorStoreConfig):
    """Configuration for the pgvector vector store."""

    table_name: str = "public.graphrag_pgvector"
    """The name of the table to store the vectors in."""

    namespace: str = "default"
    """The namespace to store the vectors in.
    This can be used to logically separate different sets of vectors within the same table."""

    async_conn: psycopg.AsyncConnection | None = None
    """An optional async connection to the PostgreSQL database.
    If not provided, a new connection will be created for each operation.
    Providing a connection can improve performance by reusing the same connection across multiple operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")


class PgStorageConfig(StorageConfig):
    """Configuration for the pgvector storage."""

    table_name: str = "graphrag.pgvector_storage"
    """The name of the table to store the data in."""

    namespace: str = "default"
    """The namespace to store the data in.
    This can be used to logically separate different sets of data within the same table."""

    async_conn: psycopg.AsyncConnection | None = None
    """An optional async connection to the PostgreSQL database.
    If not provided, a new connection will be created for each operation.
    Providing a connection can improve performance by reusing the same connection across multiple operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
