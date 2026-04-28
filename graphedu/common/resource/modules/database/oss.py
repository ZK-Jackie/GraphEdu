"""OSS (Object Storage Service) resource module.

This module provides synchronous and asynchronous S3-compatible storage clients
with support for file upload, download, deletion, and presigned URL generation.
Supports multiple S3-compatible providers (AWS S3, MinIO, Alibaba Cloud OSS, etc.).
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from itertools import repeat
import logging
from pathlib import Path
import traceback
from typing import TYPE_CHECKING, Optional, Self

from boto3 import client
from fastapi import UploadFile

from graphedu.common.config.modules.datasource import OssConfig
from graphedu.common.exceptions import (
    FileDeleteException,
    FileDownloadException,
    FileNotFoundException,
    FilePresignedUrlException,
    FileUploadException,
    StorageClientException,
    StorageConnectionException,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource
from graphedu.common.resource.modules.database.s3_adaptation.s3_config import get_provider_config
from graphedu.common.utils.files import ensure_path, ensure_str_path, is_file_exists

if TYPE_CHECKING:
    from aiobotocore.session import AioSession, ClientCreatorContext
    from types_aiobotocore_s3 import client as TypeAiobotocore
    from types_boto3_s3 import client as TypeBoto3

logger = logging.getLogger(__name__)


class S3Client(BaseSyncResource):
    """Synchronous S3-compatible storage client.

    This client manages a boto3 S3 client for synchronous object storage operations
    including file upload, download, deletion, and presigned URL generation.
    Supports multiple S3-compatible providers through provider configuration.

    Attributes:
        config (OssConfig | None): OSS connection configuration.
        mode (str): Operation mode indicator, set to "sync".
        _s3_client (Optional[TypeBoto3.S3Client]): Boto3 S3 client instance.
        _provider_config: Provider-specific configuration for URL generation.

    Raises:
        StorageConnectionException: If S3 connection fails.
        StorageClientException: If client operation fails.
        FileUploadException: If file upload fails.
        FileDownloadException: If file download fails.
        FileDeleteException: If file deletion fails.
        FilePresignedUrlException: If presigned URL generation fails.
    """

    config: OssConfig | None = None
    mode = "sync"
    _s3_client: Optional["TypeBoto3.S3Client"] = None
    _provider_config = None

    @property
    def client(self) -> Optional["TypeBoto3.S3Client"]:
        """Get the boto3 S3 client instance.

        Returns:
            Optional[TypeBoto3.S3Client]: The boto3 S3 client or None if not initialized.
        """
        return self._s3_client

    def init(self, config: OssConfig | dict) -> Self:
        """Initialize the S3 client with connection configuration.

        Creates a boto3 S3 client with the provided configuration for
        synchronous object storage operations. Accepts either an OssConfig
        object or a dictionary that will be validated into one.

        Args:
            config: OSS configuration containing endpoint, credentials, and provider settings.

        Returns:
            Self: Returns self for method chaining.

        Raises:
            StorageConnectionException: If client initialization fails.
        """
        if isinstance(config, dict):
            config = OssConfig.model_validate(config)
        self.config = config

        # Get provider configuration based on provider type
        self._provider_config = get_provider_config(self.config.provider)
        boto_config = self._provider_config.get_boto_config()

        try:
            self._s3_client = client(
                "s3",
                endpoint_url=str(self.config.endpoint),
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key,
                use_ssl=self.config.use_ssl,
                config=boto_config,
            )
            logger.debug(f"Sync S3 client connected: {self._s3_client}")
            logger.info(f"Synchronous S3 client connected successfully (provider: {self.config.provider})")
            return self
        except Exception as e:
            logger.error(f"S3 client initialization failed: {e}")
            logger.debug(traceback.format_exc())
            raise StorageConnectionException(reason=str(e), storage_type="S3") from e

    def shutdown(self, _: Self = None) -> None:
        """Shutdown the S3 client and close connections.

        Closes the boto3 S3 client and cleans up resources.
        After shutdown, the client cannot be used for new operations.

        Args:
            _: Ignored parameter (required by BaseSyncResource interface).
        """
        if self._s3_client:
            self._s3_client.close()
            self._s3_client = None
            logger.info("Synchronous S3 client closed successfully")

    def download(self, object_name: str, *, download_path: str = None, bucket_name: str = None) -> Path | None:
        """Download a file from S3-compatible storage.

        Downloads an object from S3 storage to the local filesystem.
        The download directory will be created automatically if it doesn't exist.

        Args:
            object_name: S3 object key/name to download.
            download_path: Local directory path for downloaded files.
                          Defaults to config.download_to if not specified.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            Path | None: Local file path if download succeeds, None if fails.

        Raises:
            FileDownloadException: If file download fails.
        """
        bucket_name = bucket_name or self.config.bucket
        download_path = download_path or self.config.download_to
        file_path = ensure_str_path(download_path, folder=True) / object_name
        file_path = ensure_path(file_path)
        logger.debug(f"S3: Downloading file '{object_name}' from '{bucket_name}' to '{file_path}'")
        logger.info(f"S3: Downloading file '{object_name}'")

        try:
            self._s3_client.download_file(bucket_name, object_name, str(file_path))
        except Exception as e:
            logger.error(f"Failed to download file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDownloadException(
                file_name=object_name,
                reason="Download operation failed",
                details={"bucket_name": bucket_name, "file_path": str(file_path), "original_error": str(e)},
            ) from e
        return file_path

    def upload(self, object_name: str, file_path: str = None, *, bucket_name: str = None) -> str:
        """Upload a file to S3-compatible storage.

        Uploads a local file to S3 storage and returns the object URL.

        Args:
            object_name: S3 object key/name for the uploaded file.
            file_path: Local file path to upload. If not specified,
                      defaults to config.upload_from + object_name.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: Public URL of the uploaded object.

        Raises:
            FileUploadException: If file upload fails.
        """
        file_path = file_path or self.config.upload_from + "/" + object_name
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Uploading file '{file_path}' to '{bucket_name}/{object_name}'")
        logger.info(f"S3: Uploading file '{file_path}'")

        try:
            self._s3_client.upload_file(file_path, bucket_name, object_name)
            # Generate URL using provider configuration
            return self._provider_config.build_object_url(
                endpoint=str(self.config.endpoint),
                bucket=bucket_name,
                object_name=object_name,
                use_ssl=self.config.use_ssl,
            )
        except Exception as e:
            logger.error(f"Failed to upload file '{file_path}': {e}")
            logger.debug(traceback.format_exc())
            raise FileUploadException(
                file_name=object_name,
                reason="Upload operation failed",
                details={"bucket_name": bucket_name, "file_path": str(file_path)},
            ) from e

    def upload_object(self, object_name: str, data: BytesIO, *, bucket_name: str = None) -> str:
        """Upload a file object (BytesIO) to S3-compatible storage.

        Uploads in-memory file data to S3 storage and returns the object URL.

        Args:
            object_name: S3 object key/name for the uploaded file.
            data: File data as BytesIO object.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: Public URL of the uploaded object.

        Raises:
            FileUploadException: If file object upload fails.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Uploading file object '{object_name}' to '{bucket_name}'")
        logger.info(f"S3: Uploading file object '{object_name}'")

        try:
            self._s3_client.upload_fileobj(data, bucket_name, object_name)
            # Generate URL using provider configuration
            return self._provider_config.build_object_url(
                endpoint=str(self.config.endpoint),
                bucket=bucket_name,
                object_name=object_name,
                use_ssl=self.config.use_ssl,
            )
        except Exception as e:
            logger.error(f"Failed to upload file object '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileUploadException(
                file_name=object_name, reason="File object upload failed", details={"bucket_name": bucket_name}
            ) from e

    def batch_download(
        self, object_names: list[str], *, download_path: str = None, bucket_name: str = None
    ) -> list[Path | None]:
        """Batch download files from S3-compatible storage using multithreading.

        Downloads multiple files concurrently using a thread pool.
        Failed downloads return None in the corresponding position.

        Args:
            object_names: List of S3 object keys/names to download.
            download_path: Local directory path for downloaded files.
                          Defaults to config.download_to if not specified.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            list[Path | None]: List of local file paths. Failed downloads are None.
        """

        def _download(_object_name, _bucket_name, _download_path):
            try:
                return self.download(object_name=_object_name, bucket_name=_bucket_name, download_path=_download_path)
            except FileDownloadException:
                return None

        with ThreadPoolExecutor() as executor:
            return list(executor.map(_download, object_names, repeat(bucket_name), repeat(download_path)))

    def batch_upload(
        self, file_paths: list[str], object_names: list[str], *, bucket_name: str = None
    ) -> list[str | None]:
        """Batch upload files to S3-compatible storage using multithreading.

        Uploads multiple files concurrently using a thread pool.
        Failed uploads return None in the corresponding position.

        Args:
            file_paths: List of local file paths to upload.
            object_names: List of S3 object keys/names for uploaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            list[str | None]: List of object URLs. Failed uploads are None.
        """

        def _upload(_file_path, _object_name, _bucket_name):
            try:
                return self.upload(file_path=_file_path, object_name=_object_name, bucket_name=_bucket_name)
            except FileUploadException:
                return None

        with ThreadPoolExecutor() as executor:
            return list(executor.map(_upload, file_paths, object_names, repeat(bucket_name)))

    def batch_upload_object(
        self, data: list[BytesIO], object_names: list[str], *, bucket_name: str = None
    ) -> list[str | None]:
        """Batch upload file objects to S3-compatible storage using multithreading.

        Uploads multiple BytesIO objects concurrently using a thread pool.
        Failed uploads return None in the corresponding position.

        Args:
            data: List of file data as BytesIO objects.
            object_names: List of S3 object keys/names for uploaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            list[str | None]: List of object URLs. Failed uploads are None.
        """

        def _upload_object(_data, _object_name, _bucket_name):
            try:
                return self.upload_object(data=_data, object_name=_object_name, bucket_name=_bucket_name)
            except FileUploadException:
                return None

        with ThreadPoolExecutor() as executor:
            return list(executor.map(_upload_object, data, object_names, repeat(bucket_name)))

    async def async_upload(
        self, file_path: str, object_name: str, *, bucket_name: str = None, pool: ThreadPoolExecutor = None
    ) -> str:
        """Asynchronously upload a file using thread pool with synchronous function.

        Wraps the synchronous upload method in an async executor for async compatibility.

        Args:
            file_path: Local file path to upload.
            object_name: S3 object key/name for the uploaded file.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            pool: Optional thread pool executor for async execution.

        Returns:
            str: Public URL of the uploaded object.
        """

        def _upload(_object_name, _file_path, _bucket_name):
            return self.upload(object_name=_object_name, file_path=_file_path, bucket_name=_bucket_name)

        return await asyncio.get_running_loop().run_in_executor(pool, _upload, object_name, file_path, bucket_name)

    async def async_download(
        self, object_name: str, *, download_path: str = None, bucket_name: str = None, pool: ThreadPoolExecutor = None
    ) -> Path:
        """Asynchronously download a file using thread pool with synchronous function.

        Wraps the synchronous download method in an async executor for async compatibility.

        Args:
            object_name: S3 object key/name to download.
            download_path: Local directory path for downloaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            pool: Optional thread pool executor for async execution.

        Returns:
            Path: Local file path of the downloaded file.
        """

        def _download(_object_name, _download_path, _bucket_name):
            return self.download(object_name=_object_name, download_path=_download_path, bucket_name=_bucket_name)

        return await asyncio.get_running_loop().run_in_executor(
            pool, _download, object_name, download_path, bucket_name
        )

    async def async_upload_object(
        self, data: BytesIO, object_name: str, *, bucket_name: str = None, pool: ThreadPoolExecutor = None
    ) -> str:
        """Asynchronously upload a file object using thread pool with synchronous function.

        Wraps the synchronous upload_object method in an async executor.

        Args:
            data: File data as BytesIO object.
            object_name: S3 object key/name for the uploaded file.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            pool: Optional thread pool executor for async execution.

        Returns:
            str: Public URL of the uploaded object.
        """

        def _upload_object(_data, _object_name, _bucket_name):
            return self.upload_object(data=_data, object_name=_object_name, bucket_name=_bucket_name)

        return await asyncio.get_running_loop().run_in_executor(pool, _upload_object, data, object_name, bucket_name)

    def get_md5(self, object_name: str, *, bucket_name: str = None) -> str:
        """Get the MD5 hash (ETag) of an S3 object.

        Retrieves the ETag of an object, which typically represents the MD5 hash
        of the object content for non-multipart uploads.

        Args:
            object_name: S3 object key/name.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: MD5 hash (ETag) of the object with quotes removed.

        Raises:
            FileDownloadException: If metadata retrieval fails.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Getting MD5 of file '{object_name}' from '{bucket_name}'")
        logger.info(f"S3: Getting MD5 of file '{object_name}'")

        try:
            return self._s3_client.head_object(Bucket=bucket_name, Key=object_name)["ETag"].strip('"')
        except Exception as e:
            logger.error(f"Failed to get MD5 of file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDownloadException(
                file_name=object_name, reason="Failed to retrieve object metadata", details={"bucket_name": bucket_name}
            ) from e

    def delete_object(self, object_name: str, *, bucket_name: str = None, ignore_existence_error: bool = False) -> None:
        """Delete a file from S3-compatible storage.

        Deletes an object from S3 storage. Optionally ignores errors if
        the object doesn't exist.

        Args:
            object_name: S3 object key/name to delete.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            ignore_existence_error: If True, ignores errors when object doesn't exist.

        Raises:
            FileDeleteException: If file deletion fails and ignore_existence_error is False.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Deleting file '{object_name}' from '{bucket_name}'")
        logger.info(f"S3: Deleting file '{object_name}'")

        try:
            self._s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        except Exception as e:
            if ignore_existence_error:
                logger.warning(f"File '{object_name}' may not exist, ignoring error")
                return
            logger.error(f"Failed to delete file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDeleteException(
                file_name=object_name, reason="Delete operation failed", details={"bucket_name": bucket_name}
            ) from e

    def generate_presigned_url(
        self,
        object_name: str,
        *,
        operation: str = "get_object",
        expiration: int = 3600,
        bucket_name: str = None,
        **params,
    ) -> str:
        """Generate a presigned URL for temporary access to an S3 object.

        Creates a temporary URL that allows direct access to an object without
        authentication. Useful for sharing files or allowing client-side uploads.

        Args:
            object_name: S3 object key/name.
            operation: S3 operation type. Supports 'get_object' (download) and
                      'put_object' (upload). Defaults to "get_object".
            expiration: URL expiration time in seconds. Defaults to 3600 (1 hour).
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            **params: Additional parameters such as ResponseContentType,
                     ResponseContentDisposition, etc.

        Returns:
            str: Presigned URL for temporary object access.

        Raises:
            FilePresignedUrlException: If presigned URL generation fails.
        """
        from botocore.exceptions import ClientError

        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Generating presigned URL for '{object_name}' in '{bucket_name}' (expires in {expiration}s)")
        logger.info(f"S3: Generating presigned URL for '{object_name}'")

        try:
            s3_params = {"Bucket": bucket_name, "Key": object_name, **params}

            url = self._s3_client.generate_presigned_url(ClientMethod=operation, Params=s3_params, ExpiresIn=expiration)

            logger.debug(f"Presigned URL generated: {url[:100]}...")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FilePresignedUrlException(
                file_name=object_name,
                reason="Presigned URL generation failed",
                details={
                    "bucket_name": bucket_name,
                    "operation": operation,
                    "expiration": expiration,
                    "error_code": e.response.get("Error", {}).get("Code"),
                    "error_message": e.response.get("Error", {}).get("Message"),
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FilePresignedUrlException(
                file_name=object_name,
                reason="Unexpected error during presigned URL generation",
                details={"bucket_name": bucket_name, "operation": operation, "error": str(e)},
            ) from e


class AioS3Client(BaseAsyncResource):
    """Asynchronous S3-compatible storage client.

    This client manages an aiobotocore S3 client for asynchronous object storage
    operations including file upload, download, deletion, and presigned URL generation.
    Supports multiple S3-compatible providers through provider configuration.

    Attributes:
        config (OssConfig | None): OSS connection configuration.
        mode (str): Operation mode indicator.
        _session (Optional[AioSession]): Aiobotocore session.
        _client_config (Optional[dict]): Client configuration for creating clients.
        _provider_config: Provider-specific configuration for URL generation.

    Raises:
        StorageConnectionException: If S3 connection fails.
        StorageClientException: If client operation fails.
        FileUploadException: If file upload fails.
        FileDownloadException: If file download fails.
        FileDeleteException: If file deletion fails.
        FilePresignedUrlException: If presigned URL generation fails.
    """

    config: OssConfig | None = None
    mode = "async"
    _session: Optional["AioSession"] = None
    _client_config: dict | None = None
    _provider_config = None

    def client(self) -> "ClientCreatorContext[TypeAiobotocore.S3Client]":
        """Get the async S3 client context manager.

        Returns a context manager for creating async S3 clients.
        Should be used with 'async with' statement.

        Returns:
            ClientCreatorContext[TypeAiobotocore.S3Client]: Async S3 client context manager.

        Raises:
            StorageClientException: If client is not initialized.
        """
        if not self._session:
            raise StorageClientException(operation="create_client", reason="Client not initialized. Call init() first.")
        return self._session.create_client(**self._client_config)

    async def init(self, config: OssConfig | dict) -> Self:
        """Initialize the async S3 client with connection configuration.

        Creates an aiobotocore session and client configuration for
        asynchronous object storage operations. Accepts either an OssConfig
        object or a dictionary that will be validated into one.

        Args:
            config: OSS configuration containing endpoint, credentials, and provider settings.

        Returns:
            Self: Returns self for method chaining.

        Raises:
            ImportError: If aiobotocore is not installed.
            StorageConnectionException: If client initialization fails.
        """
        try:
            from aiobotocore.session import get_session
        except ImportError:
            raise ImportError("Error while importing `aiobotocore`, please install it first.") from None

        if isinstance(config, dict):
            config = OssConfig.model_validate(config)
        self.config = config

        # Get provider configuration based on provider type
        self._provider_config = get_provider_config(self.config.provider)
        boto_config = self._provider_config.get_boto_config()

        try:
            # Store session and configuration for creating clients on demand
            self._session = get_session()
            self._client_config = {
                "service_name": "s3",
                "endpoint_url": str(self.config.endpoint),
                "aws_access_key_id": self.config.access_key,
                "aws_secret_access_key": self.config.secret_key,
                "use_ssl": self.config.use_ssl,
                "config": boto_config,
            }
            logger.info(f"Async S3 client initialized successfully (provider: {self.config.provider})")
            return self
        except Exception as e:
            logger.error(f"Async S3 client initialization failed: {e}")
            logger.debug(traceback.format_exc())
            raise StorageConnectionException(
                reason=str(e),
                storage_type="Async S3",
                details={"endpoint": str(self.config.endpoint), "original_error": str(e)},
            ) from e

    async def shutdown(self, _: Self = None) -> None:
        """Shutdown the async S3 client and clean up resources.

        Clears the session and configuration. After shutdown,
        the client cannot be used for new operations.

        Args:
            _: Ignored parameter (required by BaseAsyncResource interface).

        Raises:
            StorageConnectionException: If shutdown fails.
        """
        if self._session:
            try:
                # Clear session and configuration
                self._session = None
                self._client_config = None
                logger.info("Async S3 client closed successfully")
            except Exception as e:
                logger.error(f"Async S3 client shutdown failed: {e}")
                logger.debug(traceback.format_exc())
                raise StorageConnectionException(
                    reason=str(e), storage_type="Async S3", details={"original_error": str(e)}
                ) from e

    def build_object_url(self, object_name: str, *, bucket_name: str = None) -> str:
        """Build the public URL for an S3 object.

        Constructs the object URL based on provider configuration.

        Args:
            object_name: S3 object key/name.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: Public URL of the object.
        """
        if not bucket_name:
            bucket_name = self.config.bucket
        return self._provider_config.build_object_url(
            endpoint=str(self.config.endpoint), bucket=bucket_name, object_name=object_name, use_ssl=self.config.use_ssl
        )

    async def download(self, object_name: str, file_path: str = None, *, bucket_name: str = None) -> Path:
        """Asynchronously download a file from S3-compatible storage.

        Downloads an object from S3 storage to the local filesystem.

        Args:
            object_name: S3 object key/name to download.
            file_path: Local directory path for downloaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            Path: Local file path of the downloaded file.

        Raises:
            FileDownloadException: If file download fails.
        """
        if not bucket_name:
            bucket_name = self.config.bucket
        if not file_path:
            file_path = self.config.download_to
        aim_path = ensure_str_path(file_path, folder=True) / object_name
        logger.debug(f"S3: Downloading file '{object_name}' from '{bucket_name}' to '{file_path}'")
        logger.info(f"S3: Downloading file '{object_name}'")

        try:
            async with self.client() as async_s3:
                await async_s3.download_file(bucket_name, object_name, str(aim_path))
        except Exception as e:
            logger.error(f"Failed to download file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDownloadException(
                file_name=object_name,
                reason="Async download failed",
                details={"bucket_name": bucket_name, "file_path": str(aim_path)},
            ) from e
        return aim_path

    async def download_stream(self, object_name: str, *, bucket_name: str = None, chunk_size: int = 8192):
        """Asynchronously stream a file from S3-compatible storage.

        Downloads an object from S3 storage as an async stream for proxying.
        This is useful for implementing file proxy endpoints to avoid CORS issues.

        Args:
            object_name: S3 object key/name to download.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            chunk_size: Size of chunks to read from S3. Defaults to 8KB.

        Yields:
            bytes: Chunks of file data.

        Raises:
            FileDownloadException: If file download fails.

        Example:
            >>> async for chunk in s3_client.download_stream("path/to/file.pdf"):
            ...     yield chunk
        """
        if not bucket_name:
            bucket_name = self.config.bucket
        logger.debug(f"S3: Streaming file '{object_name}' from '{bucket_name}'")
        logger.info(f"S3: Streaming file '{object_name}'")

        try:
            async with self.client() as async_s3:
                response = await async_s3.get_object(Bucket=bucket_name, Key=object_name)
                # Note: response["Body"] is a StreamingBody wrapping aiohttp.ClientResponse
                async with response["Body"] as stream:  # type: ClientResponse
                    # Reading stream continuously
                    while True:
                        chunk = await stream.content.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
        except Exception as e:
            logger.error(f"Failed to stream file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDownloadException(
                file_name=object_name,
                reason="Async stream failed",
                details={"bucket_name": bucket_name},
            ) from e

    async def upload(self, file_path: str, object_name: str, *, bucket_name: str = None) -> str:
        """Asynchronously upload a file to S3-compatible storage.

        Uploads a local file to S3 storage and returns the object URL.

        Args:
            file_path: Local file path to upload.
            object_name: S3 object key/name for the uploaded file.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: Public URL of the uploaded object.

        Raises:
            FileUploadException: If file upload fails.
        """
        if not bucket_name:
            bucket_name = self.config.bucket
        logger.debug(f"S3: Uploading file '{file_path}' to '{bucket_name}/{object_name}'")
        logger.info(f"S3: Uploading file '{file_path}'")

        try:
            async with self.client() as async_s3:
                await async_s3.upload_file(file_path, bucket_name, object_name)
            # Generate URL using provider configuration
            return self._provider_config.build_object_url(
                endpoint=str(self.config.endpoint),
                bucket=bucket_name,
                object_name=object_name,
                use_ssl=self.config.use_ssl,
            )
        except Exception as e:
            logger.error(f"Failed to upload file '{file_path}': {e}")
            logger.debug(traceback.format_exc())
            raise FileUploadException(
                file_name=object_name,
                reason="Async upload failed",
                details={"bucket_name": bucket_name, "file_path": file_path},
            ) from e

    async def batch_download(
        self, object_names: list[str], file_path: str = None, *, bucket_name: str = None
    ) -> list[Path]:
        """Asynchronously batch download files from S3-compatible storage.

        Downloads multiple files concurrently using asyncio.gather.

        Args:
            object_names: List of S3 object keys/names to download.
            file_path: Local directory path for downloaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            list[Path]: List of local file paths.
        """
        if not bucket_name:
            bucket_name = self.config.bucket
        if not file_path:
            file_path = self.config.download_to
        tasks = []
        for object_name in object_names:
            tasks.append(self.download(object_name, file_path, bucket_name=bucket_name))
        return await asyncio.gather(*tasks)

    async def batch_upload(
        self, file_paths: list[str], object_names: list[str], *, bucket_name: str = None
    ) -> list[str]:
        """Asynchronously batch upload files to S3-compatible storage.

        Uploads multiple files concurrently using asyncio.gather.

        Args:
            file_paths: List of local file paths to upload.
            object_names: List of S3 object keys/names for uploaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            list[str]: List of object URLs.

        Raises:
            FileNotFoundException: If any local file doesn't exist.
        """
        if not bucket_name:
            bucket_name = self.config.bucket
        tasks = []
        for file_path, object_name in zip(file_paths, object_names, strict=False):
            if not is_file_exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundException(file_name=object_name, details={"file_path": file_path})
            tasks.append(self.upload(file_path, object_name, bucket_name=bucket_name))
        return await asyncio.gather(*tasks)

    async def upload_object(self, data: BytesIO, object_name: str, *, bucket_name: str = None) -> str:
        """Asynchronously upload a file object (BytesIO) to S3-compatible storage.

        Uploads in-memory file data to S3 storage and returns the object URL.

        Args:
            data: File data as BytesIO object.
            object_name: S3 object key/name for the uploaded file.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: Public URL of the uploaded object.

        Raises:
            FileUploadException: If file object upload fails.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Uploading file object '{object_name}' to '{bucket_name}'")
        logger.info(f"S3: Uploading file object '{object_name}'")

        try:
            async with self.client() as async_s3:
                # Reset pointer to beginning
                data.seek(0)
                await async_s3.upload_fileobj(data, bucket_name, object_name)
            # Generate URL using provider configuration
            return self._provider_config.build_object_url(
                endpoint=str(self.config.endpoint),
                bucket=bucket_name,
                object_name=object_name,
                use_ssl=self.config.use_ssl,
            )
        except Exception as e:
            logger.error(f"Failed to upload file object '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileUploadException(
                file_name=object_name, reason="Async file object upload failed", details={"bucket_name": bucket_name}
            ) from e

    async def batch_upload_object(
        self, data_list: list[BytesIO], object_names: list[str], *, bucket_name: str = None
    ) -> list[str]:
        """Asynchronously batch upload file objects to S3-compatible storage.

        Uploads multiple BytesIO objects concurrently using asyncio.gather.

        Args:
            data_list: List of file data as BytesIO objects.
            object_names: List of S3 object keys/names for uploaded files.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            list[str]: List of object URLs.
        """
        bucket_name = bucket_name or self.config.bucket
        tasks = []
        for data, object_name in zip(data_list, object_names, strict=False):
            tasks.append(self.upload_object(data, object_name, bucket_name=bucket_name))
        return await asyncio.gather(*tasks)

    async def upload_uploadfile(self, upload_file: UploadFile, object_name: str, *, bucket_name: str = None) -> str:
        """Asynchronously upload a FastAPI UploadFile object to S3-compatible storage.

        Uploads a FastAPI UploadFile object directly to S3 storage
        without saving to local disk first.

        Args:
            upload_file: FastAPI UploadFile object from request.
            object_name: S3 object key/name for the uploaded file.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: Public URL of the uploaded object.

        Raises:
            FileUploadException: If upload fails.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Uploading UploadFile '{upload_file.filename}' to '{bucket_name}/{object_name}'")
        logger.info(f"S3: Uploading UploadFile '{upload_file.filename}'")

        try:
            async with self.client() as async_s3:
                # UploadFile.file is the underlying file object
                await async_s3.upload_fileobj(upload_file.file, bucket_name, object_name)
            # Generate URL using provider configuration
            return self._provider_config.build_object_url(
                endpoint=str(self.config.endpoint),
                bucket=bucket_name,
                object_name=object_name,
                use_ssl=self.config.use_ssl,
            )
        except Exception as e:
            logger.error(f"Failed to upload UploadFile '{upload_file.filename}': {e}")
            logger.debug(traceback.format_exc())
            raise FileUploadException(
                file_name=upload_file.filename or object_name,
                reason="Async UploadFile upload failed",
                details={"bucket_name": bucket_name},
            ) from e

    async def download_to_bytesio(
        self, object_name: str, *, bucket_name: str = None, chunk_size: int = 1024
    ) -> BytesIO:
        """Asynchronously download an S3 object to a BytesIO object.

        Downloads an object directly into memory without saving to disk.

        Args:
            object_name: S3 object key/name to download.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            chunk_size: Download chunk size in bytes. Defaults to 1024.

        Returns:
            BytesIO: Object data as in-memory bytes.

        Raises:
            FileDownloadException: If download fails.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Downloading file '{object_name}' from '{bucket_name}' to BytesIO")
        logger.info(f"S3: Downloading file '{object_name}' to BytesIO")

        try:
            file_stream = BytesIO()
            async with self.client() as async_s3:
                s3_ob = await async_s3.get_object(Bucket=bucket_name, Key=object_name)
                while chunk := await s3_ob["Body"].read(chunk_size):
                    file_stream.write(chunk)
            file_stream.seek(0)
            return file_stream
        except Exception as e:
            logger.error(f"Failed to download file '{object_name}' to BytesIO: {e}")
            logger.debug(traceback.format_exc())
            raise FileDownloadException(
                file_name=object_name, reason="Async BytesIO download failed", details={"bucket_name": bucket_name}
            ) from e

    async def get_md5(self, object_name: str, *, bucket_name: str = None) -> str:
        """Asynchronously get the MD5 hash (ETag) of an S3 object.

        Retrieves the ETag of an object asynchronously.

        Args:
            object_name: S3 object key/name.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.

        Returns:
            str: MD5 hash (ETag) of the object with quotes removed.

        Raises:
            FileDownloadException: If metadata retrieval fails.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Getting MD5 of file '{object_name}' from '{bucket_name}'")
        logger.info(f"S3: Getting MD5 of file '{object_name}'")

        try:
            async with self.client() as async_s3:
                response = await async_s3.head_object(Bucket=bucket_name, Key=object_name)
                return response["ETag"].strip('"')
        except Exception as e:
            logger.error(f"Failed to get MD5 of file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDownloadException(
                file_name=object_name, reason="Failed to retrieve object metadata", details={"bucket_name": bucket_name}
            ) from e

    async def delete_object(
        self, object_name: str, *, bucket_name: str = None, ignore_existence_error: bool = False
    ) -> None:
        """Asynchronously delete a file from S3-compatible storage.

        Deletes an object from S3 storage asynchronously.
        Optionally ignores errors if the object doesn't exist.

        Args:
            object_name: S3 object key/name to delete.
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            ignore_existence_error: If True, ignores errors when object doesn't exist.

        Raises:
            FileDeleteException: If file deletion fails and ignore_existence_error is False.
        """
        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Deleting file '{object_name}' from '{bucket_name}'")
        logger.info(f"S3: Deleting file '{object_name}'")

        try:
            async with self.client() as async_s3:
                await async_s3.delete_object(Bucket=bucket_name, Key=object_name)
        except Exception as e:
            if ignore_existence_error:
                logger.warning(f"File '{object_name}' may not exist, ignoring error")
                return
            logger.error(f"Failed to delete file '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FileDeleteException(
                file_name=object_name, reason="Async delete failed", details={"bucket_name": bucket_name}
            ) from e

    async def generate_presigned_url(
        self,
        object_name: str,
        *,
        operation: str = "get_object",
        expiration: int = 3600,
        bucket_name: str = None,
        **params,
    ) -> str:
        """Asynchronously generate a presigned URL for temporary access to an S3 object.

        Creates a temporary URL that allows direct access to an object without
        authentication. Useful for sharing files or allowing client-side uploads.

        Args:
            object_name: S3 object key/name.
            operation: S3 operation type. Supports 'get_object' (download) and
                      'put_object' (upload). Defaults to "get_object".
            expiration: URL expiration time in seconds. Defaults to 3600 (1 hour).
            bucket_name: S3 bucket name. Defaults to config.bucket if not specified.
            **params: Additional parameters such as ResponseContentType,
                     ResponseContentDisposition, etc.

        Returns:
            str: Presigned URL for temporary object access.

        Raises:
            FilePresignedUrlException: If presigned URL generation fails.
        """
        from botocore.exceptions import ClientError

        bucket_name = bucket_name or self.config.bucket
        logger.debug(f"S3: Generating presigned URL for '{object_name}' in '{bucket_name}' (expires in {expiration}s)")
        logger.info(f"S3: Generating presigned URL for '{object_name}'")

        try:
            s3_params = {"Bucket": bucket_name, "Key": object_name, **params}

            async with self.client() as async_s3:
                url = await async_s3.generate_presigned_url(
                    ClientMethod=operation, Params=s3_params, ExpiresIn=expiration
                )

            logger.debug(f"Presigned URL generated: {url[:100]}...")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FilePresignedUrlException(
                file_name=object_name,
                reason="Async presigned URL generation failed",
                details={
                    "bucket_name": bucket_name,
                    "operation": operation,
                    "expiration": expiration,
                    "error_code": e.response.get("Error", {}).get("Code"),
                    "error_message": e.response.get("Error", {}).get("Message"),
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for '{object_name}': {e}")
            logger.debug(traceback.format_exc())
            raise FilePresignedUrlException(
                file_name=object_name,
                reason="Unexpected error during async presigned URL generation",
                details={"bucket_name": bucket_name, "operation": operation, "error": str(e)},
            ) from e
