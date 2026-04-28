"""认证服务模块

本模块提供用户认证和授权的核心功能，包括用户登录、注册、Token 管理、权限验证和路由生成。

核心类：
- CustomOAuth2PasswordRequestForm: 自定义 OAuth2 密码表单，支持验证码和会话编号
- SecurityService: 安全服务类，提供认证相关的核心业务逻辑
- RouterUtil: 路由工具类，处理菜单与路由的转换

主要功能：
- 用户认证：用户名密码登录、学号登录、工号登录、手机号登录、验证码校验、IP 黑名单检查、账号锁定机制
- Token 管理：Token 生成、验证、续期和失效处理
- 权限管理：基于角色的权限控制（RBAC），支持多端登录和单点登录模式
- 路由生成：根据用户权限动态生成前端路由配置
- 用户注册：支持验证码校验的用户注册功能
- 忘记密码：通过手机短信验证码重置密码

依赖：
- FastAPI: Web 框架，提供 OAuth2 密码流支持
- JWT: Token 编码和验证
- Redis: 会话管理、验证码存储、登录失败计数
- SQLAlchemy: 用户数据查询
"""

from datetime import UTC, datetime, timedelta
import json
import logging
import random

from fastapi import Depends, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.config.manager import get_config
from graphedu.common.exceptions import UserDeactivatedException
from graphedu.common.exceptions.base import AppException
from graphedu.common.exceptions.services.system.auth import (
    LoginAccountLockedException,
    LoginCaptchaErrorException,
    LoginCaptchaExpiredException,
    LoginIpErrorException,
    LoginPasswordErrorException,
    LoginPhoneNotFoundException,
    LoginStudentNotFoundException,
    LoginTeacherNotFoundException,
    LoginTooManyAttemptsException,
    LoginUserNotFoundException,
    PasswordResetSmsCodeErrorException,
    PasswordResetSmsCodeExpiredException,
    PasswordResetSmsCodeSendTooFrequentException,
    RegisterFunctionDisabledException,
    RegisterIllegalDoublePasswordException,
    TokenException,
    TokenInvalidException,
    TokenMalformedException,
)
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.bo.auth import AccessTokenPayload
from graphedu.common.models.bo.user import UserDetail
from graphedu.common.models.constants import RedisConstants, SystemConstants
from graphedu.common.models.dto.systemv2.user import (
    ForgotPasswordResetDTO,
    ForgotPasswordSendCodeDTO,
    UserCreateDTO,
    UserLoginByPhoneDTO,
    UserLoginByStudentNoDTO,
    UserLoginByTeacherNoDTO,
    UserLoginByUsernameDTO,
    UserRegisterByUsernameDTO,
)
from graphedu.common.models.orm.education import EduStudent, EduTeacher
from graphedu.common.models.orm.system import SysFunction
from graphedu.common.models.vo import FunctionTreeVO
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.common.utils import PasswordUtil, create_token, validate_token
from graphedu.common.utils.app import is_in_openapi
from graphedu.common.utils.cache import OneDay
from graphedu.mapper.education.student import StudentMapper
from graphedu.mapper.education.teacher import TeacherMapper
from graphedu.mapper.system.function import FunctionMapper
from graphedu.mapper.system.user import UserMapper
from graphedu.services.system.user import UserService

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class CustomOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    """自定义OAuth2PasswordRequestForm类，增加验证码及会话编号参数"""

    def __init__(
        self,
        grant_type: str = Form(default=None, pattern="password"),
        username: str = Form(),
        password: str = Form(),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
        code: str | None = Form(default=""),
        uuid: str | None = Form(default=""),
        login_info: dict[str, str] | None = Form(default=None),
    ):
        """初始化自定义 OAuth2 密码请求表单

        扩展标准的 OAuth2PasswordRequestForm，增加验证码和会话编号支持。

        Args:
            grant_type: 授权类型，必须为 "password"
            username: 用户名
            password: 密码
            scope: 授权范围
            client_id: 客户端 ID
            client_secret: 客户端密钥
            code: 验证码
            uuid: 验证码对应的 UUID（用于从 Redis 获取验证码）
            login_info: 登录信息（包含 IP、User-Agent 等）
        """
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )
        self.code = code
        self.uuid = uuid
        self.login_info = login_info


async def _check_login_ip(request: Request, redis_session: AsyncRedis):
    """校验用户登录 IP 是否在黑名单内

    Args:
        request: FastAPI Request 对象
        redis_session: Redis 异步会话对象

    Returns:
        bool: 校验结果，通过返回 True

    Raises:
        LoginIpErrorException: 当登录 IP 在黑名单中时
    """
    black_ip_value = await redis_session.get(f"{RedisConstants.System.CONFIG_CACHE_KEY}:sys.login.blackIPList")
    black_ip_list = black_ip_value.split(",") if black_ip_value else []
    if request.headers.get("X-Forwarded-For") in black_ip_list:
        raise LoginIpErrorException
    return True


