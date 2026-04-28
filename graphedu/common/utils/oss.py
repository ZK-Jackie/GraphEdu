"""OSS (Object Storage Service) utility functions.

This module provides utilities for working with S3-compatible object storage,
including URL parsing, object name extraction, and URL generation.
"""


def get_object_name(file_url: str, endpoint: str, virtual_host_style: bool = False) -> str:
    """从文件链接中提取 object_name，支持虚拟托管样式和路径样式，例如：
    1. virtual-hosted-style (虚拟托管样式):
    https://bucket.endpoint/prefix1/prefix2/xxx.png -> prefix1/prefix2/xxx.png
    2. path-style (路径样式):
    https://endpoint/bucket/prefix1/prefix2/xxx.png -> prefix1/prefix2/xxx.png

    :param file_url: 文件链接（不带末尾的 / 符号）
    :param endpoint: OSS 服务器地址，不含协议和 bucket 名称
    :param virtual_host_style: 是否使用虚拟托管样式（默认为路径样式）
    :return: object_name
    """
    # 去掉协议前缀 (https:// 或 http://)
    url_without_protocol = file_url[file_url.find("://") + 3 :]

    if virtual_host_style:
        # 虚拟托管样式: bucket.endpoint/path/to/file
        # 找到 endpoint 的位置（在 bucket. 之后）
        endpoint_pos = url_without_protocol.find(endpoint)
        # 从 endpoint 后开始找第一个 /
        after_endpoint = url_without_protocol[endpoint_pos + len(endpoint) :]
        # 返回第一个 / 后面的内容
        return after_endpoint[after_endpoint.find("/") + 1 :]
    # 路径样式: endpoint/bucket/path/to/file
    # 找到 endpoint 的位置
    endpoint_pos = url_without_protocol.find(endpoint)
    # 从 endpoint 后开始找第二个 /（跳过 /bucket）
    after_endpoint = url_without_protocol[endpoint_pos + len(endpoint) :]
    # 找第二个 /（第一个是 /bucket，第二个是 bucket 后的）
    first_slash = after_endpoint.find("/")
    second_slash = after_endpoint.find("/", first_slash + 1)
    return after_endpoint[second_slash + 1 :]


def get_file_name(file_url: str) -> str:
    """从文件链接中提取文件名，例如：
    1. aliyun:
    https://bucket.endpoint/prefix1/prefix2/xxx.png -> xxx.png
    2. minio:
    https://endpoint/bucket/prefix1/prefix2/xxx.png -> xxx.png

    :param file_url: 文件链接
    :return: 文件名
    """
    return file_url.split("/")[-1]


def get_prefix(file_url: str, endpoint: str, virtual_host_style: bool = False) -> str:
    """从文件链接中提取前缀，例如：
    1. virtual-hosted-style (虚拟托管样式):
    https://bucket.endpoint/prefix1/prefix2/xxx.png -> prefix1/prefix2
    2. path-style (路径样式):
    https://endpoint/bucket/prefix1/prefix2/xxx.png -> prefix1/prefix2

    :param file_url: 文件链接（不带末尾的 / 符号）
    :param endpoint: OSS 服务器地址
    :param virtual_host_style: 是否使用虚拟托管样式（默认为路径样式）
    :return: 前缀
    """
    # 去掉协议前缀 (https:// 或 http://)
    url_without_protocol = file_url[file_url.find("://") + 3 :]

    if virtual_host_style:
        # 虚拟托管样式: bucket.endpoint/path/to/file
        # 找到 endpoint 的位置（在 bucket. 之后）
        endpoint_pos = url_without_protocol.find(endpoint)
        # 从 endpoint 后开始找第一个 /
        after_endpoint = url_without_protocol[endpoint_pos + len(endpoint) :]
        first_slash = after_endpoint.find("/")
        # 返回从第一个 / 到最后一个 / 之间的内容（前缀）
        last_slash = after_endpoint.rfind("/")
        return after_endpoint[first_slash + 1 : last_slash]
    # 路径样式: endpoint/bucket/path/to/file
    # 找到 endpoint 的位置
    endpoint_pos = url_without_protocol.find(endpoint)
    # 从 endpoint 后开始找第二个 /（跳过 /bucket）
    after_endpoint = url_without_protocol[endpoint_pos + len(endpoint) :]
    first_slash = after_endpoint.find("/")  # /bucket
    second_slash = after_endpoint.find("/", first_slash + 1)  # /prefix
    if second_slash == -1:
        return ""  # 没有前缀
    # 找最后一个 /
    last_slash = after_endpoint.rfind("/")
    if last_slash == second_slash:
        return ""  # 没有前缀，只有文件名
    return after_endpoint[second_slash + 1 : last_slash]


def get_oss_url(
    bucket_name: str, endpoint: str, object_name: str, virtual_host_style: bool = False, use_https: bool = True
) -> str:
    """根据 bucket 名称、endpoint 和 object_name 生成 OSS 文件链接，支持虚拟托管样式和路径样式，例如：
    1. virtual-hosted-style (虚拟托管样式):
    https://bucket.endpoint/object_name
    2. path-style (路径样式):
    https://endpoint/bucket/object_name

    :param bucket_name: 存储桶名称
    :param endpoint: OSS 服务器地址，不含协议和 bucket 名称
    :param object_name: 对象名称（包括前缀）
    :param virtual_host_style: 是否使用虚拟托管样式（默认为路径样式）
    :param use_https: 是否使用 HTTPS 协议（默认为 True）
    :return: OSS 文件链接
    """
    protocol = "https" if use_https else "http"
    if virtual_host_style:
        # 虚拟托管样式
        return f"{protocol}://{bucket_name}.{endpoint}/{object_name}"
    # 路径样式
    return f"{protocol}://{endpoint}/{bucket_name}/{object_name}"
