"""PostgreSQL + pgvector vector store implementation for GraphRAG."""

from __future__ import annotations

import json
import logging
from typing import Any

from graphrag_vectors import (
    AndExpr,
    Condition,
    FilterExpr,
    NotExpr,
    Operator,
    OrExpr,
    TextEmbedder,
    VectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)
import numpy as np
from pgvector.psycopg import register_vector
import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

log = logging.getLogger(__name__)


def _filter_to_sql(expr: FilterExpr) -> tuple[str, list[Any]]:
    """Translate a FilterExpr tree into a SQL fragment and parameter list.

    Only fields present in the ``data`` JSONB column are supported.
    Returns ``("TRUE", [])`` when *expr* is None.
    """
    if expr is None:
        return "TRUE", []

    if isinstance(expr, Condition):
        return _condition_to_sql(expr)

    if isinstance(expr, AndExpr):
        parts, params = [], []
        for sub in expr.and_:
            sql, p = _filter_to_sql(sub)
            parts.append(f"({sql})")
            params.extend(p)
        return " AND ".join(parts) or "TRUE", params

    if isinstance(expr, OrExpr):
        parts, params = [], []
        for sub in expr.or_:
            sql, p = _filter_to_sql(sub)
            parts.append(f"({sql})")
            params.extend(p)
        return " OR ".join(parts) or "TRUE", params

    if isinstance(expr, NotExpr):
        sql, params = _filter_to_sql(expr.not_)
        return f"NOT ({sql})", params

    # Fallback – unknown node type; skip the filter
    return "TRUE", []


def _condition_to_sql(cond: Condition) -> tuple[str, list[Any]]:
    """Convert a single Condition to SQL targeting the ``data`` JSONB column."""
    # We use positional %s params; cast via JSONB path extraction
    col = f"(data->>'{cond.field}')"

    match cond.operator:
        case Operator.eq:
            return f"{col} = %s", [str(cond.value)]
        case Operator.ne:
            return f"{col} <> %s", [str(cond.value)]
        case Operator.gt:
            return f"({col})::numeric > %s", [cond.value]
        case Operator.gte:
            return f"({col})::numeric >= %s", [cond.value]
        case Operator.lt:
            return f"({col})::numeric < %s", [cond.value]
        case Operator.lte:
            return f"({col})::numeric <= %s", [cond.value]
        case Operator.contains:
            return f"{col} LIKE %s", [f"%{cond.value}%"]
        case Operator.startswith:
            return f"{col} LIKE %s", [f"{cond.value}%"]
        case Operator.endswith:
            return f"{col} LIKE %s", [f"%{cond.value}"]
        case Operator.in_:
            placeholders = ", ".join(["%s"] * len(cond.value))
            return f"{col} IN ({placeholders})", list(cond.value)
        case Operator.not_in:
            placeholders = ", ".join(["%s"] * len(cond.value))
            return f"{col} NOT IN ({placeholders})", list(cond.value)
        case Operator.exists:
            if cond.value:
                return "data ? %s", [cond.field]
            return "NOT (data ? %s)", [cond.field]
        case _:
            return "TRUE", []


def _row_to_document(
    row: dict[str, Any],
    include_vectors: bool = True,
    select: list[str] | None = None,
) -> VectorStoreDocument:
    """Convert a database row dict to a VectorStoreDocument."""
    data: dict[str, Any] = row.get("data") or {}
    if select:
        data = {k: v for k, v in data.items() if k in select}

    vector = None
    if include_vectors and row.get("vector") is not None:
        raw = row["vector"]
        # pgvector returns a numpy array via register_vector
        if isinstance(raw, np.ndarray):
            vector = raw.tolist()
        else:
            vector = list(raw)

    return VectorStoreDocument(
        id=row["id"],
        vector=vector,
        data=data,
        create_date=row.get("create_date"),
        update_date=row.get("update_date"),
    )


