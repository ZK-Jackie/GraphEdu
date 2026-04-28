"""Infrastructure Resource Components

This module provides infrastructure-related resources,
including HTTP clients, object storage clients, and S3 configurations.

Usage:
    from graphedu.common.resource.infrastructure import (
        HttpClient,
        AsyncHttpClient,
        S3Client,
        AioS3Client,
        S3Provider,
        S3ProviderConfig,
        get_provider_config,
    )
"""

from .request import AsyncHttpClient, HttpClient

__all__ = [
    # ========== HTTP Client Resources ==========
    "AsyncHttpClient",
    "HttpClient",
]
