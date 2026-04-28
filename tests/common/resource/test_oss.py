"""OSS (Object Storage Service) resource module unit tests.

测试覆盖范围：
- S3Client (同步客户端):
    - init 和 shutdown 流程
    - 核心功能测试 (download, upload, upload_object, batch_download, batch_upload, batch_upload_object)
    - 异步包装方法测试 (async_upload, async_download, async_upload_object)
    - MD5 获取测试
    - 删除对象测试
    - 预签名 URL 生成测试
    - 边界条件测试 (连接失败、配置错误、清理失败、未初始化调用)
- AioS3Client (异步客户端):
    - init 和 shutdown 流程
    - 核心功能测试 (download, upload, upload_object, batch_download, batch_upload, batch_upload_object)
    - UploadFile 上传测试
    - BytesIO 下载测试
    - MD5 获取测试
    - 删除对象测试
    - 预签名 URL 生成测试
    - 边界条件测试
"""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from graphedu.common.config.core.storage import OssConfig
from graphedu.common.exceptions import (
    FileDeleteException,
    FileDownloadException,
    FilePresignedUrlException,
    FileUploadException,
    StorageClientException,
    StorageConnectionException,
)
from graphedu.common.resource.modules.storage.oss import AioS3Client, S3Client


# =============================================================================
# 配置 Fixtures
# =============================================================================


@pytest.fixture
def oss_config_minio() -> OssConfig:
    """提供 MinIO 配置。"""
    return OssConfig(
        provider="minio",
        endpoint="http://localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        use_ssl=False,
        bucket="test-bucket",
        upload_from="/tmp/uploads",
        download_to="/tmp/downloads",
    )


@pytest.fixture
def oss_config_dict() -> dict:
    """提供字典形式的配置。"""
    return {
        "provider": "aws",
        "endpoint": "https://s3.amazonaws.com",
        "access_key=": "test_access_key",
        "secret_key": "test_secret_key",
        "use_ssl": True,
        "bucket": "test-bucket",
        "upload_from": "/tmp/uploads",
        "download_to": "/tmp/downloads",
    }


@pytest.fixture
def oss_config_aliyun() -> OssConfig:
    """提供阿里云 OSS 配置。"""
    return OssConfig(
        provider="aliyun",
        endpoint="https://oss-cn-hangzhou.aliyuncs.com",
        access_key="aliyun_access_key",
        secret_key="aliyun_secret_key",
        use_ssl=True,
        bucket="aliyun-bucket",
        upload_from="/tmp/uploads",
        download_to="/tmp/downloads",
    )


# =============================================================================
# Mock 对象 Fixtures - 同步客户端
# =============================================================================


@pytest.fixture
def mock_boto3_s3_client() -> MagicMock:
    """提供 Mock 的 boto3 S3 客户端。"""
    mock_client = MagicMock()
    mock_client.download_file = MagicMock()
    mock_client.upload_file = MagicMock()
    mock_client.upload_fileobj = MagicMock()
    mock_client.delete_object = MagicMock()
    mock_client.head_object = MagicMock()
    mock_client.generate_presigned_url = MagicMock()
    mock_client.close = MagicMock()
    return mock_client


@pytest.fixture
def mock_botocore_config() -> MagicMock:
    """提供 Mock 的 botocore Config 对象。"""
    mock_config = MagicMock()
    return mock_config


# =============================================================================
# Mock 对象 Fixtures - 异步客户端
# =============================================================================


@pytest.fixture
def mock_aiobotocore_session() -> MagicMock:
    """提供 Mock 的 aiobotocore session。"""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def mock_aiobotocore_client() -> AsyncMock:
    """提供 Mock 的 aiobotocore S3 客户端。"""
    mock_client = AsyncMock()
    mock_client.download_file = AsyncMock()
    mock_client.upload_file = AsyncMock()
    mock_client.upload_fileobj = AsyncMock()
    mock_client.delete_object = AsyncMock()
    mock_client.head_object = AsyncMock()
    mock_client.get_object = AsyncMock()
    mock_client.generate_presigned_url = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=lambda: mock_client)
    mock_client.__aexit__ = AsyncMock()
    return mock_client


