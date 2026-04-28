"""系统相关实体类
包含所有 sys_ 开头的数据库表对应的实体类
"""

from datetime import datetime

from sqlalchemy import CHAR, TIMESTAMP, BigInteger, Index, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SystemBase(DeclarativeBase):
    """系统模块 SQLAlchemy 2.0 声明式基类

    所有系统相关的 ORM 模型都应继承此基类

    使用方式:
        class SysModel(SystemBase):
            __tablename__ = "sys_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """


# ============================================================================
# 1. 用户基础信息表
# ============================================================================
class SysUser(SystemBase):
    """用户基础信息表。"""

    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="登录账号")
    nick_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="用户昵称")
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码（bcrypt加密）")
    email: Mapped[str] = mapped_column(String(64), default="", comment="用户邮箱")
    phonenumber: Mapped[str] = mapped_column(String(16), default="", comment="手机号码")
    avatar_file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="头像文件ID")
    user_type: Mapped[str] = mapped_column(
        String(2), nullable=True, default="4", comment="用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）"
    )
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="用户状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    login_ip: Mapped[str | None] = mapped_column(String(128), default="", comment="最后登录IP")
    login_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="最后登录时间")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        Index("idx_sys_user_user_name", "user_name"),
        Index("idx_sys_user_email", "email"),
        Index("idx_sys_user_phonenumber", "phonenumber"),
        Index("idx_sys_user_user_type", "user_type"),
        Index("idx_sys_user_status", "status"),
        {"comment": "用户基础信息表"},
    )


# ============================================================================
# 2. 部门信息表
# ============================================================================
class SysDept(SystemBase):
    """部门信息表。"""

    __tablename__ = "sys_dept"

    dept_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="部门ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="父部门ID（0表示根节点）")
    dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="部门名称")
    dept_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="部门编码（唯一标识）")
    leader: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="负责人")
    phone: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="联系电话")
    email: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="联系邮箱")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="部门状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="显示顺序")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        Index("idx_sys_dept_parent_id", "parent_id"),
        Index("idx_sys_dept_dept_key", "dept_key"),
        Index("idx_sys_dept_status", "status"),
        {"comment": "部门信息表"},
    )


# ============================================================================
# 3. 用户和部门关联表
# ============================================================================
class SysUserDept(SystemBase):
    """用户和部门关联表。"""

    __tablename__ = "sys_user_dept"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="用户ID")
    dept_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="部门ID")
    is_primary: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="N", comment="是否主部门，对应 sys_data_option（Y是 N否）"
    )

    __table_args__ = (
        Index("idx_sys_user_dept_user_id", "user_id"),
        Index("idx_sys_user_dept_dept_id", "dept_id"),
        {"comment": "用户和部门关联表（多对多）"},
    )


# ============================================================================
# 4. 角色信息表
# ============================================================================
class SysRole(SystemBase):
    """角色信息表。"""

    __tablename__ = "sys_role"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="角色ID")
    role_name: Mapped[str] = mapped_column(String(30), nullable=False, comment="角色名称")
    role_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="角色唯一标识")
    role_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="显示顺序")
    data_scope: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        default="1",
        comment=(
            "数据范围，对照 sys_role_data_scope"
            "（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限 5：仅本人数据权限）"
        ),
    )
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="角色状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        Index("idx_sys_role_role_key", "role_key"),
        Index("idx_sys_role_sort", "role_sort"),
        {"comment": "角色信息表"},
    )


# ============================================================================
# 5. 用户和角色关联表
# ============================================================================
class SysUserRole(SystemBase):
    """用户和角色关联表。"""

    __tablename__ = "sys_user_role"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="用户ID")
    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="角色ID")

    __table_args__ = {"comment": "用户和角色关联表"}


