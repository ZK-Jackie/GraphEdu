"""日志相关DTO模型"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery

# ============================================================================
# 操作日志相关 DTO
# ============================================================================


class OperLogQueryDTO(PageQuery):
    """操作日志查询参数"""

    title: str | None = Field(default=None, description="模块标题")
    oper_name: str | None = Field(default=None, description="操作人员")
    oper_ip: str | None = Field(default=None, description="操作地址")
    business_type: str | None = Field(default=None, description="业务类型")
    status: str | None = Field(default=None, description="操作状态（0正常 1异常）")
    begin_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")


class OperLogCreateDTO(DTO):
    """操作日志创建DTO"""

    title: str = Field(default="", description="模块标题")
    business_type: str = Field(default="0", description="业务类型")
    method: str = Field(default="", description="方法名称")
    request_method: str = Field(default="", description="请求方式")
    operator_type: int = Field(default=0, description="操作类别")
    oper_name: str = Field(default="", description="操作人员")
    dept_name: str = Field(default="", description="部门名称")
    oper_url: str = Field(default="", description="请求URL")
    oper_ip: str = Field(default="", description="主机地址")
    oper_location: str = Field(default="", description="操作地点")
    oper_param: str = Field(default="", description="请求参数")
    json_result: str = Field(default="", description="返回参数")
    status: int = Field(default=0, description="操作状态")
    error_msg: str = Field(default="", description="错误消息")
    oper_time: datetime | None = Field(default=None, description="操作时间")
    cost_time: int = Field(default=0, description="消耗时间（毫秒）")


class OperLogDetailDTO(DTO):
    """操作日志详情DTO"""

    oper_id: int = Field(description="日志主键")
    title: str = Field(description="模块标题")
    business_type: int = Field(description="业务类型")
    method: str = Field(description="方法名称")
    request_method: str = Field(description="请求方式")
    operator_type: int = Field(description="操作类别")
    oper_name: str = Field(description="操作人员")
    dept_name: str = Field(description="部门名称")
    oper_url: str = Field(description="请求URL")
    oper_ip: str = Field(description="主机地址")
    oper_location: str = Field(description="操作地点")
    oper_param: str = Field(description="请求参数")
    json_result: str = Field(description="返回参数")
    status: int = Field(description="操作状态")
    error_msg: str = Field(description="错误消息")
    oper_time: datetime = Field(description="操作时间")
    cost_time: int = Field(description="消耗时间（毫秒）")


# ============================================================================
# 登录日志相关 DTO
# ============================================================================


class LoginLogQueryDTO(PageQuery):
    """登录日志查询参数"""

    ipaddr: str | None = Field(default=None, description="登录IP地址")
    user_name: str | None = Field(default=None, description="用户账号")
    status: str | None = Field(default=None, description="登录状态（0成功 1失败）")
    begin_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")


class LoginLogCreateDTO(DTO):
    """登录日志创建DTO"""

    user_name: str = Field(default="", description="用户账号")
    ipaddr: str = Field(default="", description="登录IP地址")
    login_location: str = Field(default="", description="登录地点")
    browser: str = Field(default="", description="浏览器类型")
    os: str = Field(default="", description="操作系统")
    status: str = Field(default="0", description="登录状态（0成功 1失败）")
    msg: str = Field(default="", description="提示消息")
    login_time: datetime | None = Field(default=None, description="访问时间")


class LoginLogDetailDTO(DTO):
    """登录日志详情DTO"""

    info_id: int = Field(description="访问ID")
    user_name: str = Field(description="用户账号")
    ipaddr: str = Field(description="登录IP地址")
    login_location: str = Field(description="登录地点")
    browser: str = Field(description="浏览器类型")
    os: str = Field(description="操作系统")
    status: str = Field(description="登录状态")
    msg: str = Field(description="提示消息")
    login_time: datetime = Field(description="访问时间")


class UnlockUserDTO(DTO):
    """解锁用户DTO"""

    user_name: str = Field(description="用户名")
