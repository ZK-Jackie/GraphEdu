"""
测试 graphedu.common.resource.modules.database.oss 模块

提供了对 S3Client 和 AioS3Client 的全面测试，
包括初始化、文件上传下载、批量操作、预签名 URL 等功能。
"""
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from graphedu.common.config.modules.datasource.oss import OssConfig
from graphedu.common.exceptions import (
    FileDeleteException,
    FileDownloadException,
    FilePresignedUrlException,
    FileUploadException,
    StorageClientException,
    StorageConnectionException,
)
from graphedu.common.resource.modules.database.oss import AioS3Client, S3Client
from graphedu.common.resource.modules.database.s3_adaptation.s3_config import (
    S3ProviderConfig,
    get_provider_config,
)

# ============================================================================
# 测试 Fixtures
# ============================================================================

@pytest.fixture
def mock_oss_config():
    """创建模拟的 OSS 配置"""
    return OssConfig(
        provider="minio",
        endpoint="http://localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        use_ssl=False,
        bucket="test-bucket",
        upload_from="/tmp/upload",
        download_to="/tmp/download",
    )


@pytest.fixture
def mock_boto3_client():
    """创建模拟的 boto3 S3 客户端"""
    mock_client = MagicMock()
    mock_client.close = MagicMock()
    mock_client.upload_file = MagicMock()
    mock_client.upload_fileobj = MagicMock()
    mock_client.download_file = MagicMock()
    mock_client.delete_object = MagicMock()
    mock_client.head_object = MagicMock(return_value={"ETag": '"abc123"'})
    mock_client.generate_presigned_url = MagicMock(return_value="http://localhost:9000/test-bucket/test-file?presigned=true")
    return mock_client


