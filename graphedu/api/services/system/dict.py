"""字典管理路由 (Controller层)

职责：
1. 接收HTTP请求，使用DTO进行参数验证
2. 调用Service层处理业务逻辑
3. 响应VO对象给前端
"""

from fastapi import APIRouter, Depends, Path, Query
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.constants import SystemConstants
from graphedu.common.models.dto.systemv2.dict import (
    DictDataCreateDTO,
    DictDataQueryDTO,
    DictDataUpdateDTO,
    DictTypeCreateDTO,
    DictTypeQueryDTO,
    DictTypeUpdateDTO,
)
from graphedu.common.models.vo import (
    DictDataDetailVO,
    DictDataListVO,
    DictDataSimpleVO,
    DictTypeDetailVO,
    DictTypeListVO,
)
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.dict import DictDataService, DictTypeService

# 创建路由
dict_controller = APIRouter(prefix="/system/dict")


# ============== 字典类型管理 ==============


@dict_controller.get(
    "/type/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:list"))],
    response_model=ResponseType[PageResponse[DictTypeListVO]],
)
async def get_dict_type_list(dict_type_query: DictTypeQueryDTO = Query(), query_db: AsyncSession = Depends(get_db)):
    """获取字典类型列表"""
    dict_type_query_result = await DictTypeService.get_dict_type_list(query_db, dict_type_query)
    return ResponseUtil.success(data=dict_type_query_result)