# ============================================================================
# 6. 功能权限表
# ============================================================================
class SysFunction(SystemBase):
    """功能权限表。"""

    __tablename__ = "sys_function"

    function_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="功能ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="父功能ID（0表示根节点）")
    function_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="功能名称")
    function_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="权限标识（同一场景下全局唯一，如: student:list, course:add, api:user:*）；"
        "GROUP/DIVIDER 类型不需要权限标识，为 NULL",
    )
    function_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="功能类型，对照 sys_function_type"
        "（DIR目录, MENU菜单, BUTTON按钮, INTERFACE接口, GROUP菜单分组, DIVIDER菜单分隔线）",
    )
    route_path: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="路由路径")
    route_cache: Mapped[str | None] = mapped_column(
        CHAR(1),
        nullable=True,
        default=None,
        comment="路由路径页面是否缓存，对应 sys_data_option（Y是 N否）；仅 MENU 类型有效，其他类型为 NULL",
    )
    route_query: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="路由传递参数")
    route_external: Mapped[str | None] = mapped_column(
        CHAR(1),
        nullable=True,
        default=None,
        comment="是否外链，对应 sys_data_option（Y是 N否）；仅 MENU 类型有效，其他类型为 NULL",
    )
    component: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="组件路径")
    layout_component: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="布局组件路径，如 layout/CommonLayout/index，为空则不使用布局"
    )
    icon: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="菜单图标")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="显示顺序")
    visible: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="Y", comment="是否可见，对应 sys_data_option（Y是 N否）"
    )
    style: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="菜单CSS样式（JSON格式，使用css-in-js格式）"
    )
    option_style: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="菜单选项样式（JSON格式）")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="功能状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    scene: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="admin",
        comment="应用场景，对照 sys_function_scene（web用户应用, admin管理系统, userInfo个人中心等）",
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        Index("idx_sys_function_parent_id", "parent_id"),
        Index("idx_sys_function_function_key", "function_key"),
        Index("idx_sys_function_function_type", "function_type"),
        Index("idx_sys_function_scene", "scene"),
        {"comment": "功能权限表"},
    )


# ============================================================================
# 7. 角色功能关联表
# ============================================================================
class SysRoleFunction(SystemBase):
    """角色功能关联表。"""

    __tablename__ = "sys_role_function"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="角色ID")
    function_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="功能ID")

    __table_args__ = (
        Index("idx_sys_role_function_role_id", "role_id"),
        Index("idx_sys_role_function_function_id", "function_id"),
        {"comment": "角色功能关联表"},
    )


# ============================================================================
# 8. 角色部门关联表（数据权限）
# ============================================================================
class SysRoleDept(SystemBase):
    """角色部门关联表（数据权限）。"""

    __tablename__ = "sys_role_dept"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="角色ID")
    dept_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="部门ID")

    __table_args__ = (
        Index("idx_sys_role_dept_role_id", "role_id"),
        Index("idx_sys_role_dept_dept_id", "dept_id"),
        {"comment": "角色和部门关联表（用于配置角色的数据权限范围）"},
    )


# ============================================================================
# 8. 文件上传表
# ============================================================================
class SysUpload(SystemBase):
    """文件上传表。"""

    __tablename__ = "sys_upload"

    file_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="文件ID")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="存储路径/URL/oss对象名")
    file_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="MIME类型（如: image/jpeg, application/pdf）"
    )
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="文件大小（字节）")
    file_category: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        comment="文件分类，对照 sys_upload_file_category（1头像 2课程封面 3书籍封面 4书籍文件 5笔记附件 6作业 7课件）",
    )
    storage_type: Mapped[int] = mapped_column(
        String(2),
        nullable=False,
        default="1",
        comment="存储类型，对照 sys_upload_storage_type（1OSS存储 2本地存储 3CDN存储）",
    )
    # 访问控制
    access_level: Mapped[int] = mapped_column(
        CHAR(1), nullable=False, default="1", comment="访问级别，对照 sys_upload_access_level（1私有 2登录 3公开）"
    )
    download_flag: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="Y", comment="是否允许下载，对照 sys_data_option（Y是 N否）"
    )
    # 统计信息
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="查看次数")
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="下载次数")
    ref_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="被引用次数")
    # 审核信息
    audit_status: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        default="0",
        comment="审核状态，对照 sys_upload_audit_status（0待审核 1审核中 2审核通过 3审核拒绝）",
    )
    audit_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="审核人ID")
    audit_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="审核时间")
    audit_remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="审核备注")
    # 数据状态
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="上传文件状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_ip: Mapped[str] = mapped_column(String(128), default="", comment="上传者IP地址")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="上传者ID")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="上传时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="更新时间")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        Index("idx_sys_upload_file_category", "file_category"),
        Index("idx_sys_upload_create_by", "create_by"),
        Index("idx_sys_upload_status", "status"),
        Index("idx_sys_upload_access_level", "access_level"),
        {"comment": "文件上传表"},
    )


