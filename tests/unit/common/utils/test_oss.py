"""
测试 graphedu.common.utils.oss 模块
"""

from graphedu.common.utils.oss import (
    get_file_name,
    get_object_name,
    get_prefix,
)

# ==================== 测试 get_object_name ====================

class TestGetObjectNameVirtualHostedStyle:
    """测试虚拟托管样式 (virtual-hosted-style) 的 get_object_name"""

    def test_virtual_hosted_style_simple_file(self):
        """测试虚拟托管样式：简单文件"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/xxx.png"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        assert result == "xxx.png"

    def test_virtual_hosted_style_with_single_prefix(self):
        """测试虚拟托管样式：单级前缀"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix1/xxx.png"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        assert result == "prefix1/xxx.png"

    def test_virtual_hosted_style_with_multiple_prefixes(self):
        """测试虚拟托管样式：多级前缀"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix1/prefix2/xxx.png"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        assert result == "prefix1/prefix2/xxx.png"

    def test_virtual_hosted_style_with_deep_nested_path(self):
        """测试虚拟托管样式：深层嵌套路径"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/a/b/c/d/e/file.jpg"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        assert result == "a/b/c/d/e/file.jpg"

    def test_virtual_hosted_style_with_query_params(self):
        """测试虚拟托管样式：带查询参数"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix/xxx.png?Expires=123&Signature=abc"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        # 注意：函数不会去除查询参数
        assert result == "prefix/xxx.png?Expires=123&Signature=abc"

    def test_virtual_hosted_style_different_region(self):
        """测试虚拟托管样式：不同区域"""
        file_url = "https://bucket.oss-cn-beijing.aliyuncs.com/prefix/file.pdf"
        endpoint = "oss-cn-beijing.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        assert result == "prefix/file.pdf"

    def test_virtual_hosted_style_http_protocol(self):
        """测试虚拟托管样式：HTTP 协议"""
        file_url = "http://bucket.oss-cn-shanghai.aliyuncs.com/docs/report.docx"
        endpoint = "oss-cn-shanghai.aliyuncs.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=True)
        assert result == "docs/report.docx"


class TestGetObjectNamePathStyle:
    """测试路径样式 (path-style) 的 get_object_name"""

    def test_path_style_simple_file(self):
        """测试路径样式：简单文件"""
        file_url = "https://minio.example.com/bucket/xxx.png"
        endpoint = "minio.example.com"
        result = get_object_name(file_url, endpoint, virtual_host_style=False)
        assert result == "xxx.png"

    def test_path_style_with_single_prefix(self):
        """测试路径样式：单级前缀"""
        file_url = "https://minio.example.com/bucket/prefix1/xxx.png"
        endpoint = "minio.example.com"
        result = get_object_name(file_url, endpoint)
        assert result == "prefix1/xxx.png"

    def test_path_style_with_multiple_prefixes(self):
        """测试路径样式：多级前缀"""
        file_url = "https://minio.example.com/bucket/prefix1/prefix2/xxx.png"
        endpoint = "minio.example.com"
        result = get_object_name(file_url, endpoint)
        assert result == "prefix1/prefix2/xxx.png"

    def test_path_style_with_deep_nested_path(self):
        """测试路径样式：深层嵌套路径"""
        file_url = "https://minio.example.com/bucket/a/b/c/d/e/file.jpg"
        endpoint = "minio.example.com"
        result = get_object_name(file_url, endpoint)
        assert result == "a/b/c/d/e/file.jpg"

    def test_path_style_with_port(self):
        """测试路径样式：带端口号"""
        file_url = "https://minio.example.com:9000/bucket/prefix/file.pdf"
        endpoint = "minio.example.com:9000"
        result = get_object_name(file_url, endpoint)
        assert result == "prefix/file.pdf"

    def test_path_style_with_query_params(self):
        """测试路径样式：带查询参数"""
        file_url = "https://minio.example.com/bucket/prefix/xxx.png?download=1"
        endpoint = "minio.example.com"
        result = get_object_name(file_url, endpoint)
        # 注意：函数不会去除查询参数
        assert result == "prefix/xxx.png?download=1"

    def test_path_style_different_bucket(self):
        """测试路径样式：不同的 bucket 名称"""
        file_url = "https://storage.example.com/my-bucket/images/photo.jpg"
        endpoint = "storage.example.com"
        result = get_object_name(file_url, endpoint)
        assert result == "images/photo.jpg"

    def test_path_style_long_bucket_name(self):
        """测试路径样式：长的 bucket 名称"""
        file_url = "https://minio.example.com/my-app-bucket-prod/folder/document.pdf"
        endpoint = "minio.example.com"
        result = get_object_name(file_url, endpoint)
        assert result == "folder/document.pdf"


# ==================== 测试 get_file_name ====================

class TestGetFileName:
    """测试 get_file_name 函数"""

    def test_simple_filename(self):
        """测试简单文件名"""
        file_url = "https://example.com/file.txt"
        result = get_file_name(file_url)
        assert result == "file.txt"

    def test_filename_with_extension(self):
        """测试带扩展名的文件名"""
        file_url = "https://example.com/document.pdf"
        result = get_file_name(file_url)
        assert result == "document.pdf"

    def test_filename_with_path(self):
        """测试带路径的文件名"""
        file_url = "https://example.com/path/to/file.jpg"
        result = get_file_name(file_url)
        assert result == "file.jpg"

    def test_filename_with_deep_path(self):
        """测试深层嵌套路径的文件名"""
        file_url = "https://example.com/a/b/c/d/e/filename.png"
        result = get_file_name(file_url)
        assert result == "filename.png"

    def test_filename_with_multiple_extensions(self):
        """测试带多个扩展名的文件名"""
        file_url = "https://example.com/path/to/file.tar.gz"
        result = get_file_name(file_url)
        assert result == "file.tar.gz"

    def test_filename_with_query_params(self):
        """测试带查询参数的文件名"""
        file_url = "https://example.com/file.png?width=200&height=150"
        result = get_file_name(file_url)
        # 注意：函数不会去除查询参数
        assert result == "file.png?width=200&height=150"

    def test_filename_with_fragment(self):
        """测试带片段的文件名"""
        file_url = "https://example.com/document.html#section1"
        result = get_file_name(file_url)
        # 注意：函数不会去除片段
        assert result == "document.html#section1"

    def test_filename_with_special_chars(self):
        """测试文件名包含特殊字符"""
        file_url = "https://example.com/path/my-file_v2.0_final.pdf"
        result = get_file_name(file_url)
        assert result == "my-file_v2.0_final.pdf"

    def test_filename_with_dots(self):
        """测试文件名包含多个点"""
        file_url = "https://example.com/path/file.name.with.dots.txt"
        result = get_file_name(file_url)
        assert result == "file.name.with.dots.txt"

    def test_filename_without_extension(self):
        """测试无扩展名的文件名"""
        file_url = "https://example.com/path/README"
        result = get_file_name(file_url)
        assert result == "README"

    def test_filename_virtual_hosted_style(self):
        """测试虚拟托管样式的 URL"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix1/prefix2/xxx.png"
        result = get_file_name(file_url)
        assert result == "xxx.png"

    def test_filename_path_style(self):
        """测试路径样式的 URL"""
        file_url = "https://minio.example.com/bucket/prefix1/prefix2/xxx.png"
        result = get_file_name(file_url)
        assert result == "xxx.png"

    def test_filename_with_port(self):
        """测试带端口号的 URL"""
        file_url = "https://minio.example.com:9000/bucket/path/to/file.docx"
        result = get_file_name(file_url)
        assert result == "file.docx"

    def test_filename_unicode(self):
        """测试文件名包含 Unicode 字符"""
        file_url = "https://example.com/path/文件名.pdf"
        result = get_file_name(file_url)
        assert result == "文件名.pdf"

    def test_filename_with_spaces(self):
        """测试文件名包含空格（URL 编码）"""
        file_url = "https://example.com/path/my%20file.txt"
        result = get_file_name(file_url)
        assert result == "my%20file.txt"

    def test_filename_empty_url(self):
        """测试空 URL"""
        file_url = ""
        result = get_file_name(file_url)
        assert result == ""

    def test_filename_no_slash(self):
        """测试没有斜杠的 URL"""
        file_url = "https://example.com"
        result = get_file_name(file_url)
        # get_file_name 使用 split("/")[-1]，将 https://example.com 分割
        # ['https:', '', 'example.com']，返回最后一个元素
        assert result == "example.com"

    def test_filename_trailing_slash(self):
        """测试以斜杠结尾的 URL"""
        file_url = "https://example.com/path/"
        result = get_file_name(file_url)
        assert result == ""


