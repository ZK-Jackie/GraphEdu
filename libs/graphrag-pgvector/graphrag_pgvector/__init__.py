"""Graphrag pgvector integration."""
from graphrag_pgvector.config import PgVectorStoreConfig
from graphrag_pgvector.storage import PostgresStorage
from graphrag_pgvector.vector_store import PostgresVectorStore


def register_graphrag_pgvector_storage() -> None:
    """Register the PostgreSQL KV storage implementation with graphrag.

    Must be called explicitly before using ``type: pgvector`` in storage config.
    """
    from graphrag_storage import register_storage

    register_storage("pgvector", PostgresStorage)


def register_graphrag_pgvector() -> None:
    """Register both the PostgreSQL storage and vector store implementations.

    Must be called explicitly before using ``type: pgvector`` in settings.yml.
    """
    from graphrag_vectors import register_vector_store

    register_vector_store("pgvector", PostgresVectorStore)


__all__ = ["PgVectorStoreConfig", "PostgresStorage", "PostgresVectorStore", "register_graphrag_pgvector", "register_graphrag_pgvector_storage"]