@pytest.fixture
def mock_upload_file() -> MagicMock:
    """提供 Mock 的 FastAPI UploadFile 对象。"""
    upload_file = MagicMock()
    upload_file.filename = "test_file.txt"
    upload_file.file = BytesIO(b"test content")
    return upload_file


# =============================================================================
# 未初始化的客户端 Fixtures（用于测试边界情况）
# =============================================================================


@pytest.fixture
def s3_client_uninit() -> S3Client:
    """提供未初始化的同步 S3 客户端实例。"""
    return S3Client()


@pytest.fixture
def aio_s3_client_uninit() -> AioS3Client:
    """提供未初始化的异步 S3 客户端实例。"""
    return AioS3Client()


# =============================================================================
# 同步 S3Client 测试
# =============================================================================


# -----------------------------------------------------------------------------
# 测试类：初始化边界情况
# -----------------------------------------------------------------------------


class TestS3ClientInitEdgeCases:
    """测试 S3Client 初始化的边界情况。"""

    def test_init_with_connection_error(self, s3_client_uninit, oss_config_minio):
        """测试连接失败时抛出 StorageConnectionException。"""
        with patch("graphedu.common.resource.oss.client") as mock_boto_client:
            mock_boto_client.side_effect = Exception("Connection refused")

            with pytest.raises(StorageConnectionException) as exc_info:
                s3_client_uninit.init(oss_config_minio)

            assert "Connection refused" in exc_info.value.message

    def test_init_with_dict_config(self, s3_client_uninit, oss_config_dict):
        """测试支持字典配置初始化。"""
        with patch("graphedu.common.resource.oss.client") as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            s3_client_uninit.init(oss_config_dict)

            assert isinstance(s3_client_uninit.config, OssConfig)
            assert s3_client_uninit._s3_client is not None

    def test_init_creates_boto3_client_with_correct_params(self, s3_client_uninit, oss_config_minio):
        """测试初始化时使用正确的参数创建 boto3 客户端。"""
        with patch("graphedu.common.resource.oss.client") as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            s3_client_uninit.init(oss_config_minio)

            mock_boto_client.assert_called_once()
            call_kwargs = mock_boto_client.call_args[1]
            assert call_kwargs["endpoint_url"] == oss_config_minio.endpoint
            assert call_kwargs["aws_access_key_id"] == oss_config_minio.access_key
            assert call_kwargs["aws_secret_access_key"] == oss_config_minio.secret_key
            assert call_kwargs["use_ssl"] == oss_config_minio.use_ssl


# -----------------------------------------------------------------------------
# 测试类：关闭边界情况
# -----------------------------------------------------------------------------


class TestS3ClientShutdownEdgeCases:
    """测试 S3Client 关闭的边界情况。"""

    def test_shutdown_without_init(self, s3_client_uninit):
        """测试未初始化时关闭不报错。"""
        s3_client_uninit.shutdown()
        assert s3_client_uninit._s3_client is None

    def test_shutdown_with_close_error(self, s3_client_uninit, oss_config_minio):
        """测试关闭时 close 失败的情况。"""
        with patch("graphedu.common.resource.oss.client") as mock_boto_client:
            mock_s3 = MagicMock()
            mock_s3.close.side_effect = Exception("Close failed")
            mock_boto_client.return_value = mock_s3

            s3_client_uninit.init(oss_config_minio)
            # close 方法失败不会抛出异常，只是记录日志
            s3_client_uninit.shutdown()
            assert s3_client_uninit._s3_client is None


# -----------------------------------------------------------------------------
# 测试类：属性访问
# -----------------------------------------------------------------------------


