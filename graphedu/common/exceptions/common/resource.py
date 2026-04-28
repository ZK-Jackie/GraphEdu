"""Resource layer exceptions

Contains database, cache, storage, graph database, HTTP client, and other resource-related exceptions.
All exceptions inherit directly from Exception and support message interpolation.
"""

from graphedu.common.exceptions.base import AppException

# ============================================================================
# Base resource exception
# ============================================================================


class ResourceException(AppException):
    """Base exception for all resource-related errors"""

    def __init__(self, message: str = None, **kwargs):
        """Initialize resource exception

        Args:
            message: Error message template (can contain placeholders for formatting)
            **kwargs: Parameters for message interpolation (e.g., db_type="PostgreSQL", reason="timeout")
        """
        self.kwargs = kwargs

        # Format message if kwargs provided
        if message and kwargs:
            try:
                self.message = message.format(**kwargs)
            except (KeyError, ValueError):
                # If formatting fails, use original message
                self.message = message
        else:
            self.message = message or "Resource operation failed"

        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses"""
        return {"error": self.__class__.__name__, "message": self.message, "details": self.kwargs or {}}


# ============================================================================
# Database exceptions
# ============================================================================


class DatabaseException(ResourceException):
    """Base exception for database-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Database operation failed"
        super().__init__(message=message, **kwargs)


