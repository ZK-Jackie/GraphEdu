"""日志管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo.base import VO

# ============================================================================
# 操作日志相关 VO
# ============================================================================


class OperLogListVO(VO):
    """操作日志列表项 VO"""

    oper_id: int = Field(description="日志主键")
    title: str = Field(description="模块标题")
    business_type: int = Field(description="业务类型（0其它 1新增 2修改 3删除）")
    method: str = Field(description="方法名称")
    request_method: str = Field(description="请求方式")
    operator_type: int = Field(description="操作类别（0其它 1后台用户 2手机端用户）")
    oper_name: str = Field(description="操作人员")
    oper_ip: str = Field(description="主机地址")
    oper_location: str = Field(description="操作地点")
    oper_time: datetime = Field(description="操作时间")
    status: int = Field(description="操作状态（0正常 1异常）")
    cost_time: int = Field(description="消耗时间（毫秒）")


class OperLogDetailVO(VO):
    """操作日志详情 VO"""

    oper_id: int = Field(description="日志主键")
    title: str = Field(description="模块标题")
    business_type: int = Field(description="业务类型（0其它 1新增 2修改 3删除）")
    method: str = Field(description="方法名称")
    request_method: str = Field(description="请求方式")
    operator_type: int = Field(description="操作类别（0其它 1后台用户 2手机端用户）")
    oper_name: str = Field(description="操作人员")
    dept_name: str = Field(description="部门名称")
    oper_url: str = Field(description="请求URL")
    oper_ip: str = Field(description="主机地址")
    oper_location: str = Field(description="操作地点")
    oper_param: str = Field(description="请求参数")
    json_result: str = Field(description="返回参数")
    status: int = Field(description="操作状态（0正常 1异常）")
    error_msg: str = Field(description="错误消息")
    oper_time: datetime = Field(description="操作时间")
    cost_time: int = Field(description="消耗时间（毫秒）")


# ============================================================================
# 登录日志相关 VO
# ============================================================================


class LoginLogListVO(VO):
    """登录日志列表项 VO"""

    info_id: int = Field(description="访问ID")
    user_name: str = Field(description="用户账号")
    ipaddr: str = Field(description="登录IP地址")
    login_location: str = Field(description="登录地点")
    browser: str = Field(description="浏览器类型")
    os: str = Field(description="操作系统")
    status: str = Field(description="登录状态（0成功 1失败）")
    msg: str = Field(description="提示消息")
    login_time: datetime = Field(description="访问时间")


class LoginLogDetailVO(VO):
    """登录日志详情 VO"""

    info_id: int = Field(description="访问ID")
    user_name: str = Field(description="用户账号")
    ipaddr: str = Field(description="登录IP地址")
    login_location: str = Field(description="登录地点")
    browser: str = Field(description="浏览器类型")
    os: str = Field(description="操作系统")
    status: str = Field(description="登录状态（0成功 1失败）")
    msg: str = Field(description="提示消息")
    login_time: datetime = Field(description="访问时间")