class PostgresVectorStore(VectorStore):
    """pgvector-backed vector store for GraphRAG.

    Uses PostgreSQL with the ``pgvector`` extension and psycopg (psycopg3).
    Connections are managed via a ``psycopg_pool.ConnectionPool``, making the
    store safe for concurrent use across multiple threads / async tasks.

    Similarity search uses **cosine distance** (``<=>`` operator).

    **Task isolation**
    Each pipeline run *must* use a unique *namespace* so that vector indexes
    from different tasks never collide.  The effective partition key stored in
    the ``index_name`` column is built as::

        "{namespace}__{index_name}"   # namespace set  → "project_42__entities"
        "{index_name}"                # no namespace   → tasks WILL collide!

    Always pass a task-scoped namespace::

        store = PostgresVectorStore(
            connection_string="postgresql://user:pass@host/db",
            namespace="project_42",   # unique per pipeline run
            index_name="entities",
        )
        # effective index_name stored in DB: "project_42__entities"

    Configuration example (settings.yml)::

        vector_store:
          type: pgvector
          connection_string: "postgresql://user:pass@host:5432/dbname"
          namespace: "project_42"     # required for multi-task isolation
          # VectorStore base-class options (all optional):
          # vector_size: 1536
          # index_name: entities

    The table is created automatically on ``create_index()``.
    An HNSW partial index is created per namespace for approximate
    nearest-neighbour search.
    """

    def __init__(
        self,
        connection_string: str = "",
        table_name: str = "graphrag_vectors",
        namespace: str = "",
        pool_size: int = 5,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._connection_string = connection_string
        self._table_name = table_name
        self._namespace = namespace
        self._pool_size = pool_size
        self._pool: ConnectionPool | None = None

    # ------------------------------------------------------------------
    # VectorStore interface
    # ------------------------------------------------------------------

    def connect(self, **kwargs: Any) -> None:
        """Open a connection pool.

        ``register_vector`` is applied to every connection via the pool's
        *configure* callback, so callers never need to do it manually.
        """
        if not self._connection_string:
            msg = "A connection_string must be provided."
            raise RuntimeError(msg)

        if self._pool is not None and not self._pool.closed:
            return  # already open

        def _configure(conn: psycopg.Connection) -> None:
            register_vector(conn)
            conn.autocommit = True

        log.debug("Opening psycopg ConnectionPool for PostgresVectorStore.")
        self._pool = ConnectionPool(
            conninfo=self._connection_string,
            min_size=1,
            max_size=self._pool_size,
            open=True,
            configure=_configure,
            kwargs={"row_factory": dict_row},
        )

    def create_index(self, **kwargs: Any) -> None:
        """Create the shared vector table and a per-namespace partial HNSW index."""
        if self._pool is None:
            msg = "Call connect() before create_index()."
            raise RuntimeError(msg)

        tbl = self._table
        idx_key = self._index_key
        # Sanitize the index_key for use in an SQL identifier
        safe_idx = "".join(c if c.isalnum() or c == "_" else "_" for c in idx_key)
        hnsw_idx_name = f"{tbl}_{safe_idx}_hnsw_idx"

        with self._pool.connection() as conn, conn.cursor() as cur:
            # Ensure the pgvector extension is available
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create the shared documents table (once per physical table)
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {tbl} (
                    index_name  TEXT        NOT NULL,
                    id          TEXT        NOT NULL,
                    vector      VECTOR({self.vector_size}),
                    data        JSONB       DEFAULT '{{}}',
                    create_date TEXT,
                    update_date TEXT,
                    PRIMARY KEY (index_name, id)
                )
                """
            )

            # Create a partial HNSW index scoped to this namespace
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {hnsw_idx_name}
                ON {tbl} USING hnsw (vector vector_cosine_ops)
                WHERE index_name = '{idx_key}'
                """
            )

    def insert(self, document: VectorStoreDocument) -> None:
        """Insert a single document; raises ValueError if the ID already exists."""
        self._prepare_document(document)
        try:
            self._upsert(document, on_conflict="raise")
        except UniqueViolation as exc:
            msg = f"Document with id '{document.id}' already exists in '{self._index_key}'."
            raise ValueError(msg) from exc

    def update(self, document: VectorStoreDocument) -> None:
        """Update an existing document in the store."""
        self._prepare_update(document)
        self._upsert(document, on_conflict="update")

    def _upsert(
        self,
        document: VectorStoreDocument,
        on_conflict: str = "update",
    ) -> None:
        if self._pool is None:
            msg = "Call connect() before writing documents."
            raise RuntimeError(msg)

        vector = np.array(document.vector, dtype=np.float32) if document.vector else None
        data_json = json.dumps(document.data or {})

        tbl = self._table
        idx_key = self._index_key
        if on_conflict == "update":
            sql = f"""
                INSERT INTO {tbl} (index_name, id, vector, data, create_date, update_date)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (index_name, id)
                DO UPDATE SET vector      = EXCLUDED.vector,
                              data        = EXCLUDED.data,
                              create_date = EXCLUDED.create_date,
                              update_date = EXCLUDED.update_date
            """
        else:
            sql = f"""
                INSERT INTO {tbl} (index_name, id, vector, data, create_date, update_date)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            """

        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    idx_key,
                    str(document.id),
                    vector,
                    data_json,
                    document.create_date,
                    document.update_date,
                ),
            )

    def load_documents(
        self,
        documents: list[VectorStoreDocument],
        overwrite: bool = False,
    ) -> None:
        """Bulk-load documents using executemany, optionally clearing first."""
        if self._pool is None:
            msg = "Call connect() before load_documents()."
            raise RuntimeError(msg)

        tbl = self._table
        idx_key = self._index_key
        upsert_sql = f"""
            INSERT INTO {tbl} (index_name, id, vector, data, create_date, update_date)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (index_name, id)
            DO UPDATE SET vector      = EXCLUDED.vector,
                          data        = EXCLUDED.data,
                          create_date = EXCLUDED.create_date,
                          update_date = EXCLUDED.update_date
        """

        rows = []
        for doc in documents:
            self._prepare_document(doc)
            vector = np.array(doc.vector, dtype=np.float32) if doc.vector else None
            rows.append((
                idx_key,
                str(doc.id),
                vector,
                json.dumps(doc.data or {}),
                doc.create_date,
                doc.update_date,
            ))

        with self._pool.connection() as conn, conn.cursor() as cur:
            if overwrite:
                cur.execute(
                    f"DELETE FROM {tbl} WHERE index_name = %s",
                    (idx_key,),
                )
            if rows:
                cur.executemany(upsert_sql, rows)

    def similarity_search_by_vector(
        self,
        query_embedding: list[float],
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
        **kwargs: Any,
    ) -> list[VectorStoreSearchResult]:
        """Return the *k* most similar documents to *query_embedding*.

        *filters* is translated to a SQL WHERE clause on the ``data`` JSONB
        column. ``select`` restricts which ``data`` keys are returned.
        """
        if self._pool is None:
            msg = "Call connect() before searching."
            raise RuntimeError(msg)

        query_vec = np.array(query_embedding, dtype=np.float32)

        vector_col = "vector" if include_vectors else "NULL::vector AS vector"
        filter_sql, filter_params = _filter_to_sql(filters)

        tbl = self._table
        idx_key = self._index_key
        # Use CTE so query_vec is passed only once; ORDER BY reuses the
        # already-computed `score` column instead of recalculating <=>.
        sql = f"""
            WITH scored AS (
                SELECT id,
                       {vector_col},
                       data,
                       create_date,
                       update_date,
                       1 - (vector <=> %s::vector) AS score
                FROM   {tbl}
                WHERE  index_name = %s
                  AND  {filter_sql}
            )
            SELECT * FROM scored
            ORDER  BY score DESC
            LIMIT  %s
        """

        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, [query_vec, idx_key, *filter_params, k])
            rows = cur.fetchall()

        return [
            VectorStoreSearchResult(
                document=_row_to_document(row, include_vectors, select),
                score=float(row["score"]),
            )
            for row in rows
        ]

    def similarity_search_by_text(
        self,
        text: str,
        text_embedder: TextEmbedder,
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
        **kwargs: Any,
    ) -> list[VectorStoreSearchResult]:
        """Embed *text* and delegate to similarity_search_by_vector."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding,
                k=k,
                select=select,
                filters=filters,
                include_vectors=include_vectors,
            )
        return []

    def search_by_id(
        self,
        id: str,
        select: list[str] | None = None,
        include_vectors: bool = True,
    ) -> VectorStoreDocument:
        """Retrieve a document by its primary-key ID.

        Returns a document with ``vector=None`` and ``data={}`` when the ID
        does not exist (consistent with CosmosDB reference implementation).
        """
        if self._pool is None:
            msg = "Call connect() before searching."
            raise RuntimeError(msg)

        vector_col = "vector" if include_vectors else "NULL::vector AS vector"
        tbl = self._table
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT id, {vector_col}, data, create_date, update_date FROM {tbl} WHERE index_name = %s AND id = %s",
                (self._index_key, id),
            )
            row = cur.fetchone()

        if row is None:
            return VectorStoreDocument(id=id, vector=None, data={})

        return _row_to_document(row, include_vectors, select)

    def count(self) -> int:
        """Return the total number of documents in the store."""
        if self._pool is None:
            msg = "Call connect() before counting."
            raise RuntimeError(msg)

        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS n FROM {self._table} WHERE index_name = %s",
                (self._index_key,),
            )
            row = cur.fetchone()
        return int(row["n"]) if row else 0

    def remove(self, ids: list[str]) -> None:
        """Delete documents by ID list."""
        if self._pool is None:
            msg = "Call connect() before removing documents."
            raise RuntimeError(msg)
        if not ids:
            return

        placeholders = ", ".join(["%s"] * len(ids))
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE index_name = %s AND id IN ({placeholders})",
                [self._index_key, *ids],
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _table(self) -> str:
        """Sanitised physical table name (shared across all namespaces)."""
        return "".join(c if c.isalnum() or c == "_" else "_" for c in self._table_name)

    @property
    def _index_key(self) -> str:
        """Effective index key combining namespace and collection index_name.

        Format: ``{namespace}__{index_name}`` when namespace is set,
        otherwise just ``{index_name}``.
        """
        if self._namespace:
            return f"{self._namespace}__{self.index_name}"
        return self.index_name