# ============================================================================
# 9. 字典类型表
# ============================================================================
class SysDictType(SystemBase):
    """字典类型表。"""

    __tablename__ = "sys_dict_type"

    dict_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="字典主键")
    dict_name: Mapped[str] = mapped_column(String(100), nullable=False, default="", comment="字典名称")
    dict_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, default="", comment="字典类型")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="字典类型状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="更新时间")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = {"comment": "字典类型表"}


# ============================================================================
# 10. 字典数据表
# ============================================================================
class SysDictData(SystemBase):
    """字典数据表。"""

    __tablename__ = "sys_dict_data"

    dict_code: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="字典编码")
    dict_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="字典排序")
    dict_label: Mapped[str] = mapped_column(String(100), nullable=False, default="", comment="字典标签")
    dict_value: Mapped[str] = mapped_column(String(100), nullable=False, default="", comment="字典键值")
    dict_type: Mapped[str] = mapped_column(String(100), nullable=False, default="", comment="字典类型")
    style: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="数据渲染样式（JSON格式，使用css-in-js格式）"
    )
    color: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="default",
        comment="颜色主题（success | processing | error | warning | default | 自定义 16 进制颜色）",
    )
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="图标（Ant Design Vue图标名称）")
    bordered: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="N", comment="是否带边框（Y是 N否）")
    is_default: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="N", comment="是否默认（Y是 N否）")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="字典数据状态，参照 sys_data_status（0正常 1停用 2已删除）"
    )
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="更新时间")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (Index("idx_sys_dict_data_dict_type", "dict_type"), {"comment": "字典数据表"})


# ============================================================================
# 11. 操作日志表
# ============================================================================
class SysOperLog(SystemBase):
    """操作日志表。"""

    __tablename__ = "sys_oper_log"

    oper_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="日志主键")
    title: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="模块标题")
    business_type: Mapped[int] = mapped_column(
        CHAR(1),
        nullable=False,
        default="0",
        comment="业务类型，对照 sys_oper_log_business_type（0其它 1新增 2修改 3删除 等）",
    )
    method: Mapped[str] = mapped_column(String(100), nullable=False, default="", comment="方法名称")
    request_method: Mapped[str] = mapped_column(String(10), nullable=False, default="", comment="请求方式")
    operator_type: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        default="0",
        comment="操作类别，对照 sys_oper_log_oper_type（0其它 1后台用户 2手机端用户 等）",
    )
    oper_name: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="操作人员")
    dept_name: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="部门名称")
    oper_url: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="请求URL")
    oper_ip: Mapped[str] = mapped_column(String(128), nullable=False, default="", comment="主机地址")
    oper_location: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="操作地点")
    oper_param: Mapped[str] = mapped_column(String(2000), nullable=False, default="", comment="请求参数")
    json_result: Mapped[str] = mapped_column(String(2000), nullable=False, default="", comment="返回参数")
    status: Mapped[int] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="操作日志状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    error_msg: Mapped[str] = mapped_column(String(2000), nullable=False, default="", comment="错误消息")
    oper_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, comment="操作时间")
    cost_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="消耗时间（毫秒）")

    __table_args__ = (
        Index("idx_sys_oper_log_bt", "business_type"),
        Index("idx_sys_oper_log_s", "status"),
        Index("idx_sys_oper_log_ot", "oper_time"),
        {"comment": "操作日志记录"},
    )


# ============================================================================
# 12. 登录日志表
# ============================================================================
class SysLogininfor(SystemBase):
    """登录日志表。"""

    __tablename__ = "sys_logininfor"

    info_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="访问ID")
    user_name: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="用户账号")
    ipaddr: Mapped[str] = mapped_column(String(128), nullable=False, default="", comment="登录IP地址")
    login_location: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="登录地点")
    browser: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="浏览器类型")
    os: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="操作系统")
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="登录日志状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )
    msg: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="提示消息")
    login_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, comment="访问时间")

    __table_args__ = (
        Index("idx_sys_logininfor_s", "status"),
        Index("idx_sys_logininfor_lt", "login_time"),
        {"comment": "系统访问记录"},
    )