# ==================== 测试 get_prefix ====================

class TestGetPrefixVirtualHostedStyle:
    """测试虚拟托管样式 (virtual-hosted-style) 的 get_prefix"""

    def test_virtual_hosted_style_no_prefix(self):
        """测试虚拟托管样式：无前缀"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/xxx.png"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        assert result == ""

    def test_virtual_hosted_style_single_prefix(self):
        """测试虚拟托管样式：单级前缀"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix1/xxx.png"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        assert result == "prefix1"

    def test_virtual_hosted_style_multiple_prefixes(self):
        """测试虚拟托管样式：多级前缀"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix1/prefix2/xxx.png"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        assert result == "prefix1/prefix2"

    def test_virtual_hosted_style_deep_nested_prefix(self):
        """测试虚拟托管样式：深层嵌套前缀"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/a/b/c/d/file.jpg"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        assert result == "a/b/c/d"

    def test_virtual_hosted_style_different_region(self):
        """测试虚拟托管样式：不同区域"""
        file_url = "https://bucket.oss-cn-beijing.aliyuncs.com/images/2024/photo.jpg"
        endpoint = "oss-cn-beijing.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        assert result == "images/2024"

    def test_virtual_hosted_style_http_protocol(self):
        """测试虚拟托管样式：HTTP 协议"""
        file_url = "http://bucket.oss-cn-hangzhou.aliyuncs.com/data/file.csv"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        assert result == "data"

    def test_virtual_hosted_style_with_query_params(self):
        """测试虚拟托管样式：带查询参数"""
        file_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/prefix/file.png?expires=123"
        endpoint = "oss-cn-hangzhou.aliyuncs.com"
        result = get_prefix(file_url, endpoint, virtual_host_style=True)
        # 前缀是最后一个 / 之前的内容，不包含文件名和查询参数
        assert result == "prefix"


