"""代码生成器 API Router 层 (Controller层)

职责：
1. 接收 HTTP 请求，使用 DTO 进行参数验证
2. 调用 Service 层处理业务逻辑
3. 响应 VO 对象给前端
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.toolv2.generator import (
    GenDbTableQueryDTO,
    GenTableImportDTO,
    GenTableQueryDTO,
    GenTableUpdateDTO,
)
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.toolv2.generator import GenTableEditInfoVO, GenTableInfoVO, GenTableListVO
from graphedu.common.resource.deps import get_db
from graphedu.generator.services import CodeGeneratorService
from graphedu.security.auth import SecurityService

# 创建路由
gen_controller = APIRouter(prefix="/system/tool/gen", tags=["代码生成"])


# ==============================================================================
# 代码生成业务表管理
# ==============================================================================


@gen_controller.get(
    "/list",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[PageResponse[GenTableListVO]],
)
async def get_gen_table_list(
    query_object: GenTableQueryDTO = Depends(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取代码生成业务表列表"""
    result = await CodeGeneratorService.get_table_list(query_db, query_object)
    return ResponseUtil.success(data=result)


@gen_controller.get(
    "/db/list",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[PageResponse[GenTableInfoVO]],
)
async def get_db_table_list(
    query_object: GenDbTableQueryDTO = Depends(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取数据库表列表（未导入的表）"""
    result = await CodeGeneratorService.get_db_table_list(query_db, query_object)
    return ResponseUtil.success(data=result)


@gen_controller.post(
    "/importTable",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[Empty],
)
async def import_gen_table(
    import_dto: GenTableImportDTO,
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    """导入数据库表到代码生成器"""
    table_names = import_dto.table_names.split(",") if import_dto.table_names else []
    await CodeGeneratorService.import_tables(query_db, table_names, current_user)
    return ResponseUtil.success(msg="导入成功")


@gen_controller.put(
    "",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[Empty],
)
async def update_gen_table(
    table_update: GenTableUpdateDTO,
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    """更新代码生成业务表配置"""
    await CodeGeneratorService.update_table(query_db, table_update, current_user)
    return ResponseUtil.success(msg="更新成功")


@gen_controller.delete(
    "/{table_ids}",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[Empty],
)
async def delete_gen_table(
    table_ids: str = Path(..., pattern="^[0-9,]+$", description="业务表ID，多个以逗号分隔"),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    """删除代码生成业务表"""
    table_id_list = [int(table_id) for table_id in table_ids.split(",") if table_id]
    await CodeGeneratorService.delete_table(query_db, table_id_list, current_user)
    return ResponseUtil.success(msg="删除成功")


@gen_controller.get(
    "/{table_id}",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[GenTableEditInfoVO],
)
async def get_gen_table_detail(
    table_id: int = Path(..., description="业务表ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取代码生成业务表详细信息（用于编辑页面）"""
    table_detail = await CodeGeneratorService.get_table_detail(query_db, table_id)
    all_tables = await CodeGeneratorService.get_all_tables(query_db)

    result = GenTableEditInfoVO(
        info=table_detail,
        rows=table_detail.columns,
        tables=all_tables,
    )
    return ResponseUtil.success(data=result)


@gen_controller.get(
    "/sync/{table_name}",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[Empty],
)
async def sync_gen_table(
    table_name: str = Path(..., description="表名称"),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    """同步数据库表结构"""
    await CodeGeneratorService.sync_table(query_db, table_name, current_user)
    return ResponseUtil.success(msg="同步成功")


# ==============================================================================
# 代码生成功能
# ==============================================================================


@gen_controller.get(
    "/preview/{table_id}",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[dict[str, str]],
)
async def preview_gen_code(
    table_id: int = Path(..., description="业务表ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """预览生成代码"""
    result = await CodeGeneratorService.preview_code(query_db, table_id)
    return ResponseUtil.success(data=result)


@gen_controller.get(
    "/genCode/{table_name}",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[str],
)
async def generate_code(
    table_name: str = Path(..., description="表名称"),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    """生成代码到本地"""
    result = await CodeGeneratorService.generate_code(query_db, table_name, current_user)
    return ResponseUtil.success(msg=result)


@gen_controller.get(
    "/batchGenCode",
    dependencies=[Depends(SecurityService.get_current_user)],
)
async def batch_generate_code(
    tables: str = Query(..., description="表名称，多个以逗号分隔"),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    """批量生成代码（下载 ZIP）"""
    table_names = tables.split(",") if tables else []
    zip_data = await CodeGeneratorService.batch_generate_code(query_db, table_names)
    return Response(
        content=zip_data, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=code.zip"}
    )