@pytest.fixture
def mock_aiobotocore_client():
    """创建模拟的 aiobotocore S3 客户端"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    mock_client.upload_fileobj = AsyncMock()
    mock_client.get_object = AsyncMock()
    mock_client.delete_object = AsyncMock()
    mock_client.head_object = AsyncMock(return_value={"ETag": '"abc123"', "ContentLength": 1024})
    mock_client.generate_presigned_url = AsyncMock(return_value="http://localhost:9000/test-bucket/test-file?presigned=true")
    return mock_client


@pytest.fixture
def mock_aiobotocore_session(mock_aiobotocore_client):
    """创建模拟的 aiobotocore session"""
    mock_session = MagicMock()
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_aiobotocore_client)
    mock_context_manager.__aexit__ = AsyncMock()
    mock_session.create_client = MagicMock(return_value=mock_context_manager)
    return mock_session


@pytest.fixture
def sample_file_content():
    """示例文件内容"""
    return b"This is a test file content for OSS operations."


@pytest.fixture
def sample_bytesio(sample_file_content):
    """示例 BytesIO 对象"""
    return BytesIO(sample_file_content)


@pytest.fixture
def temp_upload_dir(tmp_path):
    """临时上传目录"""
    upload_dir = tmp_path / "upload"
    upload_dir.mkdir()
    return str(upload_dir)


@pytest.fixture
def temp_download_dir(tmp_path):
    """临时下载目录"""
    download_dir = tmp_path / "download"
    download_dir.mkdir()
    return str(download_dir)


@pytest.fixture
def sample_local_file(temp_upload_dir):
    """创建本地测试文件"""
    file_path = Path(temp_upload_dir) / "test_file.txt"
    file_path.write_text("Test content for upload")
    return str(file_path)


# ============================================================================
# 测试 S3ProviderConfig
# ============================================================================

class TestS3ProviderConfig:
    """测试 S3 服务商配置"""

    def test_get_provider_config_aws(self):
        """测试获取 AWS 配置"""
        config = get_provider_config("aws")
        assert config.addressing_style == "virtual"
        assert config.signature_version == "s3v4"
        assert config.force_path_style is False

    def test_get_provider_config_minio(self):
        """测试获取 MinIO 配置"""
        config = get_provider_config("minio")
        assert config.addressing_style == "path"
        assert config.signature_version == "s3v4"
        assert config.force_path_style is True

    def test_get_provider_config_aliyun(self):
        """测试获取阿里云配置"""
        config = get_provider_config("aliyun")
        assert config.addressing_style == "virtual"
        assert config.signature_version == "s3"

    def test_get_provider_config_generic(self):
        """测试获取通用配置"""
        config = get_provider_config("generic")
        assert config.addressing_style == "path"
        assert config.force_path_style is True

    def test_get_provider_config_unknown_fallback(self):
        """测试未知服务商回退到通用配置"""
        config = get_provider_config("unknown_provider")
        assert config.addressing_style == "path"

    def test_build_object_url_path_style(self):
        """测试路径样式 URL 构建"""
        config = S3ProviderConfig(
            addressing_style="path",
            url_template="{endpoint}/{bucket}/{object}"
        )
        url = config.build_object_url(
            endpoint="http://localhost:9000",
            bucket="test-bucket",
            object_name="folder/file.txt",
            use_ssl=False
        )
        assert url == "http://localhost:9000/test-bucket/folder/file.txt"

    def test_build_object_url_virtual_style(self):
        """测试虚拟托管样式 URL 构建"""
        config = S3ProviderConfig(
            addressing_style="virtual",
            url_template="{bucket}.{endpoint}/{object}"
        )
        url = config.build_object_url(
            endpoint="oss-cn-hangzhou.aliyuncs.com",
            bucket="my-bucket",
            object_name="file.pdf",
            use_ssl=True
        )
        assert url == "https://my-bucket.oss-cn-hangzhou.aliyuncs.com/file.pdf"

    def test_build_object_url_with_ssl(self):
        """测试使用 SSL 的 URL 构建"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )
        url = config.build_object_url(
            endpoint="minio.example.com",
            bucket="bucket",
            object_name="file.jpg",
            use_ssl=True
        )
        assert url.startswith("https://")

    def test_build_object_url_without_ssl(self):
        """测试不使用 SSL 的 URL 构建"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )
        url = config.build_object_url(
            endpoint="minio.example.com",
            bucket="bucket",
            object_name="file.jpg",
            use_ssl=False
        )
        assert url.startswith("http://")


# ============================================================================
# 测试 S3Client (同步客户端)
# ============================================================================

class TestS3ClientInit:
    """测试 S3Client 初始化"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_init_with_dict_config(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试使用字典配置初始化"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config.model_dump())

        assert client.config is not None
        assert client.config.provider == "minio"
        assert client._s3_client is not None

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_init_with_ossconfig(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试使用 OssConfig 对象初始化"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        assert client.config == mock_oss_config
        assert client._s3_client is not None

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_init_connection_failure(self, mock_boto3_client_factory, mock_oss_config):
        """测试连接失败抛出异常"""
        mock_boto3_client_factory.side_effect = Exception("Connection refused")

        client = S3Client()
        with pytest.raises(StorageConnectionException) as exc_info:
            client.init(mock_oss_config)

        assert "S3" in str(exc_info.value)

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_init_different_providers(self, mock_boto3_client_factory, mock_boto3_client):
        """测试不同服务商的初始化"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        providers = ["aws", "aliyun", "minio", "tencent", "generic"]
        for provider in providers:
            config = OssConfig(provider=provider)
            client = S3Client()
            client.init(config)
            assert client.config.provider == provider


class TestS3ClientShutdown:
    """测试 S3Client 关闭"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_shutdown(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试正常关闭"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)
        assert client._s3_client is not None

        client.shutdown()
        assert client._s3_client is None
        mock_boto3_client.close.assert_called_once()

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_shutdown_when_not_initialized(self, mock_boto3_client_factory, mock_oss_config):
        """测试未初始化时的关闭"""
        mock_boto3_client_factory.return_value = MagicMock()

        client = S3Client()
        # 不调用 init，直接 shutdown
        client.shutdown()  # 应该不抛出异常
        assert client._s3_client is None


