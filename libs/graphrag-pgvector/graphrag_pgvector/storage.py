"""PostgreSQL storage implementation for GraphRAG."""

from collections.abc import Iterator
import json
import logging
import re
from typing import Any
import warnings

from graphrag_storage import Storage
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

log = logging.getLogger(__name__)


class PostgresStorage(Storage):
    """PostgreSQL-backed storage implementation.

    Stores key/value pairs in a single PostgreSQL table using psycopg (psycopg3).
    Values are stored as BYTEA and decoded on retrieval if needed.

    **Task isolation**
    Every GraphRAG pipeline run (task) *must* receive a unique *namespace* so
    that artefacts from different tasks never overwrite each other.  Use the
    project or task ID as the namespace::

        storage = PostgresStorage(
            connection_string="postgresql://user:pass@host/db",
            namespace="project_42",   # unique per pipeline run
        )

    Child namespaces created via :meth:`child` inherit this prefix
    automatically, so every pipeline sub-directory is scoped to the same task.
    When *namespace* is omitted (default ``""``), all tasks share the same key
    space and **will collide**.

    Configuration example (settings.yml)::

        storage:
          type: pgvector
          connection_string: "postgresql://user:pass@host:5432/dbname"
          table_name: graphrag_storage   # optional, default: graphrag_storage
          namespace: "project_42"        # required for multi-task isolation
    """

    def __init__(
        self,
        connection_string: str = "",
        table_name: str = "graphrag_storage",
        namespace: str = "",
        async_conn: psycopg.AsyncConnection | None = None,
        **kwargs: Any,
    ) -> None:
        self._connection_string = connection_string
        self._table_name = table_name
        self._namespace = namespace
        self._async_conn: psycopg.AsyncConnection | None = async_conn
        self._table_initialized = False
        self._sync_pool: ConnectionPool | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_async_conn(self) -> psycopg.AsyncConnection:
        """Return a healthy async connection, ensuring the table exists.

        If an *async_conn* was supplied at construction time and is still open,
        it is re-used after a lightweight probe.  If the probe fails (or the
        connection is already closed) a warning is emitted and a new connection
        is opened via *connection_string*.
        """
        if self._async_conn is not None and not self._async_conn.closed:
            try:
                async with self._async_conn.cursor() as cur:
                    await cur.execute("SELECT 1")
            except Exception as exc:
                warnings.warn(
                    f"Passed psycopg.AsyncConnection failed health-check ({exc}); falling back to connection_string.",
                    RuntimeWarning,
                    stacklevel=3,
                )
                self._async_conn = None
                self._table_initialized = False

        if self._async_conn is None or self._async_conn.closed:
            if not self._connection_string:
                msg = "Neither a valid async_conn nor a connection_string was provided."
                raise RuntimeError(msg)
            log.debug("Opening new async psycopg connection for PostgresStorage.")
            self._async_conn = await psycopg.AsyncConnection.connect(
                self._connection_string,
                autocommit=True,
                row_factory=dict_row,
            )
            self._table_initialized = False

        if not self._table_initialized:
            await self._create_table(self._async_conn)
            self._table_initialized = True

        return self._async_conn

    async def _create_table(self, conn: psycopg.AsyncConnection) -> None:
        """Create the storage table (single shared table) if it does not exist."""
        tbl = self._table
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {tbl} (
                    namespace  TEXT        NOT NULL DEFAULT '',
                    key        TEXT        NOT NULL,
                    value      BYTEA,
                    encoding   TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (namespace, key)
                )
                """
            )
            await cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {tbl}_namespace_idx
                ON {tbl} (namespace)
                """
            )

    def _sync_conn(self) -> ConnectionPool:
        """Return the shared synchronous connection pool, creating it on first call."""
        if self._sync_pool is None or self._sync_pool.closed:
            if not self._connection_string:
                msg = "A connection_string must be provided for synchronous operations."
                raise RuntimeError(msg)
            tbl = self._table

            def _init(conn: psycopg.Connection) -> None:
                """Ensure the table exists on every fresh connection."""
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {tbl} (
                            namespace  TEXT        NOT NULL DEFAULT '',
                            key        TEXT        NOT NULL,
                            value      BYTEA,
                            encoding   TEXT,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            PRIMARY KEY (namespace, key)
                        )
                        """
                    )
                    cur.execute(
                        f"""
                        CREATE INDEX IF NOT EXISTS {tbl}_namespace_idx
                        ON {tbl} (namespace)
                        """
                    )
                conn.commit()

            self._sync_pool = ConnectionPool(
                conninfo=self._connection_string,
                min_size=1,
                max_size=3,
                open=True,
                configure=_init,
                kwargs={"row_factory": dict_row},
            )
        return self._sync_pool

    # ------------------------------------------------------------------
    # Async interface
    # ------------------------------------------------------------------

    async def get(
        self,
        key: str,
        as_bytes: bool | None = None,
        encoding: str | None = None,
    ) -> Any:
        """Retrieve a stored value by key."""
        conn = await self._ensure_async_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                f"SELECT value, encoding FROM {self._table} WHERE namespace = %s AND key = %s",
                (self._namespace, key),
            )
            row = await cur.fetchone()

        if row is None:
            return None

        raw: bytes = bytes(row["value"]) if row["value"] is not None else b""

        if as_bytes:
            return raw

        enc = encoding or row["encoding"] or "utf-8"
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            return raw

    async def set(
        self,
        key: str,
        value: Any,
        encoding: str | None = None,
    ) -> None:
        """Store a value with the given key."""
        conn = await self._ensure_async_conn()

        if isinstance(value, bytes):
            data = value
        elif isinstance(value, str):
            data = value.encode(encoding or "utf-8")
        else:
            data = json.dumps(value, ensure_ascii=False).encode("utf-8")
            encoding = "utf-8"

        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                INSERT INTO {self._table} (namespace, key, value, encoding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (namespace, key)
                DO UPDATE SET value    = EXCLUDED.value,
                              encoding = EXCLUDED.encoding
                """,
                (self._namespace, key, data, encoding),
            )

    async def has(self, key: str) -> bool:
        """Return True if *key* exists in the storage."""
        conn = await self._ensure_async_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                f"SELECT 1 FROM {self._table} WHERE namespace = %s AND key = %s",
                (self._namespace, key),
            )
            return await cur.fetchone() is not None

    async def delete(self, key: str) -> None:
        """Delete a key from storage."""
        conn = await self._ensure_async_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                f"DELETE FROM {self._table} WHERE namespace = %s AND key = %s",
                (self._namespace, key),
            )

    async def clear(self) -> None:
        """Delete all rows in the current namespace (does not affect other namespaces)."""
        conn = await self._ensure_async_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                f"DELETE FROM {self._table} WHERE namespace = %s",
                (self._namespace,),
            )

    async def get_creation_date(self, key: str) -> str:
        """Return the ISO-8601 creation timestamp for *key*, or empty string."""
        conn = await self._ensure_async_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                f"SELECT created_at FROM {self._table} WHERE namespace = %s AND key = %s",
                (self._namespace, key),
            )
            row = await cur.fetchone()

        if row and row["created_at"]:
            return row["created_at"].isoformat()
        return ""

    # ------------------------------------------------------------------
    # Sync interface
    # ------------------------------------------------------------------

    def find(
        self,
        file_pattern: re.Pattern[str],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> Iterator[str]:
        """Return an iterator over keys matching *file_pattern*.

        Uses PostgreSQL POSIX regex (``~`` operator) to push filtering to the
        database rather than fetching all keys and filtering in Python.
        """
        conditions = ["namespace = %s", "key ~ %s"]
        params: list[Any] = [self._namespace, file_pattern.pattern]
        if prefix:
            conditions.append("key LIKE %s")
            params.append(f"{prefix}%")
        if suffix:
            conditions.append("key LIKE %s")
            params.append(f"%{suffix}")

        where = " AND ".join(conditions)
        with self._sync_conn().connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT key FROM {self._table} WHERE {where}",
                params,
            )
            return iter([row["key"] for row in cur.fetchall()])

    def keys(self) -> list[str]:
        """Return all keys in the current namespace (synchronous)."""
        with self._sync_conn().connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT key FROM {self._table} WHERE namespace = %s",
                (self._namespace,),
            )
            return [row["key"] for row in cur.fetchall()]

    def child(self, name: str | None = None) -> "PostgresStorage":
        """Return a child storage scoped to a derived namespace.

        All children share the same physical table and database connection as
        the parent.  Namespaces nest with ``/`` as separator so
        ``parent.child("entities")`` yields namespace ``"{parent_ns}/entities"``.
        """
        if name:
            child_ns = f"{self._namespace}/{name}" if self._namespace else name
            child = PostgresStorage(
                connection_string=self._connection_string,
                table_name=self._table_name,
                namespace=child_ns,
                async_conn=self._async_conn,
            )
            # Share the sync pool only when it is already initialised.
            # Unconditional assignment would capture None when child() is called
            # before the first _sync_conn() invocation, causing the child to
            # never benefit from the shared pool (it would create its own).
            if self._sync_pool is not None:
                child._sync_pool = self._sync_pool
            return child
        return self

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _table(self) -> str:
        """Sanitised physical table name safe for use in SQL identifiers."""
        return "".join(c if c.isalnum() or c == "_" else "_" for c in self._table_name)