@dict_controller.post(
    "/type", dependencies=[Depends(CheckUserInterfacePermit("system:dict:add"))], response_model=ResponseType[Empty]
)
@SystemLog(title="字典管理", business_type=SystemConstants.BusinessType.INSERT)
async def add_dict_type(
    dict_type_add: DictTypeCreateDTO,
    current_user=Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """新增字典类型"""
    await DictTypeService.add_dict_type(query_db, redis_session, dict_type_add, current_user)
    return ResponseUtil.success()


@dict_controller.put(
    "/type", dependencies=[Depends(CheckUserInterfacePermit("system:dict:edit"))], response_model=ResponseType
)
@SystemLog(title="字典管理", business_type=SystemConstants.BusinessType.UPDATE)
async def update_dict_type(
    dict_type_update: DictTypeUpdateDTO,
    current_user=Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """修改字典类型"""
    await DictTypeService.update_dict_type(query_db, redis_session, dict_type_update, current_user)
    return ResponseUtil.success()


@dict_controller.delete(
    "/type/{dict_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="字典管理", business_type=SystemConstants.BusinessType.DELETE)
async def delete_dict_type(
    dict_ids: str = Path(..., pattern="^[0-9,]+$", description="字典类型ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """删除字典类型"""
    delete_id_list = [int(dict_id) for dict_id in dict_ids.split(",") if dict_ids]

    await DictTypeService.delete_dict_type(query_db, redis_session, delete_id_list)
    return ResponseUtil.success()


@dict_controller.get(
    "/type/{dict_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:query"))],
    response_model=ResponseType[DictTypeDetailVO],
)
async def get_dict_type_detail(dict_id: int = Path(), query_db: AsyncSession = Depends(get_db)):
    """获取字典类型详细信息"""
    dict_type_vo = await DictTypeService.get_dict_type_detail(query_db, dict_id)
    return ResponseUtil.success(data=dict_type_vo)


@dict_controller.delete(
    "/type/refreshCache",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="字典管理", business_type=SystemConstants.BusinessType.CLEAN)
async def refresh_dict_cache(query_db: AsyncSession = Depends(get_db), redis_session: AsyncRedis = Depends(get_redis)):
    """刷新字典缓存"""
    await DictTypeService.refresh_cache(query_db, redis_session)
    return ResponseUtil.success()


@dict_controller.get(
    "/type/optionselect",
    response_model=ResponseType[list[DictTypeListVO]],
)
async def get_dict_type_options(query_db: AsyncSession = Depends(get_db)):
    """获取字典类型选项列表（用于下拉框等场景）"""
    dict_type_options = await DictTypeService.get_dict_type_options(query_db)
    return ResponseUtil.success(data=dict_type_options)


# @dict_controller.post(
#     '/type/export', response_model=ResponseType,
#     dependencies=[Depends(CheckUserInterfacePermit('system:dict:export'))]
# )
# @log(title='字典管理', business_type=5)
# async def export_dict_type(
#         request: Request,
#         dict_type_query: DictTypeQueryDTO = Body(),
#         query_db: AsyncSession = Depends(get_db)
# ):
#     """
#     导出字典类型
#     """
#     # TODO: 实现导出功能
#     return ResponseUtil.success(message='导出功能待实现')


# ============== 字典数据管理 ==============


@dict_controller.get(
    "/data/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:list"))],
    response_model=ResponseType[PageResponse[DictDataListVO]],
)
async def get_dict_data_list(dict_data_query: DictDataQueryDTO = Query(), query_db: AsyncSession = Depends(get_db)):
    """获取字典数据列表"""
    dict_data_query_result = await DictDataService.get_dict_data_list(query_db, dict_data_query)
    return ResponseUtil.success(data=dict_data_query_result)


@dict_controller.get("/data/type/{dict_type}", response_model=ResponseType[list[DictDataSimpleVO]])
async def get_dict_data_by_type(
    dict_type: str = Path(), query_db: AsyncSession = Depends(get_db), redis_session: AsyncRedis = Depends(get_redis)
):
    """根据字典类型查询字典数据（优先从缓存获取，缓存不存在则从数据库加载）"""
    dict_data_list = await DictDataService.get_dict_data_from_cache(query_db, redis_session, dict_type)
    return ResponseUtil.success(data=dict_data_list)


@dict_controller.post(
    "/data", dependencies=[Depends(CheckUserInterfacePermit("system:dict:add"))], response_model=ResponseType[Empty]
)
@SystemLog(title="字典数据", business_type=SystemConstants.BusinessType.INSERT)
async def add_dict_data(
    dict_data_add: DictDataCreateDTO,
    current_user=Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """新增字典数据"""
    await DictDataService.add_dict_data(query_db, redis_session, dict_data_add, current_user)
    return ResponseUtil.success()


@dict_controller.put(
    "/data", dependencies=[Depends(CheckUserInterfacePermit("system:dict:edit"))], response_model=ResponseType[Empty]
)
@SystemLog(title="字典数据", business_type=SystemConstants.BusinessType.UPDATE)
async def update_dict_data(
    dict_data_update: DictDataUpdateDTO,
    current_user=Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """修改字典数据"""
    await DictDataService.update_dict_data(query_db, redis_session, dict_data_update, current_user)
    return ResponseUtil.success()


@dict_controller.delete(
    "/data/{dict_code_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="字典数据", business_type=SystemConstants.BusinessType.DELETE)
async def delete_dict_data(
    dict_code_ids: str = Path(..., pattern="^[0-9,]+$", description="字典数据ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """删除字典数据"""
    dict_code_id_list = [int(code) for code in dict_code_ids.split(",") if code]
    await DictDataService.delete_dict_data(query_db, redis_session, dict_code_id_list)
    return ResponseUtil.success()


@dict_controller.get(
    "/data/{dict_code}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dict:query"))],
    response_model=ResponseType[DictDataDetailVO],
)
async def get_dict_data_detail(dict_code: int, query_db: AsyncSession = Depends(get_db)):
    """获取字典数据详细信息"""
    dict_data_vo = await DictDataService.get_dict_data_detail(query_db, dict_code)
    return ResponseUtil.success(data=dict_data_vo)


# @dict_controller.post('/data/export', response_model=ResponseType,
#                       dependencies=[Depends(CheckUserInterfacePermit('system:dict:export'))])
# @log(title='字典数据', business_type=5)
# async def export_dict_data(
#         request: Request,
#         dict_data_query: DictDataQueryDTO = Depends(DictDataQueryDTO.as_form),
#         query_db: AsyncSession = Depends(get_db)
# ):
#     """
#     导出字典数据
#     """
#     # TODO: 实现导出功能
#     return ResponseUtil.success()