async def _check_login_captcha(redis_session: AsyncRedis, login_user: UserLoginByUsernameDTO):
    """校验用户登录验证码

    Args:
        redis_session: Redis 异步会话对象
        login_user: 登录用户对象

    Returns:
        bool: 校验结果，通过返回 True

    Raises:
        LoginCaptchaExpiredException: 当验证码已过期时
        LoginCaptchaErrorException: 当验证码错误时
    """
    captcha_value = await redis_session.get(f"{RedisConstants.Auth.CAPTCHA_KEY}:{login_user.uuid}")
    if not captcha_value:
        raise LoginCaptchaExpiredException
    if login_user.code != str(captcha_value):
        raise LoginCaptchaErrorException
    return True


async def _check_captcha(redis_session: AsyncRedis, code: str | None, uuid: str | None):
    """校验验证码（直接传参版本）

    Args:
        redis_session: Redis 异步会话对象
        code: 验证码
        uuid: 验证码对应的 UUID

    Returns:
        bool: 校验结果，通过返回 True

    Raises:
        LoginCaptchaExpiredException: 当验证码已过期时
        LoginCaptchaErrorException: 当验证码错误时
    """
    captcha_value = await redis_session.get(f"{RedisConstants.Auth.CAPTCHA_KEY}:{uuid}")
    if not captcha_value:
        raise LoginCaptchaExpiredException
    if code != str(captcha_value):
        raise LoginCaptchaErrorException
    return True


def _generate_menus(pid: int, function_list: list[SysFunction]) -> list[FunctionTreeVO]:
    """根据功能列表生成菜单信息树

    递归生成树形结构的菜单数据。

    Args:
        pid: 父菜单 ID
        function_list: 菜单/功能列表信息

    Returns:
        菜单信息树形嵌套数据列表
    """
    menu_list: list[FunctionTreeVO] = []
    for function in function_list:
        if function.parent_id == pid:
            children = _generate_menus(function.function_id, function_list)
            menu_list_data = FunctionTreeVO.model_validate(function)
            if children:
                menu_list_data.children = children
                menu_list_data.has_children = True
            else:
                menu_list_data.has_children = False
            menu_list.append(menu_list_data)

    return menu_list