class TestGetPrefixPathStyle:
    """测试路径样式 (path-style) 的 get_prefix"""

    def test_path_style_no_prefix(self):
        """测试路径样式：无前缀"""
        file_url = "https://minio.example.com/bucket/xxx.png"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == ""

    def test_path_style_single_prefix(self):
        """测试路径样式：单级前缀"""
        file_url = "https://minio.example.com/bucket/prefix1/xxx.png"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == "prefix1"

    def test_path_style_multiple_prefixes(self):
        """测试路径样式：多级前缀"""
        file_url = "https://minio.example.com/bucket/prefix1/prefix2/xxx.png"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == "prefix1/prefix2"

    def test_path_style_deep_nested_prefix(self):
        """测试路径样式：深层嵌套前缀"""
        file_url = "https://minio.example.com/bucket/a/b/c/d/file.jpg"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == "a/b/c/d"

    def test_path_style_with_port(self):
        """测试路径样式：带端口号"""
        file_url = "https://minio.example.com:9000/bucket/images/photo.jpg"
        endpoint = "minio.example.com:9000"
        result = get_prefix(file_url, endpoint)
        assert result == "images"

    def test_path_style_long_bucket_name(self):
        """测试路径样式：长的 bucket 名称"""
        file_url = "https://minio.example.com/my-app-bucket-prod/folder/document.pdf"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == "folder"

    def test_path_style_different_bucket(self):
        """测试路径样式：不同的 bucket 名称"""
        file_url = "https://storage.example.com/assets/images/logo.png"
        endpoint = "storage.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == "images"

    def test_path_style_bucket_with_hyphen(self):
        """测试路径样式：bucket 名称包含连字符"""
        file_url = "https://minio.example.com/my-bucket/docs/readme.pdf"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        assert result == "docs"

    def test_path_style_with_query_params(self):
        """测试路径样式：带查询参数"""
        file_url = "https://minio.example.com/bucket/prefix/file.png?download=1"
        endpoint = "minio.example.com"
        result = get_prefix(file_url, endpoint)
        # 前缀是最后一个 / 之前的内容，不包含文件名和查询参数
        assert result == "prefix"