# ============================================================================
# 13. 定时任务表
# ============================================================================
class SysJob(SystemBase):
    """定时任务表。"""

    __tablename__ = "sys_job"

    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    job_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="任务名称")
    job_group: Mapped[str] = mapped_column(
        String(64), nullable=False, default="DEFAULT", comment="任务分组（DEFAULT=默认, SYSTEM=系统）"
    )
    job_executor: Mapped[str] = mapped_column(
        String(32), nullable=False, default="python", comment="执行器类型（python=Python函数, webhook=Webhook调用）"
    )
    invoke_target: Mapped[str] = mapped_column(String(512), nullable=False, comment="调用目标字符串")
    job_args: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="位置参数（JSON格式）")
    job_kwargs: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="关键字参数（JSON格式）")
    cron_expression: Mapped[str] = mapped_column(String(128), nullable=False, comment="Cron执行表达式")
    misfire_policy: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="1", comment="执行策略（1=立即执行, 2=执行一次, 3=放弃执行）"
    )
    concurrent: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0", comment="是否并发（0=禁止, 1=允许）")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0", comment="任务状态（0=正常, 1=暂停）")
    webhook_enabled: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0", comment="是否启用Webhook（0=否, 1=是）"
    )
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="Webhook URL")
    webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="Webhook密钥")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间（由应用程序更新）"
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        Index("idx_sys_job_job_group", "job_group"),
        Index("idx_sys_job_job_executor", "job_executor"),
        Index("idx_sys_job_status", "status"),
        {"comment": "定时任务表"},
    )


# ============================================================================
# 14. 定时任务执行日志表
# ============================================================================
class SysJobLog(SystemBase):
    """定时任务执行日志表。"""

    __tablename__ = "sys_job_log"

    job_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    job_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务ID")
    job_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="任务名称")
    job_group: Mapped[str] = mapped_column(String(64), nullable=False, comment="任务分组")
    invoke_target: Mapped[str] = mapped_column(String(512), nullable=False, comment="调用目标字符串")
    job_message: Mapped[str | None] = mapped_column(String(2000), nullable=True, comment="执行信息")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0", comment="执行状态（0=成功, 1=失败）")
    exception_info: Mapped[str | None] = mapped_column(String(2000), nullable=True, comment="异常信息")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")

    __table_args__ = (
        Index("idx_sys_job_log_job_id", "job_id"),
        Index("idx_sys_job_log_status", "status"),
        Index("idx_sys_job_log_create_time", "create_time"),
        {"comment": "定时任务执行日志表"},
    )


# ============================================================================
# 异步任务表
# ============================================================================
class SysAsyncTask(SystemBase):
    """通用异步任务表。

    所有需要异步执行且需要持久化状态跟踪的任务统一使用此表。
    通过 task_type 区分不同业务类型的任务。
    """

    __tablename__ = "sys_async_task"

    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    task_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="任务名称（人类可读）")
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="任务类型标识")
    task_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", comment="任务状态（pending/processing/success/failed/cancelled）"
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Celery 任务 ID")
    task_params: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True, comment="任务输入参数（JSON）")
    task_result: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True, comment="任务输出结果（JSON）")
    task_message: Mapped[str | None] = mapped_column(String(2000), nullable=True, comment="进度描述或错误信息")
    progress_percent: Mapped[int] = mapped_column(SmallInteger, default=0, comment="进度百分比（0-100）")
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="提交者用户ID")
    start_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="开始执行时间")
    end_time: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, comment="完成时间")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0", comment="数据状态（0正常 2已删除）")
    create_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者")
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间"
    )

    __table_args__ = (
        Index("idx_sys_async_task_type", "task_type"),
        Index("idx_sys_async_task_status", "task_status"),
        Index("idx_sys_async_task_user_id", "user_id"),
        Index("idx_sys_async_task_create_time", "create_time"),
        {"comment": "通用异步任务表"},
    )
