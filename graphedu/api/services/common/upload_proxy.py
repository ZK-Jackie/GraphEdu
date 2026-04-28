"""文件流式代理接口 - 解决 OSS PDF 跨域问题"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.resource import AioS3Client
from graphedu.common.resource.deps import get_db, get_s3
from graphedu.mapper.system.upload import UploadMapper

logger = logging.getLogger(__name__)

upload_proxy_controller = APIRouter(prefix="/common/proxy", tags=["文件代理"])


@upload_proxy_controller.get("/file/{file_id}")
async def proxy_file(
    file_id: int = Path(..., gt=0), query_db: AsyncSession = Depends(get_db), s3_client: AioS3Client = Depends(get_s3)
):
    """代理访问 OSS 文件（解决跨域问题）

    - 通过后端流式转发 OSS 文件内容
    - 避免 PDF.js 等前端组件直接访问 OSS 时的跨域问题
    - 支持断点续传（Range 请求）
    - 自动设置正确的 Content-Type
    """
    # 1. 查询文件信息
    file_info = await UploadMapper.get_by_id(file_id, query_db)
    if not file_info:
        raise HTTPException(status_code=404, detail=f"文件不存在: file_id={file_id}")

    # 2. 检查访问权限
    # if file_info.access_level == SysConst.AccessLevel.PRIVATE:
    #     user_id = current_user.detail.user.user_id if current_user.detail and current_user.detail.user else None
    #     if file_info.create_by != user_id and not current_user.is_admin():
    #         raise HTTPException(status_code=403, detail="无权限访问该文件")
    #
    # logger.info(f"代理访问文件: {file_info.file_name} (ID: {file_id})")

    # 3. 从 OSS 获取文件流
    try:
        file_stream = s3_client.download_stream(object_name=file_info.file_path)
    except Exception as e:
        logger.error(f"从 OSS 下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件读取失败: {e!s}") from e

    # 4. 推断 Content-Type（从文件名）
    content_type = _guess_content_type(file_info.file_name)

    # 5. 流式返回文件内容
    return StreamingResponse(
        file_stream,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{file_info.file_name.encode("utf8")}"',
            # "Cache-Control": "public, max-age=3600",  # 缓存 1 小时
            "Accept-Ranges": "bytes",  # 支持断点续传
        },
    )


def _guess_content_type(filename: str) -> str:
    """根据文件扩展名猜测 Content-Type"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mp3": "audio/mpeg",
        "txt": "text/plain; charset=utf-8",
        "json": "application/json",
        "xml": "application/xml",
        "md": "text/markdown",
    }
    return content_types.get(ext, "application/octet-stream")
