"""用户认证 API 控制器.

提供登录、登出、注册、获取用户信息等认证相关功能。
"""

from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, Query, Request
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.config.manager import get_config
from graphedu.common.exceptions import TokenException
from graphedu.common.models.bo.auth import AccessTokenPayload
from graphedu.common.models.bo.user import CurrentUser
from graphedu.common.models.constants import RedisConstants, SystemConstants
from graphedu.common.models.dto.systemv2.user import (
    ForgotPasswordResetDTO,
    ForgotPasswordSendCodeDTO,
    UserLoginByPhoneDTO,
    UserLoginByStudentNoDTO,
    UserLoginByTeacherNoDTO,
    UserLoginByUsernameDTO,
    UserLoginResponseDTO,
    UserRegisterByUsernameDTO,
)
from graphedu.common.models.vo import FunctionTreeVO
from graphedu.common.models.vo.base import Empty, ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.user import AuthCurrentUserVO, UserDetailVO
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.common.utils import validate_token
from graphedu.common.utils.app import is_in_openapi
from graphedu.common.utils.uuids import uuid7_str
from graphedu.mapper.system.user import UserMapper
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import CustomOAuth2PasswordRequestForm, SecurityService, oauth2_scheme

login_controller = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# 通用登录处理辅助函数
# ============================================================================


async def _handle_login_success(
    request: Request,
    redis_session: AsyncRedis,
    query_db: AsyncSession,
    user_detail,
    login_info: dict | None = None,
) -> dict:
    """处理登录成功后的通用逻辑：生成 Token、存储会话、更新登录时间。

    Args:
        request: FastAPI Request 对象
        redis_session: Redis 异步会话
        query_db: 数据库异步会话
        user_detail: 用户详情（UserDetail 对象）
        login_info: 登录信息

    Returns:
        dict: 包含 access_token 和 token_type 的字典
    """
    session_id = uuid7_str()
    access_token_expires = timedelta(minutes=get_config().security.token.expire)
    access_token = await SecurityService.create_access_token(
        data=AccessTokenPayload(
            user_id=user_detail.user.user_id,
            user_name=user_detail.user.user_name,
            dept_names=[d.dept_name for d in user_detail.depts] if user_detail.depts else [],
            session_id=session_id,
            login_info=login_info,
        ),
        expires_delta=access_token_expires,
    )
    if not get_config().security.login.single_end:
        await redis_session.set(
            f"{RedisConstants.Auth.TOKEN_KEY}:{session_id}",
            access_token,
            ex=access_token_expires,
        )
    else:
        # 此方法可实现同一账号同一时间只能登录一次
        await redis_session.set(
            f"{RedisConstants.Auth.TOKEN_KEY}:{user_detail.user.user_id}",
            access_token,
            ex=access_token_expires,
        )
    # 更新用户登录时间
    user_detail.user.login_date = datetime.now()
    user_detail.user.update_time = datetime.now()
    await UserMapper.update(user_detail.user, query_db)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }


# ============================================================================
# 登录接口
# ============================================================================