class SecurityService:
    """登录模块服务层"""

    # ========================================================================
    # 身份信息加载
    # ========================================================================

    @staticmethod
    async def _load_student_info(user_id: int, query_db: AsyncSession) -> EduStudent | None:
        """加载学生扩展信息

        Args:
            user_id: 用户ID
            query_db: 数据库会话

        Returns:
            学生扩展信息 ORM 对象，不存在则返回 None
        """
        student = await StudentMapper.get_by_user_id(user_id, query_db)
        if student:
            query_db.expunge(student)  # 从 session 中分离，避免 DetachedInstanceError
        return student

    @staticmethod
    async def _load_teacher_info(user_id: int, query_db: AsyncSession) -> EduTeacher | None:
        """加载教师扩展信息

        Args:
            user_id: 用户ID
            query_db: 数据库会话

        Returns:
            教师扩展信息 ORM 对象，不存在则返回 None
        """
        teacher = await TeacherMapper.get_by_user_id(user_id, query_db)
        if teacher:
            query_db.expunge(teacher)  # 从 session 中分离，避免 DetachedInstanceError
        return teacher

    # ========================================================================
    # 通用认证流程辅助方法
    # ========================================================================

    @staticmethod
    async def _check_pre_authentication(
        request: Request,
        redis_session: AsyncRedis,
        login_identifier: str,
        captcha_enabled: bool,
        code: str | None = None,
        uuid: str | None = None,
    ) -> None:
        """登录前校验：IP 黑名单检查、账号锁定检查、验证码校验

        所有登录方式的通用前置校验，在用户查询之前执行。

        Args:
            request: FastAPI Request 对象
            redis_session: Redis 异步会话对象
            login_identifier: 登录标识（用户名/学号/工号/手机号），用于锁定键
            captcha_enabled: 是否启用验证码
            code: 验证码
            uuid: 验证码对应的 UUID

        Raises:
            LoginIpErrorException: 当登录 IP 在黑名单中时
            LoginAccountLockedException: 当账号被锁定时
            LoginCaptchaExpiredException: 当验证码已过期时
            LoginCaptchaErrorException: 当验证码错误时
        """
        # 1. IP 黑名单检查
        await _check_login_ip(request, redis_session)
        # 2. 账号锁定检查（通过 login_identifier 作为 Redis 键后缀）
        account_lock = await redis_session.get(f"{RedisConstants.Auth.LOGIN_FAIL_LOCK_KEY}:{login_identifier}")
        if login_identifier == account_lock:
            raise LoginAccountLockedException
        # 3. 验证码校验（dev 模式下来自 API 文档的登录请求不校验）
        if captcha_enabled and not is_in_openapi(request.headers):
            await _check_captcha(redis_session, code, uuid)

    @staticmethod
    async def _verify_password_with_lock(
        redis_session: AsyncRedis,
        login_identifier: str,
        raw_password: str,
        hashed_password: str,
    ) -> None:
        """密码验证与错误计数/锁定处理

        验证密码正确性，错误时累计计数，超过阈值（5 次）则锁定账号 10 分钟。

        Args:
            redis_session: Redis 异步会话对象
            login_identifier: 登录标识，用于错误计数和锁定的 Redis 键后缀
            raw_password: 用户输入的明文密码
            hashed_password: 数据库中存储的哈希密码

        Raises:
            LoginPasswordErrorException: 当密码错误且未达到锁定阈值时
            LoginTooManyAttemptsException: 当密码错误次数超过 5 次时
        """
        if not PasswordUtil.verify_password(raw_password, hashed_password):
            # 获取密码错误次数
            cache_cnt = (
                await redis_session.get(f"{RedisConstants.Auth.LOGIN_PASSWORD_ERROR_CNT_KEY}:{login_identifier}") or 0
            )
            password_error_count = int(cache_cnt) + 1
            # 更新密码错误次数，过期时间为 10 分钟
            await redis_session.set(
                f"{RedisConstants.Auth.LOGIN_PASSWORD_ERROR_CNT_KEY}:{login_identifier}",
                password_error_count,
                ex=timedelta(minutes=10),
            )
            # 若密码错误次数超过 5 次，则锁定账号 10 分钟
            if password_error_count > 5:
                await redis_session.delete(f"{RedisConstants.Auth.LOGIN_PASSWORD_ERROR_CNT_KEY}:{login_identifier}")
                await redis_session.set(
                    f"{RedisConstants.Auth.LOGIN_FAIL_LOCK_KEY}:{login_identifier}",
                    login_identifier,
                    ex=timedelta(minutes=10),
                )
                raise LoginTooManyAttemptsException(period_seconds=10 * 60, wait_seconds=5 * 60)
            raise LoginPasswordErrorException

    @staticmethod
    async def _clear_login_fail_count(redis_session: AsyncRedis, login_identifier: str) -> None:
        """清除登录失败计数器

        登录成功后调用，清除 Redis 中该登录标识对应的密码错误计数。

        Args:
            redis_session: Redis 异步会话对象
            login_identifier: 登录标识（用户名/学号/工号/手机号）
        """
        await redis_session.delete(f"{RedisConstants.Auth.LOGIN_PASSWORD_ERROR_CNT_KEY}:{login_identifier}")

    @staticmethod
    async def _build_user_detail(user_id: int, user_type: str, query_db: AsyncSession) -> UserDetail:
        """构建用户详情（加载部门、角色、身份信息）

        根据 user_id 查询完整的用户详情，包括所属部门、角色，以及根据 user_type
        加载对应的学生/教师扩展信息。

        Args:
            user_id: 用户 ID
            user_type: 用户类型，对照 SystemConstants.UserType
            query_db: 数据库异步会话对象

        Returns:
            UserDetail: 用户详细信息对象

        Raises:
            LoginUserNotFoundException: 当用户详情查询不到时
        """
        query_user = await UserMapper.get_detail_by_id(user_id, query_db)
        if query_user.get("user_basic_info") is None:
            raise LoginUserNotFoundException

        # 将 ORM 对象从 session 中分离，避免后续 DetachedInstanceError
        query_db.expunge(query_user["user_basic_info"])
        for dept in query_user["user_dept_info"]:
            query_db.expunge(dept)
        for role in query_user["user_role_info"]:
            query_db.expunge(role)

        # 组装当前用户信息
        dept_ids = [row.dept_id for row in query_user["user_dept_info"]]
        role_ids = [row.role_id for row in query_user["user_role_info"]]

        # 始终尝试加载学生和教师两种身份信息，支持双角色用户
        student_info = await SecurityService._load_student_info(user_id, query_db)
        teacher_info = await SecurityService._load_teacher_info(user_id, query_db)

        return UserDetail(
            dept_ids=dept_ids,
            role_ids=role_ids,
            depts=list(query_user["user_dept_info"]),
            roles=list(query_user["user_role_info"]),
            user=query_user["user_basic_info"],
            student_info=student_info,
            teacher_info=teacher_info,
        )

    # ========================================================================
    # 登录认证方法
    # ========================================================================

    @staticmethod
    async def authenticate_user_by_username(
        request: Request, redis_session: AsyncRedis, query_db: AsyncSession, login_user: UserLoginByUsernameDTO
    ) -> UserDetail | None:
        """根据用户名密码校验用户登录

        执行完整的用户登录认证流程，包括 IP 黑名单检查、验证码验证、
        账号锁定检查、密码验证、账号状态检查等。

        Args:
            request: FastAPI Request 对象
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象
            login_user: 登录用户信息

        Returns:
            UserDetail: 用户详细信息对象

        Raises:
            LoginIpErrorException: 当登录 IP 在黑名单中时
            LoginAccountLockedException: 当账号被锁定时
            LoginCaptchaExpiredException: 当验证码已过期时
            LoginCaptchaErrorException: 当验证码错误时
            LoginUserNotFoundException: 当用户不存在时
            LoginPasswordErrorException: 当密码错误时
            LoginTooManyAttemptsException: 当密码错误次数过多时
            UserDeactivatedException: 当账号被停用时
        """
        # 前置校验
        await SecurityService._check_pre_authentication(
            request, redis_session, login_user.user_name, login_user.captcha_enabled, login_user.code, login_user.uuid
        )
        # 根据用户名获取用户信息
        user = await UserMapper.get_by_username(login_user.user_name, query_db)
        if not user:
            raise LoginUserNotFoundException
        # 密码验证与锁定处理
        await SecurityService._verify_password_with_lock(
            redis_session, login_user.user_name, login_user.password, user.password
        )
        # 登录成功，清除失败计数
        await SecurityService._clear_login_fail_count(redis_session, login_user.user_name)
        # 账户停用验证
        if user.status == "1":
            raise UserDeactivatedException
        # 构建用户详情
        return await SecurityService._build_user_detail(user.user_id, user.user_type, query_db)

    @staticmethod
    async def authenticate_user_by_student_no(
        request: Request, redis_session: AsyncRedis, query_db: AsyncSession, login_user: UserLoginByStudentNoDTO
    ) -> UserDetail | None:
        """根据学号密码校验用户登录（学生）

        通过学号查找关联的学生记录（EduStudent），再通过 student_id 关联到
        系统用户（SysUser），执行完整的认证流程。

        Args:
            request: FastAPI Request 对象
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象
            login_user: 学号登录信息

        Returns:
            UserDetail: 用户详细信息对象

        Raises:
            LoginIpErrorException: 当登录 IP 在黑名单中时
            LoginAccountLockedException: 当账号被锁定时
            LoginCaptchaExpiredException: 当验证码已过期时
            LoginCaptchaErrorException: 当验证码错误时
            LoginStudentNotFoundException: 当学号不存在或未关联用户时
            LoginUserNotFoundException: 当关联的系统用户不存在时
            LoginPasswordErrorException: 当密码错误时
            LoginTooManyAttemptsException: 当密码错误次数过多时
            UserDeactivatedException: 当账号被停用时
        """
        # 前置校验（使用学号作为锁定标识）
        await SecurityService._check_pre_authentication(
            request,
            redis_session,
            login_user.student_no,
            login_user.captcha_enabled,
            login_user.code,
            login_user.uuid,
        )
        # 根据学号查找学生记录
        student = await StudentMapper.get_student_by_no_for_binding(login_user.student_no, query_db)
        if not student:
            raise LoginStudentNotFoundException
        # 通过 student_id 关联查找系统用户
        user = await UserMapper.get_by_id(student.student_id, query_db)
        if not user:
            raise LoginUserNotFoundException
        # 密码验证与锁定处理
        await SecurityService._verify_password_with_lock(
            redis_session, login_user.student_no, login_user.password, user.password
        )
        # 登录成功，清除失败计数
        await SecurityService._clear_login_fail_count(redis_session, login_user.student_no)
        # 账户停用验证
        if user.status == "1":
            raise UserDeactivatedException
        # 构建用户详情
        return await SecurityService._build_user_detail(user.user_id, user.user_type, query_db)

    @staticmethod
    async def authenticate_user_by_teacher_no(
        request: Request, redis_session: AsyncRedis, query_db: AsyncSession, login_user: UserLoginByTeacherNoDTO
    ) -> UserDetail | None:
        """根据工号密码校验用户登录（教师）

        通过工号查找关联的教师记录（EduTeacher），再通过 teacher_id 关联到
        系统用户（SysUser），执行完整的认证流程。

        Args:
            request: FastAPI Request 对象
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象
            login_user: 工号登录信息

        Returns:
            UserDetail: 用户详细信息对象

        Raises:
            LoginIpErrorException: 当登录 IP 在黑名单中时
            LoginAccountLockedException: 当账号被锁定时
            LoginCaptchaExpiredException: 当验证码已过期时
            LoginCaptchaErrorException: 当验证码错误时
            LoginTeacherNotFoundException: 当工号不存在或未关联用户时
            LoginUserNotFoundException: 当关联的系统用户不存在时
            LoginPasswordErrorException: 当密码错误时
            LoginTooManyAttemptsException: 当密码错误次数过多时
            UserDeactivatedException: 当账号被停用时
        """
        # 前置校验（使用工号作为锁定标识）
        await SecurityService._check_pre_authentication(
            request,
            redis_session,
            login_user.teacher_no,
            login_user.captcha_enabled,
            login_user.code,
            login_user.uuid,
        )
        # 根据工号查找教师记录
        teacher = await TeacherMapper.get_teacher_by_no_for_binding(login_user.teacher_no, query_db)
        if not teacher:
            raise LoginTeacherNotFoundException
        # 通过 teacher_id 关联查找系统用户
        user = await UserMapper.get_by_id(teacher.teacher_id, query_db)
        if not user:
            raise LoginUserNotFoundException
        # 密码验证与锁定处理
        await SecurityService._verify_password_with_lock(
            redis_session, login_user.teacher_no, login_user.password, user.password
        )
        # 登录成功，清除失败计数
        await SecurityService._clear_login_fail_count(redis_session, login_user.teacher_no)
        # 账户停用验证
        if user.status == "1":
            raise UserDeactivatedException
        # 构建用户详情
        return await SecurityService._build_user_detail(user.user_id, user.user_type, query_db)

    @staticmethod
    async def authenticate_user_by_phone(
        request: Request, redis_session: AsyncRedis, query_db: AsyncSession, login_user: UserLoginByPhoneDTO
    ) -> UserDetail | None:
        """根据手机号密码校验用户登录（通用）

        通过手机号直接查找系统用户（SysUser），执行完整的认证流程。

        Args:
            request: FastAPI Request 对象
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象
            login_user: 手机号登录信息

        Returns:
            UserDetail: 用户详细信息对象

        Raises:
            LoginIpErrorException: 当登录 IP 在黑名单中时
            LoginAccountLockedException: 当账号被锁定时
            LoginCaptchaExpiredException: 当验证码已过期时
            LoginCaptchaErrorException: 当验证码错误时
            LoginPhoneNotFoundException: 当手机号未注册时
            LoginPasswordErrorException: 当密码错误时
            LoginTooManyAttemptsException: 当密码错误次数过多时
            UserDeactivatedException: 当账号被停用时
        """
        # 前置校验（使用手机号作为锁定标识）
        await SecurityService._check_pre_authentication(
            request,
            redis_session,
            login_user.phonenumber,
            login_user.captcha_enabled,
            login_user.code,
            login_user.uuid,
        )
        # 根据手机号查找用户
        user = await UserMapper.get_by_phonenumber(login_user.phonenumber, query_db)
        if not user:
            raise LoginPhoneNotFoundException
        # 密码验证与锁定处理
        await SecurityService._verify_password_with_lock(
            redis_session, login_user.phonenumber, login_user.password, user.password
        )
        # 登录成功，清除失败计数
        await SecurityService._clear_login_fail_count(redis_session, login_user.phonenumber)
        # 账户停用验证
        if user.status == "1":
            raise UserDeactivatedException
        # 构建用户详情
        return await SecurityService._build_user_detail(user.user_id, user.user_type, query_db)

    # ========================================================================
    # 忘记密码
    # ========================================================================

    @staticmethod
    async def send_password_reset_code(
        forgot_dto: ForgotPasswordSendCodeDTO, redis_session: AsyncRedis, query_db: AsyncSession
    ) -> str:
        """发送密码重置短信验证码

        验证手机号是否已注册，通过频率限制后生成 6 位数字验证码并存储到 Redis。

        Args:
            forgot_dto: 忘记密码发送验证码请求
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象

        Returns:
            str: 发送结果提示信息

        Raises:
            LoginPhoneNotFoundException: 当手机号未注册时
            PasswordResetSmsCodeSendTooFrequentException: 当发送过于频繁时
        """
        phonenumber = forgot_dto.phonenumber
        # 校验手机号是否已注册
        user = await UserMapper.get_by_phonenumber(phonenumber, query_db)
        if not user:
            raise LoginPhoneNotFoundException
        # 频率限制：同一手机号 60 秒内只能发送一次
        rate_limit_key = f"{RedisConstants.Auth.SMS_RATE_LIMIT_KEY}:{phonenumber}"
        if await redis_session.get(rate_limit_key):
            raise PasswordResetSmsCodeSendTooFrequentException
        # 生成 6 位数字验证码
        sms_code = str(random.randint(100000, 999999))
        # 存储验证码到 Redis，有效期为 2 分钟
        code_key = f"{RedisConstants.Auth.SMS_CODE_KEY}:{phonenumber}"
        await redis_session.set(code_key, sms_code, ex=timedelta(minutes=2))
        # 设置发送频率限制
        await redis_session.set(rate_limit_key, "1", ex=timedelta(seconds=60))
        # TODO: 对接实际短信服务发送验证码
        logger.info("Password reset SMS code for %s: %s", phonenumber, sms_code)
        return "验证码已发送"

    @staticmethod
    async def reset_password(
        reset_dto: ForgotPasswordResetDTO, redis_session: AsyncRedis, query_db: AsyncSession
    ) -> None:
        """通过短信验证码重置密码

        验证短信验证码的正确性，通过后更新用户密码。

        Args:
            reset_dto: 密码重置请求
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象

        Raises:
            PasswordResetSmsCodeExpiredException: 当短信验证码已过期时
            PasswordResetSmsCodeErrorException: 当短信验证码错误时
            LoginPhoneNotFoundException: 当手机号未注册时
        """
        phonenumber = reset_dto.phonenumber
        # 验证短信验证码
        code_key = f"{RedisConstants.Auth.SMS_CODE_KEY}:{phonenumber}"
        cached_code = await redis_session.get(code_key)
        if not cached_code:
            raise PasswordResetSmsCodeExpiredException
        if reset_dto.sms_code != str(cached_code):
            raise PasswordResetSmsCodeErrorException
        # 验证通过后删除已使用的验证码
        await redis_session.delete(code_key)
        # 查找用户并更新密码
        user = await UserMapper.get_by_phonenumber(phonenumber, query_db)
        if not user:
            raise LoginPhoneNotFoundException
        user.password = PasswordUtil.hash_password(reset_dto.new_password)
        await UserMapper.update(user, query_db)

    # ========================================================================
    # Token 管理
    # ========================================================================

    @staticmethod
    async def create_access_token(data: AccessTokenPayload, expires_delta: timedelta | None = None):
        """根据登录信息创建访问令牌

        Args:
            data: 登录信息载荷
            expires_delta: Token 有效期，优先级：传入值 > 配置值 > 默认值（30分钟）

        Returns:
            str: JWT 访问令牌
        """
        payload = data.copy()
        if expires_delta is not None:
            pass
        elif get_config().security.token.expire:
            expires_delta = timedelta(minutes=get_config().security.token.expire)
        else:
            expires_delta = timedelta(minutes=30)
        expire = datetime.now(UTC) + expires_delta
        return create_token(
            payload, get_config().security.token.secret, algorithm=get_config().security.token.algorithm, expire=expire
        )

    @staticmethod
    async def _load_current_user_from_db(user_id: int, session_id: str, query_db: AsyncSession) -> CurrentUser:
        """从数据库加载用户信息（内部方法，用于 cashews 缓存装饰器）

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            query_db: 数据库会话

        Returns:
            CurrentUser: 当前用户信息
        """
        query_user = await UserMapper.get_detail_by_id(user_id, query_db)
        if query_user.get("user_basic_info") is None:
            raise TokenInvalidException

        # 将 ORM 对象从 session 中分离，避免后续 DetachedInstanceError
        query_db.expunge(query_user["user_basic_info"])
        for dept in query_user["user_dept_info"]:
            query_db.expunge(dept)
        for role in query_user["user_role_info"]:
            query_db.expunge(role)
        for func_obj in query_user["user_function_info"]:
            query_db.expunge(func_obj)

        # 组装当前用户信息
        role_id_list = [item.role_id for item in query_user["user_role_info"]]
        # 超级管理员定义：role_id <= 10 的角色
        if any(role_id <= 10 for role_id in role_id_list):
            permissions = ["*:*:*"]
        else:
            permissions = [row.function_key for row in query_user["user_function_info"]]
        dept_ids = [row.dept_id for row in query_user["user_dept_info"]]
        role_ids = [row.role_id for row in query_user["user_role_info"]]
        role_keys = [row.role_key for row in query_user["user_role_info"]]

        # 始终加载学生和教师两种身份信息，支持双角色用户
        student_info = await SecurityService._load_student_info(user_id, query_db)
        teacher_info = await SecurityService._load_teacher_info(user_id, query_db)

        return CurrentUser(
            session_id=session_id,
            permissions=permissions,
            role_keys=role_keys,
            detail=UserDetail(
                dept_ids=dept_ids,
                role_ids=role_ids,
                depts=list(query_user["user_dept_info"]),
                roles=list(query_user["user_role_info"]),
                user=query_user["user_basic_info"],
                student_info=student_info,
                teacher_info=teacher_info,
            ),
        )

    @staticmethod
    async def _load_user_from_cache(
        user_id: int, session_id: str, query_db: AsyncSession, redis_session: AsyncRedis
    ) -> CurrentUser:
        """从缓存加载用户菜单信息，缓存未命中时从数据库加载"""
        if get_config().security.login.single_end:
            cache_key = f"{RedisConstants.Auth.USER_CACHE_KEY}:{user_id}"
        else:
            cache_key = f"{RedisConstants.Auth.USER_CACHE_KEY}:{session_id}"
        # 尝试从缓存获取用户信息
        cached_user = await redis_session.get(cache_key)
        if cached_user:
            return CurrentUser.model_validate_json(cached_user)
        cur_user = await SecurityService._load_current_user_from_db(user_id, session_id, query_db)
        # 将用户信息缓存到 Redis，设置过期时间为 1 天
        await redis_session.set(cache_key, cur_user.model_dump_json(), ex=OneDay)
        return cur_user

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        query_db: AsyncSession = Depends(get_db),
        redis_session: AsyncRedis = Depends(get_redis),
    ) -> CurrentUser:
        """根据 Token 获取当前用户信息

        验证 Token 有效性，使用 cashews 缓存获取用户信息。
        根据登录模式（多端登录/单点登录）检查 Token 是否匹配。

        Args:
            token: JWT 访问令牌
            query_db: 数据库异步会话对象
            redis_session: Redis 异步会话对象

        Returns:
            CurrentUser: 当前用户信息对象，包含权限、角色、部门等详细信息

        Raises:
            TokenInvalidException: 当 Token 无效时
            TokenExpiredException: 当 Token 已过期时
            TokenMalformedException: 当 Token 格式错误时
        """
        try:
            if token.startswith("Bearer"):
                token = token.split(" ")[1]
            payload = validate_token(
                token,
                get_config().security.token.secret,
                algorithms=get_config().security.token.algorithm,
            )
            user_id: int | str = payload.get("user_id")
            session_id: str = payload.get("session_id")
            if not user_id or (not session_id and not get_config().security.login.single_end):
                raise TokenInvalidException
        except TokenException:
            raise
        except Exception as e:
            logger.warning("Unable to validate token when getting current user: ", e)
            raise TokenMalformedException from None

        # 验证 Token 有效性
        user_id_int = int(user_id)
        if not get_config().security.login.single_end:
            redis_token = await redis_session.get(f"{RedisConstants.Auth.TOKEN_KEY}:{session_id}")
        else:
            redis_token = await redis_session.get(f"{RedisConstants.Auth.TOKEN_KEY}:{user_id_int}")

        if token != redis_token:
            raise TokenInvalidException

        # 续期 Token
        if not get_config().security.login.single_end:
            await redis_session.set(
                f"{RedisConstants.Auth.TOKEN_KEY}:{session_id}",
                redis_token,
                ex=timedelta(minutes=get_config().security.token.expire),
            )
        else:
            await redis_session.set(
                f"{RedisConstants.Auth.TOKEN_KEY}:{user_id_int}",
                redis_token,
                ex=timedelta(minutes=get_config().security.token.expire),
            )

        # 使用带缓存的加载方法
        return await SecurityService._load_user_from_cache(user_id_int, session_id, query_db, redis_session)

    # ========================================================================
    # 菜单与路由
    # ========================================================================

    @staticmethod
    async def get_current_user_menus_by_scene(
        role_ids: list[int],
        scene: str,
        query_db: AsyncSession,
        redis_session: AsyncRedis,
    ) -> list[FunctionTreeVO]:
        """根据用户 ID 和场景获取当前用户菜单树（用于 Ant Design Menu）

        使用 Redis 缓存角色级别的菜单 VO 对象，多角色数据在运行时合并去重。

        Args:
            role_ids: 用户角色 ID 列表
            scene: 应用场景 (web/admin/mobile)
            query_db: 数据库异步会话对象
            redis_session: Redis 异步会话对象

        Returns:
            list[FunctionTreeVO]: 用户菜单树列表，用于前端菜单渲染
        """
        # 超级管理员（role_id <= 10）使用特殊缓存键 0
        if any(role_id <= 10 for role_id in role_ids):
            return await SecurityService._load_role_menus(0, scene, query_db, redis_session)

        # 按角色分别加载菜单，然后合并去重
        all_menus: dict[int, FunctionTreeVO] = {}  # 使用 function_id 作为去重键
        for role_id in role_ids:
            menus = await SecurityService._load_role_menus(role_id, scene, query_db, redis_session)
            for menu in menus:
                # 使用 function_id 进行去重，递归合并子菜单
                if menu.function_id not in all_menus:
                    all_menus[menu.function_id] = menu
                else:
                    # 如果已存在，合并子菜单
                    existing = all_menus[menu.function_id]
                    if menu.children:
                        if existing.children:
                            # 合并子菜单（简单追加，前端会处理去重）
                            existing.children.extend(menu.children)
                        else:
                            existing.children = menu.children

        # 按 sort_order 排序返回（递归排序子菜单）
        def sort_menus(unsorted_menus: list[FunctionTreeVO]) -> list[FunctionTreeVO]:
            sorted_menus = sorted(unsorted_menus, key=lambda m: m.sort_order)
            for sm in sorted_menus:
                if sm.children:
                    sm.children = sort_menus(sm.children)
            return sorted_menus

        return sort_menus(list(all_menus.values()))

    # ========================================================================
    # 注册
    # ========================================================================

    @staticmethod
    async def register_user(
        user_register: UserRegisterByUsernameDTO, redis_session: AsyncRedis, query_db: AsyncSession
    ):
        """用户注册

        验证注册功能是否启用、验证码是否正确，然后创建新用户。

        Args:
            user_register: 用户注册信息
            redis_session: Redis 异步会话对象
            query_db: 数据库异步会话对象

        Returns:
            注册结果

        Raises:
            RegisterFunctionDisabledException: 当注册功能未启用时
            LoginCaptchaExpiredException: 当验证码已过期时
            LoginCaptchaErrorException: 当验证码错误时
            RegisterIllegalDoublePasswordException: 当两次密码不一致时
        """
        register_enabled = (
            await redis_session.get(
                f"{RedisConstants.System.CONFIG_CACHE_KEY}:{SystemConstants.Config.REGISTER_ENABLED}"
            )
            == "true"
        )
        captcha_enabled = (
            await redis_session.get(
                f"{RedisConstants.System.CONFIG_CACHE_KEY}:{SystemConstants.Config.CAPTCHA_ENABLED}"
            )
            == "true"
        )
        if user_register.password == user_register.confirm_password:
            if register_enabled:
                if captcha_enabled:
                    captcha_value = await redis_session.get(f"{RedisConstants.Auth.CAPTCHA_KEY}:{user_register.uuid}")
                    if not captcha_value:
                        raise LoginCaptchaExpiredException
                    if user_register.code != str(captcha_value):
                        raise LoginCaptchaErrorException
                add_user = UserCreateDTO(
                    user_name=user_register.username,
                    nick_name=user_register.username,
                    password=PasswordUtil.hash_password(user_register.password),
                )
                return await UserService.add_user(query_db, add_user, None)
            raise RegisterFunctionDisabledException
        raise RegisterIllegalDoublePasswordException

    # ========================================================================
    # 登出
    # ========================================================================

    @staticmethod
    async def logout(user_id: int, session_id: str, redis_session: AsyncRedis) -> None:
        """退出登录

        删除 Redis 中存储的 Token，使用户会话失效。

        Args:
            user_id: 用户 ID
            session_id: 会话编号
            redis_session: Redis 异步会话对象

        Returns:
            bool: 退出登录结果，成功返回 True
        """
        if not user_id or (not session_id and not get_config().security.login.single_end):
            raise AppException("Invalid user ID or session ID for logout")
        if get_config().security.login.single_end:
            # 单点登录模式 - 以 user_id 为 key 删除 Token 和用户缓存
            await redis_session.delete(f"{RedisConstants.Auth.TOKEN_KEY}:{user_id}")
            await redis_session.delete(f"{RedisConstants.Auth.USER_CACHE_KEY}:{user_id}")
        else:
            await redis_session.delete(f"{RedisConstants.Auth.TOKEN_KEY}:{session_id}")
            await redis_session.delete(f"{RedisConstants.Auth.USER_CACHE_KEY}:{user_id}")

    # ========== 角色级缓存：只缓存 VO/DTO 对象 ==========

    @staticmethod
    async def _load_menus_from_db(role_ids: list[int], scene: str, query_db: AsyncSession) -> list[FunctionTreeVO]:
        """从数据库加载角色的菜单树 VO

        Args:
            role_ids: 角色 ID 列表（空列表表示超级管理员）
            scene: 应用场景
            query_db: 数据库会话

        Returns:
            list[FunctionTreeVO]: 菜单树 VO 列表
        """
        # 加载原始功能数据
        functions = await FunctionMapper.get_function_list_for_tree_by_user_roles_and_scene(role_ids, scene, query_db)
        # 过滤目录和菜单类型，转换为菜单树
        menu_functions = sorted(
            [
                f
                for f in functions
                if f.function_type in [SystemConstants.FunctionType.DIR, SystemConstants.FunctionType.MENU]
            ],
            key=lambda x: x.sort_order,
        )
        return _generate_menus(0, menu_functions)

    @staticmethod
    async def _load_role_menus(
        role_id: int, scene: str, query_db: AsyncSession, redis_session: AsyncRedis
    ) -> list[FunctionTreeVO]:
        """加载单个角色的菜单 VO（带缓存）

        缓存格式：graphedu:auth:role_cache:{role_id}:{scene}:menus
        缓存内容：菜单 VO 的 JSON 数组
        特殊：role_id=0 表示超级管理员（拥有所有菜单）

        Args:
            role_id: 角色 ID（0 表示超级管理员，从此函数开始后续都不单独判断管理员）
            scene: 应用场景
            query_db: 数据库会话
            redis_session: Redis 会话

        Returns:
            list[FunctionTreeVO]: 菜单树 VO 列表
        """
        cache_key = f"{RedisConstants.Auth.ROLE_CACHE_KEY}:{role_id}:{scene}:menus"

        # 尝试从缓存获取
        cached_data: str | None = await redis_session.get(cache_key)
        if cached_data is not None:
            # 反序列化为 VO 对象
            return [
                FunctionTreeVO.model_validate(d) for d in json.loads(cached_data)
            ]  # 外层是列表，内层是单个对象的字典

        # 缓存未命中，从数据库加载
        # role_id=0 表示超级管理员，传空列表加载所有菜单
        menus = await SecurityService._load_menus_from_db([role_id], scene, query_db)

        # 序列化并缓存 VO 对象，设置过期时间为 1 天
        menus_json = json.dumps([m.model_dump(mode="json") for m in menus], ensure_ascii=False)
        await redis_session.set(cache_key, menus_json, ex=OneDay)

        return menus

    # ========== 缓存失效方法 ==========

    @staticmethod
    async def invalidate_role_cache(
        role_ids: list[int] | set[int],
        redis_session: AsyncRedis,
        scenes: list[str] | None = None,
    ) -> None:
        """清除指定角色的缓存（包括菜单和路由）

        缓存键格式：graphedu:auth:role_cache:{role_id}:{scene}:{type}
        其中 type 为 menus 或 routers
        特殊：当需要清除超级管理员缓存时，请传入 role_id=0

        Args:
            role_ids: 角色 ID 列表（0 表示超级管理员）
            redis_session: Redis 会话
            scenes: 指定场景列表，为 None 时清除所有场景
        """
        if not role_ids:
            return

        for role_id in set(role_ids):
            if scenes is None:
                # 清除该角色的所有缓存（所有场景、所有类型）
                pattern = f"{RedisConstants.Auth.ROLE_CACHE_KEY}:{role_id}:*"
                async for key in redis_session.scan_iter(match=pattern):
                    await redis_session.delete(key)
            else:
                # 清除指定场景的缓存（菜单和路由）
                for scene in scenes:
                    await redis_session.delete(f"{RedisConstants.Auth.ROLE_CACHE_KEY}:{role_id}:{scene}:menus")
                    await redis_session.delete(f"{RedisConstants.Auth.ROLE_CACHE_KEY}:{role_id}:{scene}:routers")

    @staticmethod
    async def invalidate_all_role_cache(redis_session: AsyncRedis) -> None:
        """清除所有角色相关的缓存（包括超级管理员）

        用于功能（菜单）全局变更时，如功能表结构变更。
        会清除所有角色的缓存，包括 role_id=0 的超级管理员缓存。
        """
        pattern = f"{RedisConstants.Auth.ROLE_CACHE_KEY}:*"
        async for key in redis_session.scan_iter(match=pattern):
            await redis_session.delete(key)