class DatabaseConnectionException(DatabaseException):
    """Database connection failure"""

    def __init__(self, db_type: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if db_type and reason:
                message = f"{db_type} database connection failed: {reason}"
            elif db_type:
                message = f"{db_type} database connection failed"
            else:
                message = "Database connection failed"

        super().__init__(message=message, db_type=db_type, reason=reason, **kwargs)


class DatabaseDisconnectedException(DatabaseException):
    """Database connection lost"""

    def __init__(self, db_type: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"{db_type} database connection lost" if db_type else "Database connection lost"

        super().__init__(message=message, db_type=db_type, **kwargs)


class DatabaseTransactionException(DatabaseException):
    """Database transaction operation failure"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"Database transaction failed: {reason}" if reason else "Database transaction failed"

        super().__init__(message=message, reason=reason, **kwargs)


class DatabaseQueryException(DatabaseException):
    """Database query execution failure"""

    def __init__(self, query: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"Database query failed: {reason}" if reason else "Database query failed"

        super().__init__(message=message, query=query, reason=reason, **kwargs)


class DatabaseExecuteException(DatabaseException):
    """Database statement execution failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Database {operation} operation failed: {reason}"
            elif operation:
                message = f"Database {operation} operation failed"
            else:
                message = "Database execution failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


class DatabasePoolExhaustedException(DatabaseException):
    """Database connection pool exhausted"""

    def __init__(self, db_type: str = None, message: str = None, **kwargs):
        if message is None:
            if db_type:
                message = f"{db_type} database connection pool exhausted"
            else:
                message = "Database connection pool exhausted"

        super().__init__(message=message, db_type=db_type, **kwargs)


class DatabaseConfigValidationException(DatabaseException):
    """Database configuration validation failure"""

    def __init__(self, config_key: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_key and reason:
                message = f"Database configuration '{config_key}' validation failed: {reason}"
            elif config_key:
                message = f"Database configuration '{config_key}' validation failed"
            else:
                message = "Database configuration validation failed"

        super().__init__(message=message, config_key=config_key, reason=reason, **kwargs)


class DatabaseSessionException(DatabaseException):
    """Database session operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Database session {operation} failed: {reason}"
            elif operation:
                message = f"Database session {operation} failed"
            else:
                message = "Database session operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


class DatabaseEngineException(DatabaseException):
    """Database engine operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Database engine {operation} failed: {reason}"
            elif operation:
                message = f"Database engine {operation} failed"
            else:
                message = "Database engine operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


# ============================================================================
# Cache exceptions
# ============================================================================


class CacheException(ResourceException):
    """Base exception for cache-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Cache operation failed"
        super().__init__(message=message, **kwargs)


class CacheConnectionException(CacheException):
    """Cache connection failure"""

    def __init__(self, cache_type: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if cache_type and reason:
                message = f"{cache_type} cache connection failed: {reason}"
            elif cache_type:
                message = f"{cache_type} cache connection failed"
            else:
                message = "Cache connection failed"

        super().__init__(message=message, cache_type=cache_type, reason=reason, **kwargs)


class CacheDisconnectedException(CacheException):
    """Cache connection lost"""

    def __init__(self, cache_type: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"{cache_type} cache connection lost" if cache_type else "Cache connection lost"

        super().__init__(message=message, cache_type=cache_type, **kwargs)


class CacheOperationException(CacheException):
    """Cache operation failure"""

    def __init__(self, operation: str = None, key: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and key and reason:
                message = f"Cache {operation} operation failed (key={key}): {reason}"
            elif operation and key:
                message = f"Cache {operation} operation failed (key={key})"
            elif operation:
                message = f"Cache {operation} operation failed"
            else:
                message = "Cache operation failed"

        super().__init__(message=message, operation=operation, key=key, reason=reason, **kwargs)


class CacheTimeoutException(CacheException):
    """Cache operation timeout"""

    def __init__(self, operation: str = None, key: str = None, timeout: float = None, message: str = None, **kwargs):
        if message is None:
            if operation and key and timeout:
                message = f"Cache {operation} operation timed out (key={key}, timeout={timeout}s)"
            elif operation and timeout:
                message = f"Cache {operation} operation timed out (timeout={timeout}s)"
            else:
                message = "Cache operation timed out"

        super().__init__(message=message, operation=operation, key=key, timeout=timeout, **kwargs)


class CacheConfigValidationException(CacheException):
    """Cache configuration validation failure"""

    def __init__(self, config_key: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_key and reason:
                message = f"Cache configuration '{config_key}' validation failed: {reason}"
            elif config_key:
                message = f"Cache configuration '{config_key}' validation failed"
            else:
                message = "Cache configuration validation failed"

        super().__init__(message=message, config_key=config_key, reason=reason, **kwargs)


class CacheClientException(CacheException):
    """Cache client creation or operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Cache client {operation} failed: {reason}"
            elif operation:
                message = f"Cache client {operation} failed"
            else:
                message = "Cache client operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


class CachePoolException(CacheException):
    """Cache connection pool operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Cache pool {operation} failed: {reason}"
            elif operation:
                message = f"Cache pool {operation} failed"
            else:
                message = "Cache pool operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


# ============================================================================
# Storage exceptions
# ============================================================================


class StorageException(ResourceException):
    """Base exception for storage-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Storage operation failed"
        super().__init__(message=message, **kwargs)


class StorageConnectionException(StorageException):
    """Storage connection failure"""

    def __init__(self, storage_type: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if storage_type and reason:
                message = f"{storage_type} storage connection failed: {reason}"
            elif storage_type:
                message = f"{storage_type} storage connection failed"
            else:
                message = "Storage connection failed"

        super().__init__(message=message, storage_type=storage_type, reason=reason, **kwargs)


class StorageConfigValidationException(StorageException):
    """Storage configuration validation failure"""

    def __init__(self, config_key: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_key and reason:
                message = f"Storage configuration '{config_key}' validation failed: {reason}"
            elif config_key:
                message = f"Storage configuration '{config_key}' validation failed"
            else:
                message = "Storage configuration validation failed"

        super().__init__(message=message, config_key=config_key, reason=reason, **kwargs)


class FileUploadException(StorageException):
    """File upload failure"""

    def __init__(self, file_name: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if file_name and reason:
                message = f"File '{file_name}' upload failed: {reason}"
            elif file_name:
                message = f"File '{file_name}' upload failed"
            elif reason:
                message = f"File upload failed: {reason}"
            else:
                message = "File upload failed"

        super().__init__(message=message, file_name=file_name, reason=reason, **kwargs)


class FileDownloadException(StorageException):
    """File download failure"""

    def __init__(self, file_name: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if file_name and reason:
                message = f"File '{file_name}' download failed: {reason}"
            elif file_name:
                message = f"File '{file_name}' download failed"
            elif reason:
                message = f"File download failed: {reason}"
            else:
                message = "File download failed"

        super().__init__(message=message, file_name=file_name, reason=reason, **kwargs)


class FileDeleteException(StorageException):
    """File deletion failure"""

    def __init__(self, file_name: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if file_name and reason:
                message = f"File '{file_name}' deletion failed: {reason}"
            elif file_name:
                message = f"File '{file_name}' deletion failed"
            elif reason:
                message = f"File deletion failed: {reason}"
            else:
                message = "File deletion failed"

        super().__init__(message=message, file_name=file_name, reason=reason, **kwargs)


class FileNotFoundException(StorageException):
    """File not found"""

    def __init__(self, file_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"File '{file_name}' not found" if file_name else "File not found"

        super().__init__(message=message, file_name=file_name, **kwargs)


class FilePresignedUrlException(StorageException):
    """Generate presigned URL failure"""

    def __init__(self, file_name: str = None, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if file_name and operation:
                message = f"Failed to generate {operation} presigned URL for file '{file_name}'"
            elif file_name:
                message = f"Failed to generate presigned URL for file '{file_name}'"
            else:
                message = "Failed to generate presigned URL"

        super().__init__(message=message, file_name=file_name, operation=operation, reason=reason, **kwargs)


class StorageClientException(StorageException):
    """Storage client operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Storage client {operation} failed: {reason}"
            elif operation:
                message = f"Storage client {operation} failed"
            else:
                message = "Storage client operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


class StorageOperationException(StorageException):
    """Generic storage operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Storage {operation} operation failed: {reason}"
            elif operation:
                message = f"Storage {operation} operation failed"
            else:
                message = "Storage operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


# ============================================================================
# Graph database exceptions
# ============================================================================


class GraphDatabaseException(ResourceException):
    """Base exception for graph database-related errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Graph database operation failed"
        super().__init__(message=message, **kwargs)


class GraphDatabaseConnectionException(GraphDatabaseException):
    """Graph database connection failure"""

    def __init__(self, db_type: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if db_type and reason:
                message = f"{db_type} graph database connection failed: {reason}"
            elif db_type:
                message = f"{db_type} graph database connection failed"
            else:
                message = "Graph database connection failed"

        super().__init__(message=message, db_type=db_type, reason=reason, **kwargs)


class GraphDatabaseDisconnectedException(GraphDatabaseException):
    """Graph database connection lost"""

    def __init__(self, db_type: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"{db_type} graph database connection lost" if db_type else "Graph database connection lost"

        super().__init__(message=message, db_type=db_type, **kwargs)


class GraphDatabaseQueryException(GraphDatabaseException):
    """Graph database query execution failure"""

    def __init__(self, query: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"Graph database query failed: {reason}" if reason else "Graph database query failed"

        super().__init__(message=message, query=query, reason=reason, **kwargs)


class GraphDatabaseExecuteException(GraphDatabaseException):
    """Graph database statement execution failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Graph database {operation} operation failed: {reason}"
            elif operation:
                message = f"Graph database {operation} operation failed"
            else:
                message = "Graph database execution failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


class GraphDatabaseConfigValidationException(GraphDatabaseException):
    """Graph database configuration validation failure"""

    def __init__(self, config_key: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if config_key and reason:
                message = f"Graph database configuration '{config_key}' validation failed: {reason}"
            elif config_key:
                message = f"Graph database configuration '{config_key}' validation failed"
            else:
                message = "Graph database configuration validation failed"

        super().__init__(message=message, config_key=config_key, reason=reason, **kwargs)


class GraphDatabaseDriverException(GraphDatabaseException):
    """Graph database driver operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"Graph database driver {operation} failed: {reason}"
            elif operation:
                message = f"Graph database driver {operation} failed"
            else:
                message = "Graph database driver operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


class GraphDatabaseValidationException(GraphDatabaseException):
    """Graph database parameter validation failure"""

    def __init__(self, parameter: str = None, value: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if parameter and value and reason:
                message = f"Graph database parameter '{parameter}' validation failed for value '{value}': {reason}"
            elif parameter and reason:
                message = f"Graph database parameter '{parameter}' validation failed: {reason}"
            elif parameter:
                message = f"Graph database parameter '{parameter}' validation failed"
            else:
                message = "Graph database parameter validation failed"

        super().__init__(message=message, parameter=parameter, value=value, reason=reason, **kwargs)


class InvalidGraphNameException(GraphDatabaseValidationException):
    """Invalid graph name exception"""

    def __init__(self, graph_name: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if graph_name and reason:
                message = f"Invalid graph name '{graph_name}': {reason}"
            elif graph_name:
                message = f"Invalid graph name '{graph_name}'"
            else:
                message = "Invalid graph name"

        super().__init__(parameter="graph_name", value=graph_name, reason=reason, message=message, **kwargs)


class InvalidIdentifierException(GraphDatabaseValidationException):
    """Invalid identifier exception"""

    def __init__(self, identifier: str = None, context: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if identifier and context and reason:
                message = f"Invalid {context} '{identifier}': {reason}"
            elif identifier and reason:
                message = f"Invalid identifier '{identifier}': {reason}"
            elif identifier:
                message = f"Invalid identifier '{identifier}'"
            else:
                message = "Invalid identifier"

        super().__init__(parameter=context or "identifier", value=identifier, reason=reason, message=message, **kwargs)


# ============================================================================
# HTTP client exceptions
# ============================================================================


class HTTPException(ResourceException):
    """Base exception for HTTP request errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "HTTP request failed"
        super().__init__(message=message, **kwargs)


class HTTPConnectionException(HTTPException):
    """HTTP connection failure"""

    def __init__(self, url: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if url and reason:
                message = f"HTTP connection failed (url={url}): {reason}"
            elif url:
                message = f"HTTP connection failed (url={url})"
            elif reason:
                message = f"HTTP connection failed: {reason}"
            else:
                message = "HTTP connection failed"

        super().__init__(message=message, url=url, reason=reason, **kwargs)


class HTTPTimeoutException(HTTPException):
    """HTTP request timeout"""

    def __init__(self, url: str = None, timeout: float = None, message: str = None, **kwargs):
        if message is None:
            if url and timeout:
                message = f"HTTP request timed out (url={url}, timeout={timeout}s)"
            elif url:
                message = f"HTTP request timed out (url={url})"
            else:
                message = "HTTP request timed out"

        super().__init__(message=message, url=url, timeout=timeout, **kwargs)


class HTTPRequestException(HTTPException):
    """HTTP request execution failure"""

    def __init__(
        self,
        method: str = None,
        url: str = None,
        status_code: int = None,
        reason: str = None,
        message: str = None,
        **kwargs,
    ):
        if message is None:
            if method and url and status_code:
                message = f"HTTP request failed: {method} {url} (status={status_code})"
                if reason:
                    message += f" - {reason}"
            elif method and url:
                message = f"HTTP request failed: {method} {url}"
                if reason:
                    message += f" - {reason}"
            else:
                message = "HTTP request failed"

        super().__init__(message=message, method=method, url=url, status_code=status_code, reason=reason, **kwargs)


class HTTPClientException(HTTPException):
    """HTTP client creation or operation failure"""

    def __init__(self, operation: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if operation and reason:
                message = f"HTTP client {operation} failed: {reason}"
            elif operation:
                message = f"HTTP client {operation} failed"
            else:
                message = "HTTP client operation failed"

        super().__init__(message=message, operation=operation, reason=reason, **kwargs)


# ============================================================================
# Resource lifecycle exceptions
# ============================================================================


class ResourceInitializationException(ResourceException):
    """Resource initialization failure"""

    def __init__(self, resource_type: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if resource_type and reason:
                message = f"{resource_type} resource initialization failed: {reason}"
            elif resource_type:
                message = f"{resource_type} resource initialization failed"
            else:
                message = "Resource initialization failed"

        super().__init__(message=message, resource_type=resource_type, reason=reason, **kwargs)


class ResourceShutdownException(ResourceException):
    """Resource shutdown failure"""

    def __init__(self, resource_type: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if resource_type and reason:
                message = f"{resource_type} resource shutdown failed: {reason}"
            elif resource_type:
                message = f"{resource_type} resource shutdown failed"
            else:
                message = "Resource shutdown failed"

        super().__init__(message=message, resource_type=resource_type, reason=reason, **kwargs)


class ResourceNotInitializedException(ResourceException):
    """Resource not initialized"""

    def __init__(self, resource_type: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"{resource_type} resource not initialized" if resource_type else "Resource not initialized"

        super().__init__(message=message, resource_type=resource_type, **kwargs)


# ============================================================================
# Async executor exceptions
# ============================================================================


class AsyncExecutorException(ResourceException):
    """Base exception for async executor errors"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Async executor operation failed"
        super().__init__(message=message, **kwargs)


class AsyncExecutorPoolExhaustedException(AsyncExecutorException):
    """Async executor thread pool exhausted"""

    def __init__(self, max_workers: int = None, message: str = None, **kwargs):
        if message is None:
            if max_workers:
                message = f"Async executor thread pool exhausted (max_workers={max_workers})"
            else:
                message = "Async executor thread pool exhausted"

        super().__init__(message=message, max_workers=max_workers, **kwargs)


class AsyncExecutorTimeoutException(AsyncExecutorException):
    """Async executor operation timeout"""

    def __init__(self, operation: str = None, timeout: float = None, message: str = None, **kwargs):
        if message is None:
            if operation and timeout:
                message = f"Async executor {operation} operation timed out (timeout={timeout}s)"
            elif operation:
                message = f"Async executor {operation} operation timed out"
            else:
                message = "Async executor operation timed out"

        super().__init__(message=message, operation=operation, timeout=timeout, **kwargs)


class AsyncExecutorNotInitializedException(AsyncExecutorException):
    """Async executor not initialized"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "Async executor not initialized. Call init() before using run() or batch()"
        super().__init__(message=message, **kwargs)


class AsyncExecutorSubmitException(AsyncExecutorException):
    """Async executor task submission failure"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if reason:
                message = f"Async executor failed to submit task: {reason}"
            else:
                message = "Async executor failed to submit task"
        super().__init__(message=message, reason=reason, **kwargs)


class AsyncExecutorShutdownException(AsyncExecutorException):
    """Async executor shutdown failure"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"Async executor shutdown failed: {reason}" if reason else "Async executor shutdown failed"
        super().__init__(message=message, reason=reason, **kwargs)


class AsyncExecutorValidationException(AsyncExecutorException):
    """Async executor parameter validation failure"""

    def __init__(self, parameter: str = None, reason: str = None, message: str = None, **kwargs):
        if message is None:
            if parameter and reason:
                message = f"Async executor parameter '{parameter}' validation failed: {reason}"
            elif parameter:
                message = f"Async executor parameter '{parameter}' validation failed"
            else:
                message = "Async executor parameter validation failed"
        super().__init__(message=message, parameter=parameter, reason=reason, **kwargs)


# 导出所有异常类 - 按类别分组以便于查找
__all__ = [
    # ========== 异步执行器异常 ==========
    "AsyncExecutorException",
    "AsyncExecutorNotInitializedException",
    "AsyncExecutorPoolExhaustedException",
    "AsyncExecutorShutdownException",
    "AsyncExecutorSubmitException",
    "AsyncExecutorTimeoutException",
    "AsyncExecutorValidationException",
    "CacheClientException",
    "CacheConfigValidationException",
    "CacheConnectionException",
    "CacheDisconnectedException",
    # ========== 缓存异常 ==========
    "CacheException",
    "CacheOperationException",
    "CachePoolException",
    "CacheTimeoutException",
    "DatabaseConfigValidationException",
    "DatabaseConnectionException",
    "DatabaseDisconnectedException",
    "DatabaseEngineException",
    # ========== 数据库异常 ==========
    "DatabaseException",
    "DatabaseExecuteException",
    "DatabasePoolExhaustedException",
    "DatabaseQueryException",
    "DatabaseSessionException",
    "DatabaseTransactionException",
    "FileDeleteException",
    "FileDownloadException",
    "FileNotFoundException",
    "FilePresignedUrlException",
    "FileUploadException",
    "GraphDatabaseConfigValidationException",
    "GraphDatabaseConnectionException",
    "GraphDatabaseDisconnectedException",
    "GraphDatabaseDriverException",
    # ========== 图数据库异常 ==========
    "GraphDatabaseException",
    "GraphDatabaseExecuteException",
    "GraphDatabaseQueryException",
    "GraphDatabaseValidationException",
    "HTTPClientException",
    "HTTPConnectionException",
    # ========== HTTP 客户端异常 ==========
    "HTTPException",
    "HTTPRequestException",
    "HTTPTimeoutException",
    "InvalidGraphNameException",
    "InvalidIdentifierException",
    # ========== 基础异常 ==========
    "ResourceException",
    # ========== 资源生命周期异常 ==========
    "ResourceInitializationException",
    "ResourceNotInitializedException",
    "ResourceShutdownException",
    "StorageClientException",
    "StorageConfigValidationException",
    "StorageConnectionException",
    # ========== 存储异常 ==========
    "StorageException",
    "StorageOperationException",
]