@login_controller.post("/login", response_model=ResponseType[UserLoginResponseDTO])
@SystemLog(title="用户登录", business_type=SystemConstants.BusinessType.OTHER, log_type="login")
async def login(
    request: Request,
    form_data: CustomOAuth2PasswordRequestForm = Depends(),
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """用户名密码登录接口.

    Args:
        request: FastAPI 请求对象.
        form_data: OAuth2 密码表单数据（用户名、密码、验证码等）.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        登录成功返回访问令牌，失败返回错误信息.
    """
    captcha_enabled = (
        await redis_session.get(f"{RedisConstants.System.CONFIG_CACHE_KEY}:{SystemConstants.Config.CAPTCHA_ENABLED}")
        == "true"
    )
    user_login_info = UserLoginByUsernameDTO(
        user_name=form_data.username,
        password=form_data.password,
        code=form_data.code,
        uuid=form_data.uuid,
        login_info=form_data.login_info,
        captcha_enabled=captcha_enabled,
    )
    user_detail = await SecurityService.authenticate_user_by_username(request, redis_session, query_db, user_login_info)
    token_data = await _handle_login_success(request, redis_session, query_db, user_detail, user_login_info.login_info)

    response_token = UserLoginResponseDTO(**token_data)
    if is_in_openapi(request.headers):
        return response_token.model_dump(include={"access_token", "token_type"}, by_alias=True)
    return ResponseUtil.success(data=response_token)


@login_controller.post("/login/student", response_model=ResponseType[UserLoginResponseDTO])
@SystemLog(title="学号登录", business_type=SystemConstants.BusinessType.OTHER, log_type="login")
async def login_by_student_no(
    request: Request,
    login_data: UserLoginByStudentNoDTO,
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """学号密码登录接口（学生）.

    Args:
        request: FastAPI 请求对象.
        login_data: 学号登录数据（学号、密码、验证码等）.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        登录成功返回访问令牌，失败返回错误信息.
    """
    captcha_enabled = (
        await redis_session.get(f"{RedisConstants.System.CONFIG_CACHE_KEY}:{SystemConstants.Config.CAPTCHA_ENABLED}")
        == "true"
    )
    login_data.captcha_enabled = captcha_enabled
    user_detail = await SecurityService.authenticate_user_by_student_no(
        request, redis_session, query_db, login_data
    )
    token_data = await _handle_login_success(request, redis_session, query_db, user_detail, login_data.login_info)

    response_token = UserLoginResponseDTO(**token_data)
    if is_in_openapi(request.headers):
        return response_token.model_dump(include={"access_token", "token_type"}, by_alias=True)
    return ResponseUtil.success(data=response_token)


@login_controller.post("/login/teacher", response_model=ResponseType[UserLoginResponseDTO])
@SystemLog(title="工号登录", business_type=SystemConstants.BusinessType.OTHER, log_type="login")
async def login_by_teacher_no(
    request: Request,
    login_data: UserLoginByTeacherNoDTO,
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """工号密码登录接口（教师）.

    Args:
        request: FastAPI 请求对象.
        login_data: 工号登录数据（工号、密码、验证码等）.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        登录成功返回访问令牌，失败返回错误信息.
    """
    captcha_enabled = (
        await redis_session.get(f"{RedisConstants.System.CONFIG_CACHE_KEY}:{SystemConstants.Config.CAPTCHA_ENABLED}")
        == "true"
    )
    login_data.captcha_enabled = captcha_enabled
    user_detail = await SecurityService.authenticate_user_by_teacher_no(
        request, redis_session, query_db, login_data
    )
    token_data = await _handle_login_success(request, redis_session, query_db, user_detail, login_data.login_info)

    response_token = UserLoginResponseDTO(**token_data)
    if is_in_openapi(request.headers):
        return response_token.model_dump(include={"access_token", "token_type"}, by_alias=True)
    return ResponseUtil.success(data=response_token)


@login_controller.post("/login/phone", response_model=ResponseType[UserLoginResponseDTO])
@SystemLog(title="手机号登录", business_type=SystemConstants.BusinessType.OTHER, log_type="login")
async def login_by_phone(
    request: Request,
    login_data: UserLoginByPhoneDTO,
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """手机号密码登录接口（通用）.

    Args:
        request: FastAPI 请求对象.
        login_data: 手机号登录数据（手机号、密码、验证码等）.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        登录成功返回访问令牌，失败返回错误信息.
    """
    captcha_enabled = (
        await redis_session.get(f"{RedisConstants.System.CONFIG_CACHE_KEY}:{SystemConstants.Config.CAPTCHA_ENABLED}")
        == "true"
    )
    login_data.captcha_enabled = captcha_enabled
    user_detail = await SecurityService.authenticate_user_by_phone(request, redis_session, query_db, login_data)
    token_data = await _handle_login_success(request, redis_session, query_db, user_detail, login_data.login_info)

    response_token = UserLoginResponseDTO(**token_data)
    if is_in_openapi(request.headers):
        return response_token.model_dump(include={"access_token", "token_type"}, by_alias=True)
    return ResponseUtil.success(data=response_token)


# ============================================================================
# 用户信息与菜单
# ============================================================================


@login_controller.get("/info", response_model=ResponseType[AuthCurrentUserVO])
async def get_login_user_info(current_user: CurrentUser = Depends(SecurityService.get_current_user)):
    """获取当前登录用户信息.

    Args:
        current_user: 当前登录用户对象.

    Returns:
        当前用户信息.
    """
    return ResponseUtil.success(data=AuthCurrentUserVO.model_validate(current_user, from_attributes=True))


@login_controller.get("/menus", response_model=ResponseType[list[FunctionTreeVO]])
async def get_login_user_menus(
    scene: str = Query(default="admin", description="应用场景: web-日常应用, admin-管理系统, mobile-移动端"),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
):
    """获取当前登录用户的菜单树（用于 Ant Design Menu 渲染）.

    返回规则：
    1. 仅返回当前用户有权限的功能
    2. 仅返回目录(DIR)、菜单(MENU)、分组(GROUP)、分隔线(DIVIDER)类型
    3. 根据 scene 参数过滤不同场景的菜单
    4. 按 sort_order 排序
    5. 保持树形结构

    Args:
        scene: 应用场景，默认为 admin（管理系统）
        current_user: 当前登录用户对象.
        query_db: 数据库异步会话.
        redis_session: Redis 异步会话.

    Returns:
        用户可访问的菜单树列表.
    """
    user_menus = await SecurityService.get_current_user_menus_by_scene(
        current_user.detail.role_ids,
        scene,
        query_db,
        redis_session,
    )
    return ResponseUtil.success(data=user_menus)


# ============================================================================
# 注册
# ============================================================================


@login_controller.post("/register", response_model=ResponseType[UserDetailVO])
async def register_user(
    user_register: UserRegisterByUsernameDTO,
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """用户注册接口.

    Args:
        user_register: 用户注册信息.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        注册成功返回用户详细信息.
    """
    user_register_result = await SecurityService.register_user(user_register, redis_session, query_db)
    return ResponseUtil.success(data=user_register_result)


# ============================================================================
# 忘记密码
# ============================================================================


@login_controller.post("/forgot-password/send-code", response_model=ResponseType[str])
async def forgot_password_send_code(
    forgot_dto: ForgotPasswordSendCodeDTO,
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """忘记密码 - 发送短信验证码.

    向用户注册手机号发送 6 位数字验证码，验证码有效期为 2 分钟。
    同一手机号 60 秒内只能发送一次。

    Args:
        forgot_dto: 发送验证码请求（包含手机号）.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        发送结果提示信息.
    """
    result = await SecurityService.send_password_reset_code(forgot_dto, redis_session, query_db)
    return ResponseUtil.success(data=result)


@login_controller.post("/forgot-password/reset", response_model=ResponseType[Empty])
async def forgot_password_reset(
    reset_dto: ForgotPasswordResetDTO,
    redis_session: AsyncRedis = Depends(get_redis),
    query_db: AsyncSession = Depends(get_db),
):
    """忘记密码 - 通过短信验证码重置密码.

    验证短信验证码后重置用户密码。

    Args:
        reset_dto: 密码重置请求（包含手机号、验证码、新密码）.
        redis_session: Redis 异步会话.
        query_db: 数据库异步会话.

    Returns:
        重置成功返回空响应.
    """
    await SecurityService.reset_password(reset_dto, redis_session, query_db)
    return ResponseUtil.success()


# ============================================================================
# 登出
# ============================================================================


@login_controller.post("/logout", response_model=ResponseType[Empty])
async def logout(token: str | None = Depends(oauth2_scheme), redis_session: AsyncRedis = Depends(get_redis)):
    """用户登出接口.

    Args:
        token: JWT 访问令牌.
        redis_session: Redis 异步会话.

    Returns:
        登出成功返回空响应.
    """
    try:
        payload = validate_token(
            token, secret=get_config().security.token.secret, algorithms=get_config().security.token.algorithm
        )
    except TokenException:
        # 如果 token 无效或过期，直接返回成功（因为用户已经无法使用该 token 访问资源了）
        return ResponseUtil.success()
    # 若 session_id 为空，交给 service 层处理（可能是单点登录模式，使用 user_id 作为 key）
    session_id: str = payload.get("session_id")
    user_id: int = int(payload.get("user_id"))
    await SecurityService.logout(user_id, session_id, redis_session)
    return ResponseUtil.success()