class TestS3ClientProperties:
    """测试 S3Client 的属性访问。"""

    def test_config_property_returns_config(self, s3_client_uninit, oss_config_minio):
        """测试 config 属性返回正确的配置对象。"""
        with patch("graphedu.common.resource.oss.client"):
            s3_client_uninit.init(oss_config_minio)
            assert isinstance(s3_client_uninit.config, OssConfig)
            assert s3_client_uninit.config.bucket == "test-bucket"

    def test_client_property_returns_boto3_client(self, s3_client_uninit, oss_config_minio):
        """测试 client 属性返回 boto3 客户端。"""
        with patch("graphedu.common.resource.oss.client") as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            s3_client_uninit.init(oss_config_minio)
            assert s3_client_uninit.client is not None
            assert s3_client_uninit.client == mock_s3

    def test_mode_property(self, s3_client_uninit):
        """测试 mode 属性。"""
        assert s3_client_uninit.mode == "sync"


# -----------------------------------------------------------------------------
# 测试类：核心功能 - 下载
# -----------------------------------------------------------------------------


class TestS3ClientDownload:
    """测试 S3Client 的下载功能。"""

    def test_download_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试成功下载文件。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            # Mock file operations
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/tmp/downloads/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                with patch("graphedu.common.resource.oss.ensure_path", return_value=mock_file_path):
                    result = s3_client_uninit.download("test_object.txt")

                    assert result == mock_file_path
                    mock_boto3_s3_client.download_file.assert_called_once_with(
                        oss_config_minio.bucket, "test_object.txt", str(mock_file_path)
                    )

    def test_download_with_custom_bucket_and_path(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试使用自定义 bucket 和下载路径下载文件。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/custom/path/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                with patch("graphedu.common.resource.oss.ensure_path", return_value=mock_file_path):
                    result = s3_client_uninit.download(
                        "test_object.txt", bucket_name="custom-bucket", download_path="/custom/path"
                    )

                    assert result == mock_file_path
                    mock_boto3_s3_client.download_file.assert_called_once_with("custom-bucket", "test_object.txt", str(mock_file_path))

    def test_download_failure_raises_exception(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试下载失败时抛出 FileDownloadException。"""
        mock_boto3_s3_client.download_file.side_effect = Exception("Download failed")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path", return_value=Path("/tmp/downloads")):
                with patch("graphedu.common.resource.oss.ensure_path"):
                    with pytest.raises(FileDownloadException) as exc_info:
                        s3_client_uninit.download("test_object.txt")

                    assert exc_info.value.file_name == "test_object.txt"

    def test_batch_download_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试批量下载成功。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/tmp/downloads/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                with patch("graphedu.common.resource.oss.ensure_path", return_value=mock_file_path):
                    results = s3_client_uninit.batch_download(["obj1.txt", "obj2.txt"])

                    assert len(results) == 2
                    assert mock_boto3_s3_client.download_file.call_count == 2

    def test_batch_download_partial_failure(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试批量下载部分失败。"""
        # 第一个成功，第二个失败
        mock_boto3_s3_client.download_file.side_effect = [None, Exception("Download failed")]
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/tmp/downloads/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                with patch("graphedu.common.resource.oss.ensure_path", return_value=mock_file_path):
                    results = s3_client_uninit.batch_download(["obj1.txt", "obj2.txt"])

                    assert len(results) == 2
                    # 失败的返回 None
                    assert results[1] is None


# -----------------------------------------------------------------------------
# 测试类：核心功能 - 上传
# -----------------------------------------------------------------------------


class TestS3ClientUpload:
    """测试 S3Client 的上传功能。"""

    def test_upload_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试成功上传文件。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                result = s3_client_uninit.upload("test_object.txt", file_path="/local/path/test.txt")

                assert "http://" in result or "https://" in result
                mock_boto3_s3_client.upload_file.assert_called_once()

    def test_upload_with_default_file_path(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试使用默认文件路径上传。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                s3_client_uninit.upload("test_object.txt")

                # 应该使用 config.upload_from + object_name
                call_args = mock_boto3_s3_client.upload_file.call_args
                assert call_args[0][0] == f"{oss_config_minio.upload_from}/test_object.txt"

    def test_upload_failure_raises_exception(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试上传失败时抛出 FileUploadException。"""
        mock_boto3_s3_client.upload_file.side_effect = Exception("Upload failed")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                with pytest.raises(FileUploadException) as exc_info:
                    s3_client_uninit.upload("test_object.txt", file_path="/local/path/test.txt")

                assert exc_info.value.file_name == "test_object.txt"

    def test_upload_object_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试成功上传 BytesIO 对象。"""
        data = BytesIO(b"test data")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            result = s3_client_uninit.upload_object("test_object.txt", data=data)

            assert "http://" in result or "https://" in result
            mock_boto3_s3_client.upload_fileobj.assert_called_once()

    def test_batch_upload_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试批量上传成功。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                results = s3_client_uninit.batch_upload(
                    ["/local/file1.txt", "/local/file2.txt"], ["obj1.txt", "obj2.txt"]
                )

                assert len(results) == 2
                assert mock_boto3_s3_client.upload_file.call_count == 2

    def test_batch_upload_object_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试批量上传 BytesIO 对象成功。"""
        data_list = [BytesIO(b"data1"), BytesIO(b"data2")]
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            results = s3_client_uninit.batch_upload_object(data_list, ["obj1.txt", "obj2.txt"])

            assert len(results) == 2
            assert mock_boto3_s3_client.upload_fileobj.call_count == 2


# -----------------------------------------------------------------------------
# 测试类：异步包装方法
# -----------------------------------------------------------------------------


class TestS3ClientAsyncWrappers:
    """测试 S3Client 的异步包装方法。"""

    @pytest.mark.asyncio
    async def test_async_upload_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试异步上传成功。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                result = await s3_client_uninit.async_upload("/local/path/test.txt", "test_object.txt")

                assert "http://" in result or "https://" in result

    @pytest.mark.asyncio
    async def test_async_download_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试异步下载成功。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/tmp/downloads/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                with patch("graphedu.common.resource.oss.ensure_path", return_value=mock_file_path):
                    result = await s3_client_uninit.async_download("test_object.txt")

                    assert isinstance(result, Path)

    @pytest.mark.asyncio
    async def test_async_upload_object_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试异步上传 BytesIO 对象成功。"""
        data = BytesIO(b"test data")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            result = await s3_client_uninit.async_upload_object(data, "test_object.txt")

            assert "http://" in result or "https://" in result

    @pytest.mark.asyncio
    async def test_async_wrapper_with_thread_pool(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试使用自定义线程池的异步包装方法。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    result = await s3_client_uninit.async_upload(
                        "/local/path/test.txt", "test_object.txt", pool=pool
                    )

                    assert "http://" in result or "https://" in result


# -----------------------------------------------------------------------------
# 测试类：MD5 获取
# -----------------------------------------------------------------------------


class TestS3ClientGetMD5:
    """测试 S3Client 的 MD5 获取功能。"""

    def test_get_md5_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试成功获取对象 MD5。"""
        mock_boto3_s3_client.head_object.return_value = {"ETag": '"d41d8cd98f00b204e9800998ecf8427e"'}
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            result = s3_client_uninit.get_md5("test_object.txt")

            assert result == "d41d8cd98f00b204e9800998ecf8427e"
            mock_boto3_s3_client.head_object.assert_called_once_with(Bucket=oss_config_minio.bucket, Key="test_object.txt")

    def test_get_md5_failure_raises_exception(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试获取 MD5 失败时抛出 FileDownloadException。"""
        mock_boto3_s3_client.head_object.side_effect = Exception("Object not found")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FileDownloadException) as exc_info:
                s3_client_uninit.get_md5("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# -----------------------------------------------------------------------------
# 测试类：删除对象
# -----------------------------------------------------------------------------


class TestS3ClientDeleteObject:
    """测试 S3Client 的删除对象功能。"""

    def test_delete_object_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试成功删除对象。"""
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            s3_client_uninit.delete_object("test_object.txt")

            mock_boto3_s3_client.delete_object.assert_called_once_with(Bucket=oss_config_minio.bucket, Key="test_object.txt")

    def test_delete_object_with_ignore_error(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试删除对象时忽略错误。"""
        mock_boto3_s3_client.delete_object.side_effect = Exception("Object not found")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            # 不应该抛出异常
            s3_client_uninit.delete_object("test_object.txt", ignore_existence_error=True)

    def test_delete_object_failure_raises_exception(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试删除失败时抛出 FileDeleteException。"""
        mock_boto3_s3_client.delete_object.side_effect = Exception("Delete failed")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FileDeleteException) as exc_info:
                s3_client_uninit.delete_object("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# -----------------------------------------------------------------------------
# 测试类：预签名 URL
# -----------------------------------------------------------------------------


class TestS3ClientGeneratePresignedUrl:
    """测试 S3Client 的预签名 URL 生成功能。"""

    def test_generate_presigned_url_success(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试成功生成预签名 URL。"""
        mock_boto3_s3_client.generate_presigned_url.return_value = "https://example.com/presigned-url"
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            result = s3_client_uninit.generate_presigned_url("test_object.txt")

            assert result == "https://example.com/presigned-url"
            mock_boto3_s3_client.generate_presigned_url.assert_called_once()

    def test_generate_presigned_url_with_custom_expiration(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试使用自定义过期时间生成预签名 URL。"""
        mock_boto3_s3_client.generate_presigned_url.return_value = "https://example.com/presigned-url"
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            s3_client_uninit.generate_presigned_url("test_object.txt", expiration=7200)

            call_kwargs = mock_boto3_s3_client.generate_presigned_url.call_args[1]
            assert call_kwargs["ExpiresIn"] == 7200

    def test_generate_presigned_url_failure_raises_exception(self, s3_client_uninit, oss_config_minio, mock_boto3_s3_client):
        """测试生成预签名 URL 失败时抛出 FilePresignedUrlException。"""
        from botocore.exceptions import ClientError

        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mock_boto3_s3_client.generate_presigned_url.side_effect = ClientError(error_response, "GeneratePresignedUrl")
        with patch("graphedu.common.resource.oss.client", return_value=mock_boto3_s3_client):
            s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FilePresignedUrlException) as exc_info:
                s3_client_uninit.generate_presigned_url("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# =============================================================================
# 异步 AioS3Client 测试
# =============================================================================


# -----------------------------------------------------------------------------
# 测试类：初始化边界情况
# -----------------------------------------------------------------------------


class TestAioS3ClientInitEdgeCases:
    """测试 AioS3Client 初始化的边界情况。"""

    @pytest.mark.asyncio
    async def test_init_with_import_error(self, aio_s3_client_uninit, oss_config_minio):
        """测试 aiobotocore 未安装时抛出 ImportError。"""
        with patch("graphedu.common.resource.oss.get_session", side_effect=ImportError):
            with pytest.raises(ImportError) as exc_info:
                await aio_s3_client_uninit.init(oss_config_minio)

            assert "aiobotocore" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_init_with_connection_error(self, aio_s3_client_uninit, oss_config_minio):
        """测试连接失败时抛出 StorageConnectionException。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")

            with pytest.raises(StorageConnectionException) as exc_info:
                await aio_s3_client_uninit.init(oss_config_minio)

            assert "Connection failed" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_init_with_dict_config(self, aio_s3_client_uninit, oss_config_dict):
        """测试支持字典配置初始化。"""
        with patch("graphedu.common.resource.oss.get_session"):
            await aio_s3_client_uninit.init(oss_config_dict)

            assert isinstance(aio_s3_client_uninit.config, OssConfig)
            assert aio_s3_client_uninit._session is not None

    @pytest.mark.asyncio
    async def test_init_creates_session_with_correct_config(self, aio_s3_client_uninit, oss_config_minio):
        """测试初始化时使用正确的配置创建 session。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)

            mock_get_session.assert_called_once()
            assert aio_s3_client_uninit._client_config is not None
            assert aio_s3_client_uninit._client_config["service_name"] == "s3"
            assert aio_s3_client_uninit._client_config["endpoint_url"] == oss_config_minio.endpoint


# -----------------------------------------------------------------------------
# 测试类：关闭边界情况
# -----------------------------------------------------------------------------


class TestAioS3ClientShutdownEdgeCases:
    """测试 AioS3Client 关闭的边界情况。"""

    @pytest.mark.asyncio
    async def test_shutdown_without_init(self, aio_s3_client_uninit):
        """测试未初始化时关闭不报错。"""
        await aio_s3_client_uninit.shutdown()
        assert aio_s3_client_uninit._session is None

    @pytest.mark.asyncio
    async def test_shutdown_success(self, aio_s3_client_uninit, oss_config_minio):
        """测试成功关闭。"""
        with patch("graphedu.common.resource.oss.get_session"):
            await aio_s3_client_uninit.init(oss_config_minio)
            await aio_s3_client_uninit.shutdown()

            assert aio_s3_client_uninit._session is None
            assert aio_s3_client_uninit._client_config is None


# -----------------------------------------------------------------------------
# 测试类：属性访问和客户端创建
# -----------------------------------------------------------------------------


class TestAioS3ClientProperties:
    """测试 AioS3Client 的属性访问。"""

    @pytest.mark.asyncio
    async def test_client_without_init_raises_exception(self, aio_s3_client_uninit):
        """测试未初始化时调用 client 方法抛出异常。"""
        with pytest.raises(StorageClientException) as exc_info:
            aio_s3_client_uninit.client()

        assert "not initialized" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_client_returns_context_manager(self, aio_s3_client_uninit, oss_config_minio):
        """测试 client 方法返回上下文管理器。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value = MagicMock()
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            client_context = aio_s3_client_uninit.client()

            assert client_context is not None

    def test_mode_property(self, aio_s3_client_uninit):
        """测试 mode 属性。"""
        assert aio_s3_client_uninit.mode == "async"


# -----------------------------------------------------------------------------
# 测试类：核心功能 - 下载
# -----------------------------------------------------------------------------


class TestAioS3ClientDownload:
    """测试 AioS3Client 的下载功能。"""

    @pytest.mark.asyncio
    async def test_download_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功下载文件。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/tmp/downloads/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                result = await aio_s3_client_uninit.download("test_object.txt")

                assert isinstance(result, Path)
                mock_aiobotocore_client.download_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_failure_raises_exception(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试下载失败时抛出 FileDownloadException。"""
        mock_aiobotocore_client.download_file.side_effect = Exception("Download failed")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path", return_value=Path("/tmp/downloads")):
                with pytest.raises(FileDownloadException) as exc_info:
                    await aio_s3_client_uninit.download("test_object.txt")

                assert exc_info.value.file_name == "test_object.txt"

    @pytest.mark.asyncio
    async def test_batch_download_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试批量下载成功。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.ensure_str_path") as mock_ensure_path:
                mock_file_path = Path("/tmp/downloads/test_object.txt")
                mock_ensure_path.return_value = mock_file_path

                results = await aio_s3_client_uninit.batch_download(["obj1.txt", "obj2.txt"])

                assert len(results) == 2
                assert mock_aiobotocore_client.download_file.call_count == 2


# -----------------------------------------------------------------------------
# 测试类：核心功能 - 上传
# -----------------------------------------------------------------------------


class TestAioS3ClientUpload:
    """测试 AioS3Client 的上传功能。"""

    @pytest.mark.asyncio
    async def test_upload_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功上传文件。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                result = await aio_s3_client_uninit.upload("/local/path/test.txt", "test_object.txt")

                assert "http://" in result or "https://" in result
                mock_aiobotocore_client.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_failure_raises_exception(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试上传失败时抛出 FileUploadException。"""
        mock_aiobotocore_client.upload_file.side_effect = Exception("Upload failed")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                with pytest.raises(FileUploadException) as exc_info:
                    await aio_s3_client_uninit.upload("/local/path/test.txt", "test_object.txt")

                assert exc_info.value.file_name == "test_object.txt"

    @pytest.mark.asyncio
    async def test_upload_object_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功上传 BytesIO 对象。"""
        data = BytesIO(b"test data")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            result = await aio_s3_client_uninit.upload_object(data, "test_object.txt")

            assert "http://" in result or "https://" in result
            mock_aiobotocore_client.upload_fileobj.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_uploadfile_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client, mock_upload_file):
        """测试成功上传 FastAPI UploadFile 对象。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            result = await aio_s3_client_uninit.upload_uploadfile(mock_upload_file, "test_object.txt")

            assert "http://" in result or "https://" in result
            mock_aiobotocore_client.upload_fileobj.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_upload_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试批量上传成功。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=True):
                results = await aio_s3_client_uninit.batch_upload(
                    ["/local/file1.txt", "/local/file2.txt"], ["obj1.txt", "obj2.txt"]
                )

                assert len(results) == 2
                assert mock_aiobotocore_client.upload_file.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_upload_file_not_found_raises_exception(
        self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client
    ):
        """测试批量上传文件不存在时抛出 FileNotFoundException。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with patch("graphedu.common.resource.oss.is_file_exists", return_value=False):
                from graphedu.common.exceptions import FileNotFoundException

                with pytest.raises(FileNotFoundException):
                    await aio_s3_client_uninit.batch_upload(["/local/file1.txt"], ["obj1.txt"])

    @pytest.mark.asyncio
    async def test_batch_upload_object_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试批量上传 BytesIO 对象成功。"""
        data_list = [BytesIO(b"data1"), BytesIO(b"data2")]
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            results = await aio_s3_client_uninit.batch_upload_object(data_list, ["obj1.txt", "obj2.txt"])

            assert len(results) == 2
            assert mock_aiobotocore_client.upload_fileobj.call_count == 2


# -----------------------------------------------------------------------------
# 测试类：BytesIO 下载
# -----------------------------------------------------------------------------


class TestAioS3ClientDownloadToBytesio:
    """测试 AioS3Client 的 BytesIO 下载功能。"""

    @pytest.mark.asyncio
    async def test_download_to_bytesio_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功下载到 BytesIO。"""
        # Mock streaming response
        mock_stream = AsyncMock()
        mock_stream.read.return_value = b"test data"
        mock_aiobotocore_client.get_object.return_value = {"Body": mock_stream}

        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            result = await aio_s3_client_uninit.download_to_bytesio("test_object.txt")

            assert isinstance(result, BytesIO)
            mock_aiobotocore_client.get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_to_bytesio_failure_raises_exception(
        self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client
    ):
        """测试下载到 BytesIO 失败时抛出 FileDownloadException。"""
        mock_aiobotocore_client.get_object.side_effect = Exception("Download failed")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FileDownloadException) as exc_info:
                await aio_s3_client_uninit.download_to_bytesio("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# -----------------------------------------------------------------------------
# 测试类：MD5 获取
# -----------------------------------------------------------------------------


class TestAioS3ClientGetMD5:
    """测试 AioS3Client 的 MD5 获取功能。"""

    @pytest.mark.asyncio
    async def test_get_md5_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功获取对象 MD5。"""
        mock_aiobotocore_client.head_object.return_value = {"ETag": '"d41d8cd98f00b204e9800998ecf8427e"'}
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            result = await aio_s3_client_uninit.get_md5("test_object.txt")

            assert result == "d41d8cd98f00b204e9800998ecf8427e"
            mock_aiobotocore_client.head_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_md5_failure_raises_exception(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试获取 MD5 失败时抛出 FileDownloadException。"""
        mock_aiobotocore_client.head_object.side_effect = Exception("Object not found")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FileDownloadException) as exc_info:
                await aio_s3_client_uninit.get_md5("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# -----------------------------------------------------------------------------
# 测试类：删除对象
# -----------------------------------------------------------------------------


class TestAioS3ClientDeleteObject:
    """测试 AioS3Client 的删除对象功能。"""

    @pytest.mark.asyncio
    async def test_delete_object_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功删除对象。"""
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            await aio_s3_client_uninit.delete_object("test_object.txt")

            mock_aiobotocore_client.delete_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_object_with_ignore_error(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试删除对象时忽略错误。"""
        mock_aiobotocore_client.delete_object.side_effect = Exception("Object not found")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            # 不应该抛出异常
            await aio_s3_client_uninit.delete_object("test_object.txt", ignore_existence_error=True)

    @pytest.mark.asyncio
    async def test_delete_object_failure_raises_exception(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试删除失败时抛出 FileDeleteException。"""
        mock_aiobotocore_client.delete_object.side_effect = Exception("Delete failed")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FileDeleteException) as exc_info:
                await aio_s3_client_uninit.delete_object("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# -----------------------------------------------------------------------------
# 测试类：预签名 URL
# -----------------------------------------------------------------------------


class TestAioS3ClientGeneratePresignedUrl:
    """测试 AioS3Client 的预签名 URL 生成功能。"""

    @pytest.mark.asyncio
    async def test_generate_presigned_url_success(self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client):
        """测试成功生成预签名 URL。"""
        mock_aiobotocore_client.generate_presigned_url.return_value = "https://example.com/presigned-url"
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            result = await aio_s3_client_uninit.generate_presigned_url("test_object.txt")

            assert result == "https://example.com/presigned-url"
            mock_aiobotocore_client.generate_presigned_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_presigned_url_with_custom_expiration(
        self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client
    ):
        """测试使用自定义过期时间生成预签名 URL。"""
        mock_aiobotocore_client.generate_presigned_url.return_value = "https://example.com/presigned-url"
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            await aio_s3_client_uninit.generate_presigned_url("test_object.txt", expiration=7200)

            call_kwargs = mock_aiobotocore_client.generate_presigned_url.call_args[1]
            assert call_kwargs["ExpiresIn"] == 7200

    @pytest.mark.asyncio
    async def test_generate_presigned_url_failure_raises_exception(
        self, aio_s3_client_uninit, oss_config_minio, mock_aiobotocore_client
    ):
        """测试生成预签名 URL 失败时抛出 FilePresignedUrlException。"""
        from botocore.exceptions import ClientError

        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mock_aiobotocore_client.generate_presigned_url.side_effect = ClientError(error_response, "GeneratePresignedUrl")
        with patch("graphedu.common.resource.oss.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.create_client.return_value.__aenter__.return_value = mock_aiobotocore_client
            mock_get_session.return_value = mock_session

            await aio_s3_client_uninit.init(oss_config_minio)
            with pytest.raises(FilePresignedUrlException) as exc_info:
                await aio_s3_client_uninit.generate_presigned_url("test_object.txt")

            assert exc_info.value.file_name == "test_object.txt"


# -----------------------------------------------------------------------------
# 测试类：build_object_url
# -----------------------------------------------------------------------------


class TestAioS3ClientBuildObjectUrl:
    """测试 AioS3Client 的 build_object_url 方法。"""

    @pytest.mark.asyncio
    async def test_build_object_url(self, aio_s3_client_uninit, oss_config_minio):
        """测试构建对象 URL。"""
        with patch("graphedu.common.resource.oss.get_session"):
            await aio_s3_client_uninit.init(oss_config_minio)
            url = aio_s3_client_uninit.build_object_url("test_object.txt")

            assert "http://" in url or "https://" in url
            assert "test_object.txt" in url

    @pytest.mark.asyncio
    async def test_build_object_url_with_custom_bucket(self, aio_s3_client_uninit, oss_config_minio):
        """测试使用自定义 bucket 构建 URL。"""
        with patch("graphedu.common.resource.oss.get_session"):
            await aio_s3_client_uninit.init(oss_config_minio)
            url = aio_s3_client_uninit.build_object_url("test_object.txt", bucket_name="custom-bucket")

            assert "custom-bucket" in url