class TestS3ClientUpload:
    """测试 S3Client 上传功能"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_upload_file_success(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_local_file):
        """测试成功上传文件"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = client.upload(object_name="test_file.txt", file_path=sample_local_file)

        mock_boto3_client.upload_file.assert_called_once()
        assert url == "http://localhost:9000/test-bucket/test_file.txt"

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_upload_file_failure(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_local_file):
        """测试上传文件失败"""
        mock_boto3_client.upload_file.side_effect = Exception("Upload failed")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        with pytest.raises(FileUploadException):
            client.upload(object_name="test_file.txt", file_path=sample_local_file)

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_upload_object_with_bytesio(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_bytesio):
        """测试上传 BytesIO 对象"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = client.upload_object(object_name="bytesio_file.dat", data=sample_bytesio)

        mock_boto3_client.upload_fileobj.assert_called_once()
        assert url == "http://localhost:9000/test-bucket/bytesio_file.dat"

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_upload_object_failure(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_bytesio):
        """测试上传 BytesIO 对象失败"""
        mock_boto3_client.upload_fileobj.side_effect = Exception("Upload failed")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        with pytest.raises(FileUploadException):
            client.upload_object(object_name="file.dat", data=sample_bytesio)


class TestS3ClientDownload:
    """测试 S3Client 下载功能"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_download_file_success(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_download_dir):
        """测试成功下载文件"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        file_path = client.download(object_name="remote_file.txt", download_path=temp_download_dir)

        mock_boto3_client.download_file.assert_called_once()
        assert file_path is not None
        assert str(file_path).endswith("remote_file.txt")

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_download_file_failure(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_download_dir):
        """测试下载文件失败"""
        mock_boto3_client.download_file.side_effect = Exception("Download failed")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        with pytest.raises(FileDownloadException):
            client.download(object_name="remote_file.txt", download_path=temp_download_dir)


class TestS3ClientDelete:
    """测试 S3Client 删除功能"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_delete_object_success(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试成功删除对象"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        client.delete_object(object_name="file_to_delete.txt")

        mock_boto3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="file_to_delete.txt"
        )

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_delete_object_failure(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试删除对象失败"""
        mock_boto3_client.delete_object.side_effect = Exception("Delete failed")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        with pytest.raises(FileDeleteException):
            client.delete_object(object_name="file.txt")

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_delete_object_ignore_error(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试删除对象时忽略错误"""
        mock_boto3_client.delete_object.side_effect = Exception("Not found")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        # 不应抛出异常
        client.delete_object(object_name="file.txt", ignore_existence_error=True)


class TestS3ClientGetMd5:
    """测试 S3Client 获取 MD5 功能"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_get_md5_success(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试成功获取 MD5"""
        mock_boto3_client.head_object.return_value = {"ETag": '"abc123def456"'}
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        md5 = client.get_md5(object_name="file.txt")

        assert md5 == "abc123def456"
        mock_boto3_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="file.txt"
        )

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_get_md5_failure(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试获取 MD5 失败"""
        mock_boto3_client.head_object.side_effect = Exception("Head failed")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        with pytest.raises(FileDownloadException):
            client.get_md5(object_name="file.txt")


class TestS3ClientPresignedUrl:
    """测试 S3Client 预签名 URL 功能"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_generate_presigned_url_get_object(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试生成 GET 预签名 URL"""
        mock_boto3_client.generate_presigned_url.return_value = "http://localhost:9000/test-bucket/file.txt?signature=xxx"
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = client.generate_presigned_url(object_name="file.txt", operation="get_object")

        assert "signature=xxx" in url
        mock_boto3_client.generate_presigned_url.assert_called_once()

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_generate_presigned_url_put_object(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试生成 PUT 预签名 URL"""
        mock_boto3_client.generate_presigned_url.return_value = "http://localhost:9000/test-bucket/upload.txt?signature=yyy"
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = client.generate_presigned_url(object_name="upload.txt", operation="put_object")

        assert "signature=yyy" in url

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_generate_presigned_url_with_expiration(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试生成带过期时间的预签名 URL"""
        mock_boto3_client.generate_presigned_url.return_value = "http://localhost:9000/test-bucket/file.txt?expires=7200"
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = client.generate_presigned_url(object_name="file.txt", expiration=7200)

        assert "expires=7200" in url

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_generate_presigned_url_failure(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试生成预签名 URL 失败"""
        from botocore.exceptions import ClientError

        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mock_boto3_client.generate_presigned_url.side_effect = ClientError(error_response, "GeneratePresignedUrl")
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        with pytest.raises(FilePresignedUrlException):
            client.generate_presigned_url(object_name="file.txt")


class TestS3ClientBatchOperations:
    """测试 S3Client 批量操作"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_batch_upload(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_upload_dir):
        """测试批量上传"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        # 创建多个测试文件
        file_paths = []
        object_names = []
        for i in range(3):
            file_path = Path(temp_upload_dir) / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            file_paths.append(str(file_path))
            object_names.append(f"file_{i}.txt")

        client = S3Client()
        client.init(mock_oss_config)

        results = client.batch_upload(file_paths=file_paths, object_names=object_names)

        assert len(results) == 3
        assert all(r is not None for r in results)
        assert mock_boto3_client.upload_file.call_count == 3

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_batch_upload_with_failures(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_upload_dir):
        """测试批量上传时部分失败"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        # 设置上传第二次失败
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Upload failed")

        mock_boto3_client.upload_file.side_effect = side_effect

        # 创建测试文件
        file_paths = []
        object_names = []
        for i in range(3):
            file_path = Path(temp_upload_dir) / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            file_paths.append(str(file_path))
            object_names.append(f"file_{i}.txt")

        client = S3Client()
        client.init(mock_oss_config)

        results = client.batch_upload(file_paths=file_paths, object_names=object_names)

        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is None  # 第二个失败
        assert results[2] is not None

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_batch_download(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_download_dir):
        """测试批量下载"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        object_names = ["file1.txt", "file2.txt", "file3.txt"]

        client = S3Client()
        client.init(mock_oss_config)

        results = client.batch_download(object_names=object_names, download_path=temp_download_dir)

        assert len(results) == 3
        assert all(r is not None for r in results)
        assert mock_boto3_client.download_file.call_count == 3

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_batch_upload_object(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试批量上传 BytesIO 对象"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        data_list = [BytesIO(b"data1"), BytesIO(b"data2"), BytesIO(b"data3")]
        object_names = ["obj1.txt", "obj2.txt", "obj3.txt"]

        client = S3Client()
        client.init(mock_oss_config)

        results = client.batch_upload_object(data=data_list, object_names=object_names)

        assert len(results) == 3
        assert all(r is not None for r in results)
        assert mock_boto3_client.upload_fileobj.call_count == 3


class TestS3ClientAsyncOperations:
    """测试 S3Client 异步操作"""

    @pytest.mark.asyncio
    @patch('graphedu.common.resource.modules.database.oss.client')
    async def test_async_upload(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_local_file):
        """测试异步上传"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = await client.async_upload(file_path=sample_local_file, object_name="async_file.txt")

        assert url == "http://localhost:9000/test-bucket/async_file.txt"
        mock_boto3_client.upload_file.assert_called_once()

    @pytest.mark.asyncio
    @patch('graphedu.common.resource.modules.database.oss.client')
    async def test_async_download(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_download_dir):
        """测试异步下载"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        file_path = await client.async_download(object_name="async_file.txt", download_path=temp_download_dir)

        assert file_path is not None
        mock_boto3_client.download_file.assert_called_once()

    @pytest.mark.asyncio
    @patch('graphedu.common.resource.modules.database.oss.client')
    async def test_async_upload_object(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_bytesio):
        """测试异步上传 BytesIO 对象"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = await client.async_upload_object(data=sample_bytesio, object_name="async_obj.txt")

        assert url == "http://localhost:9000/test-bucket/async_obj.txt"
        mock_boto3_client.upload_fileobj.assert_called_once()


# ============================================================================
# 测试 AioS3Client (异步客户端)
# ============================================================================

class TestAioS3ClientInit:
    """测试 AioS3Client 初始化"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_init_with_dict_config(self, mock_get_session, mock_oss_config, mock_aiobotocore_session):
        """测试使用字典配置初始化"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config.model_dump())

        assert client.config is not None
        assert client._session is not None
        assert client._client_config is not None

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_init_with_ossconfig(self, mock_get_session, mock_oss_config, mock_aiobotocore_session):
        """测试使用 OssConfig 对象初始化"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        assert client.config == mock_oss_config
        assert client._session is not None

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_init_connection_failure(self, mock_get_session, mock_oss_config):
        """测试连接失败抛出异常"""
        mock_get_session.side_effect = Exception("Connection failed")

        client = AioS3Client()
        with pytest.raises(StorageConnectionException) as exc_info:
            await client.init(mock_oss_config)

        assert "Async S3" in str(exc_info.value)


class TestAioS3ClientClientMethod:
    """测试 AioS3Client.client() 方法"""

    def test_client_before_init(self):
        """测试未初始化时调用 client()"""
        client = AioS3Client()

        with pytest.raises(StorageClientException) as exc_info:
            _ = client.client()

        assert "not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_client_after_init(self, mock_get_session, mock_oss_config, mock_aiobotocore_session):
        """测试初始化后调用 client()"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        context_manager = client.client()
        assert context_manager is not None


class TestAioS3ClientShutdown:
    """测试 AioS3Client 关闭"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_shutdown(self, mock_get_session, mock_oss_config, mock_aiobotocore_session):
        """测试正常关闭"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)
        assert client._session is not None

        await client.shutdown()
        assert client._session is None

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_shutdown_when_not_initialized(self, mock_get_session):
        """测试未初始化时的关闭"""
        client = AioS3Client()
        await client.shutdown()  # 应该不抛出异常
        assert client._session is None


class TestAioS3ClientUpload:
    """测试 AioS3Client 上传功能"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    @patch('aiofiles.open')
    async def test_upload_file_success(self, mock_aiofiles_open, mock_get_session, mock_oss_config,
                                       mock_aiobotocore_session, mock_aiobotocore_client, sample_local_file):
        """测试成功上传文件"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        url = await client.upload(file_path=sample_local_file, object_name="async_test_file.txt")

        assert url == "http://localhost:9000/test-bucket/async_test_file.txt"

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_upload_object_success(self, mock_get_session, mock_oss_config,
                                         mock_aiobotocore_session, mock_aiobotocore_client, sample_bytesio):
        """测试成功上传 BytesIO 对象"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        url = await client.upload_object(data=sample_bytesio, object_name="async_obj.dat")

        assert url == "http://localhost:9000/test-bucket/async_obj.dat"
        mock_aiobotocore_client.upload_fileobj.assert_called_once()

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_upload_object_failure(self, mock_get_session, mock_oss_config, sample_bytesio):
        """测试上传 BytesIO 对象失败"""
        # 设置一个会抛出异常的 mock
        mock_client = AsyncMock()
        mock_client.upload_fileobj = AsyncMock(side_effect=Exception("Upload failed"))

        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_client
        mock_cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.create_client = MagicMock(return_value=mock_cm)
        mock_get_session.return_value = mock_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        # 验证异常被正确抛出
        with pytest.raises(FileUploadException):
            await client.upload_object(data=sample_bytesio, object_name="file.dat")

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_upload_uploadfile(self, mock_get_session, mock_oss_config,
                                     mock_aiobotocore_session, mock_aiobotocore_client):
        """测试上传 FastAPI UploadFile"""
        from fastapi import UploadFile

        mock_get_session.return_value = mock_aiobotocore_session

        # 创建模拟的 UploadFile
        upload_file = MagicMock(spec=UploadFile)
        upload_file.file = BytesIO(b"test content")
        upload_file.filename = "upload_test.txt"

        client = AioS3Client()
        await client.init(mock_oss_config)

        url = await client.upload_uploadfile(upload_file=upload_file, object_name="uploaded_file.txt")

        assert url == "http://localhost:9000/test-bucket/uploaded_file.txt"
        mock_aiobotocore_client.upload_fileobj.assert_called_once()


class TestAioS3ClientDownload:
    """测试 AioS3Client 下载功能"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    @patch('aiofiles.open')
    async def test_download_file_success(self, mock_aiofiles_open, mock_get_session, mock_oss_config,
                                         mock_aiobotocore_session, mock_aiobotocore_client, temp_download_dir):
        """测试成功下载文件"""
        # 模拟 StreamingBody
        mock_stream = MagicMock()
        mock_stream.read = AsyncMock(side_effect=[b"chunk1", b"chunk2", b""])

        mock_aiobotocore_client.get_object.return_value = {
            "Body": mock_stream,
            "ContentLength": 12
        }
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        file_path = await client.download(object_name="remote_file.txt", file_path=temp_download_dir)

        assert file_path is not None
        assert str(file_path).endswith("remote_file.txt")

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_download_to_bytesio(self, mock_get_session, mock_oss_config,
                                       mock_aiobotocore_session, mock_aiobotocore_client):
        """测试下载到 BytesIO"""
        mock_stream = MagicMock()
        mock_stream.read = AsyncMock(side_effect=[b"data1", b"data2", b""])

        mock_aiobotocore_client.get_object.return_value = {"Body": mock_stream}
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        bytesio = await client.download_to_bytesio(object_name="file.txt")

        assert isinstance(bytesio, BytesIO)
        content = bytesio.read()
        assert content == b"data1data2"


class TestAioS3ClientDelete:
    """测试 AioS3Client 删除功能"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_delete_object_success(self, mock_get_session, mock_oss_config,
                                         mock_aiobotocore_session, mock_aiobotocore_client):
        """测试成功删除对象"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        await client.delete_object(object_name="file_to_delete.txt")

        mock_aiobotocore_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="file_to_delete.txt"
        )

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_delete_object_failure(self, mock_get_session, mock_oss_config):
        """测试删除对象失败"""
        # 设置一个会抛出异常的 mock
        mock_client = AsyncMock()
        mock_client.delete_object = AsyncMock(side_effect=Exception("Delete failed"))

        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_client
        mock_cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.create_client = MagicMock(return_value=mock_cm)
        mock_get_session.return_value = mock_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        # 验证异常被正确抛出
        with pytest.raises(FileDeleteException):
            await client.delete_object(object_name="file.txt")


class TestAioS3ClientGetMd5:
    """测试 AioS3Client 获取 MD5 功能"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_get_md5_success(self, mock_get_session, mock_oss_config,
                                   mock_aiobotocore_session, mock_aiobotocore_client):
        """测试成功获取 MD5"""
        mock_aiobotocore_client.head_object.return_value = {"ETag": '"abc123def456"'}
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        md5 = await client.get_md5(object_name="file.txt")

        assert md5 == "abc123def456"
        mock_aiobotocore_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="file.txt"
        )


class TestAioS3ClientPresignedUrl:
    """测试 AioS3Client 预签名 URL 功能"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_generate_presigned_url(self, mock_get_session, mock_oss_config,
                                          mock_aiobotocore_session, mock_aiobotocore_client):
        """测试生成预签名 URL"""
        mock_aiobotocore_client.generate_presigned_url.return_value = "http://localhost:9000/test-bucket/file.txt?signature=zzz"
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        url = await client.generate_presigned_url(object_name="file.txt")

        assert "signature=zzz" in url
        mock_aiobotocore_client.generate_presigned_url.assert_called_once()


class TestAioS3ClientBatchOperations:
    """测试 AioS3Client 批量操作"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    @patch('aiofiles.open')
    async def test_batch_upload(self, mock_aiofiles_open, mock_get_session, mock_oss_config,
                                mock_aiobotocore_session, mock_aiobotocore_client, temp_upload_dir):
        """测试批量上传"""
        mock_get_session.return_value = mock_aiobotocore_session

        # 创建测试文件
        file_paths = []
        object_names = []
        for i in range(3):
            file_path = Path(temp_upload_dir) / f"async_file_{i}.txt"
            file_path.write_text(f"Content {i}")
            file_paths.append(str(file_path))
            object_names.append(f"async_file_{i}.txt")

        client = AioS3Client()
        await client.init(mock_oss_config)

        results = await client.batch_upload(file_paths=file_paths, object_names=object_names)

        assert len(results) == 3
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    @patch('aiofiles.open')
    async def test_batch_download(self, mock_aiofiles_open, mock_get_session, mock_oss_config,
                                  mock_aiobotocore_session, mock_aiobotocore_client, temp_download_dir):
        """测试批量下载"""
        # 模拟 StreamingBody
        mock_stream = MagicMock()
        mock_stream.read = AsyncMock(side_effect=[b"data", b""])

        mock_aiobotocore_client.get_object.return_value = {
            "Body": mock_stream,
            "ContentLength": 4
        }
        mock_get_session.return_value = mock_aiobotocore_session

        object_names = ["file1.txt", "file2.txt", "file3.txt"]

        client = AioS3Client()
        await client.init(mock_oss_config)

        results = await client.batch_download(object_names=object_names, file_path=temp_download_dir)

        assert len(results) == 3
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_batch_upload_object(self, mock_get_session, mock_oss_config,
                                       mock_aiobotocore_session, mock_aiobotocore_client):
        """测试批量上传 BytesIO 对象"""
        mock_get_session.return_value = mock_aiobotocore_session

        data_list = [BytesIO(b"data1"), BytesIO(b"data2"), BytesIO(b"data3")]
        object_names = ["obj1.txt", "obj2.txt", "obj3.txt"]

        client = AioS3Client()
        await client.init(mock_oss_config)

        results = await client.batch_upload_object(data_list=data_list, object_names=object_names)

        assert len(results) == 3
        assert all(r is not None for r in results)


class TestAioS3ClientBuildObjectUrl:
    """测试 AioS3Client.build_object_url() 方法"""

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_build_object_url(self, mock_get_session, mock_oss_config, mock_aiobotocore_session):
        """测试构建对象 URL"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        url = client.build_object_url(object_name="folder/file.txt")

        assert url == "http://localhost:9000/test-bucket/folder/file.txt"

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_build_object_url_custom_bucket(self, mock_get_session, mock_oss_config, mock_aiobotocore_session):
        """测试使用自定义 bucket 构建 URL"""
        mock_get_session.return_value = mock_aiobotocore_session

        client = AioS3Client()
        await client.init(mock_oss_config)

        url = client.build_object_url(object_name="file.jpg", bucket_name="custom-bucket")

        assert url == "http://localhost:9000/custom-bucket/file.jpg"


# ============================================================================
# 测试不同服务商配置
# ============================================================================

class TestDifferentProviders:
    """测试不同服务商的配置"""

    @pytest.mark.parametrize("provider,expected_style", [
        ("aws", "virtual"),
        ("aliyun", "virtual"),
        ("minio", "path"),
        ("tencent", "virtual"),
        ("generic", "path"),
    ])
    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_provider_addressing_style(self, mock_boto3_client_factory, provider, expected_style, mock_boto3_client):
        """测试不同服务商的地址风格"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        config = OssConfig(provider=provider)
        client = S3Client()
        client.init(config)

        provider_config = get_provider_config(provider)
        assert provider_config.addressing_style == expected_style


# ============================================================================
# 边界条件和异常测试
# ============================================================================

class TestEdgeCasesAndExceptions:
    """测试边界条件和异常情况"""

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_upload_with_custom_bucket(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, sample_local_file):
        """测试使用自定义 bucket 上传"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        url = client.upload(object_name="file.txt", file_path=sample_local_file, bucket_name="custom-bucket")

        assert "custom-bucket" in url

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_download_with_custom_bucket(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_download_dir):
        """测试使用自定义 bucket 下载"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        file_path = client.download(object_name="file.txt", download_path=temp_download_dir, bucket_name="custom-bucket")

        assert file_path is not None

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_presigned_url_with_custom_params(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试生成带自定义参数的预签名 URL"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        client.generate_presigned_url(
            object_name="file.txt",
            ResponseContentType="application/pdf",
            ResponseContentDisposition="attachment; filename=test.pdf"
        )

        mock_boto3_client.generate_presigned_url.assert_called_once()
        call_args = mock_boto3_client.generate_presigned_url.call_args
        assert "ResponseContentType" in call_args[1]["Params"]
        assert "ResponseContentDisposition" in call_args[1]["Params"]

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_empty_bytesio_upload(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试上传空的 BytesIO"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        empty_bytesio = BytesIO(b"")
        url = client.upload_object(object_name="empty.txt", data=empty_bytesio)

        assert url is not None
        mock_boto3_client.upload_fileobj.assert_called_once()

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_large_file_upload(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client, temp_upload_dir):
        """测试上传大文件（模拟）"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        # 创建一个较大的文件
        large_file = Path(temp_upload_dir) / "large_file.bin"
        large_file.write_bytes(b"x" * 1024 * 1024)  # 1 MB

        client = S3Client()
        client.init(mock_oss_config)

        url = client.upload(object_name="large_file.bin", file_path=str(large_file))

        assert url is not None

    @pytest.mark.asyncio
    @patch('aiobotocore.session.get_session')
    async def test_async_client_not_initialized_error(self, mock_get_session):
        """测试异步客户端未初始化错误"""
        mock_get_session.return_value = MagicMock()

        client = AioS3Client()
        # 不调用 init

        with pytest.raises(StorageClientException):
            _ = client.client()

    @patch('graphedu.common.resource.modules.database.oss.client')
    def test_client_property(self, mock_boto3_client_factory, mock_oss_config, mock_boto3_client):
        """测试 S3Client.client 属性"""
        mock_boto3_client_factory.return_value = mock_boto3_client

        client = S3Client()
        client.init(mock_oss_config)

        assert client.client is not None
        assert client.client == mock_boto3_client

    def test_s3_client_mode_attribute(self):
        """测试 S3Client.mode 属性"""
        client = S3Client()
        assert client.mode == "sync"

    def test_aio_s3_client_mode_attribute(self):
        """测试 AioS3Client.mode 属性"""
        client = AioS3Client()
        assert client.mode == "async"
