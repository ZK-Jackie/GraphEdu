"""系统常量定义模块

本模块定义了系统使用的各种常量，包括：

- **project_prefix**: Redis 键前缀
- **CommonConstants**: 通用常量（HTTP、HTTPS、WWW 前缀等）
- **RedisConstants**: Redis 键名常量
- **SystemConstants**: 系统状态和配置常量
"""

project_prefix = "graphedu:"


class CommonConstants:
    """通用常量类

    定义系统中使用的通用协议和前缀常量
    """

    HTTP = "http://"
    """HTTP 协议前缀"""

    HTTPS = "https://"
    """HTTPS 协议前缀"""

    WWW = "www."
    """WWW 子域名前缀"""


class RedisConstants:
    """Redis 键常量定义

    定义所有 Redis 存储的键名前缀和格式
    """

    class System:
        """系统相关的 Redis 键常量

        用于存储系统级别的缓存数据，如在线用户、系统配置等
        """

        ONLINE_USER_KEY = project_prefix + "system:online_user"
        """在线用户键前缀"""

        CONFIG_CACHE_KEY = project_prefix + "system:config_cache"
        """系统配置缓存键前缀"""

    class UserInfo:
        """用户信息缓存键"""

        USER_INFO_KEY = project_prefix + "user:info"
        """用户信息键前缀，值为用户信息的 JSON 字符串"""

    class Auth:
        """登录/认证相关的 Redis 键常量

        用于存储用户认证信息，包括：
        - 登录密码错误计数
        - 登录失败锁定状态
        - 验证码
        - JWT Token
        - 用户功能数据缓存（统一数据源，按需转换为菜单/路由）
        """

        LOGIN_PASSWORD_ERROR_CNT_KEY = project_prefix + "auth:password_error_count"
        """用户密码错误计数键前缀，值为整数次数"""

        LOGIN_FAIL_LOCK_KEY = project_prefix + "auth:login_fail_lock"
        """用户登录失败锁定键前缀，值为布尔类型"""

        CAPTCHA_KEY = project_prefix + "auth:captcha"
        """用户登录验证码键前缀，值为验证码答案字符串"""

        SMS_CODE_KEY = project_prefix + "auth:sms_code"
        """密码重置短信验证码键前缀，值为6位数字验证码"""

        SMS_RATE_LIMIT_KEY = project_prefix + "auth:sms_rate_limit"
        """短信验证码发送频率限制键前缀，值为发送标记"""

        TOKEN_KEY = project_prefix + "auth:token"
        """用户登录Token键前缀，值为用户id"""

        USER_CACHE_KEY = project_prefix + "auth:user_cache"
        """CurrentUser 对象缓存键前缀，值为 CurrentUser 对象的 JSON 字符串"""

        # ========== 角色级缓存（单角色 + VO/DTO 对象） ==========

        ROLE_CACHE_KEY = project_prefix + "auth:role_cache"
        """角色缓存键前缀，格式: {prefix}:{role_id}:{scene}:{type}

        缓存内容：转换后的 VO/DTO 对象的 JSON 数组（不缓存 ORM 对象）
        type 可选值：menus（菜单树 VO）、routers（路由 VO）

        设计原则：
            - 只缓存 VO/DTO 对象，不缓存 SQLAlchemy ORM 对象
            - 按单个角色存储，用户多角色数据在运行时合并去重
            - 分离菜单和路由缓存，按需加载
            - 超级管理员使用 role_id=0 作为特殊缓存键

        示例：
            graphedu:auth:role_cache:0:admin:menus   → 超级管理员在 admin 场景的菜单树 VO
            graphedu:auth:role_cache:0:admin:routers → 超级管理员在 admin 场景的路由 VO
            graphedu:auth:role_cache:1:admin:menus   → 角色 1 在 admin 场景的菜单树 VO
            graphedu:auth:role_cache:1:admin:routers → 角色 1 在 admin 场景的路由 VO
            graphedu:auth:role_cache:2:web:menus     → 角色 2 在 web 场景的菜单树 VO

        优势：
            - 无数据冗余：每个角色的数据只存储一次
            - 避免击穿：超级管理员也享有缓存，不会每次查库
            - 失效简单：role_id=1 变更时直接删除 role_cache:1:*
            - 命中率高：新角色组合不会全部缓存未命中
            - 架构清晰：只缓存视图对象，符合缓存最佳实践
        """

    class Common:
        """通用 Redis 键常量

        用于存储通用的缓存数据，如验证码、字典类型等
        """

        CAPTCHA_KEY = project_prefix + "common:captcha"
        """通用验证码键前缀，值为验证码答案字符串"""

        DICT_TYPE = project_prefix + "common:dict"
        """字典类型键前缀，键为字典类型名称，值为字典数据列表的JSON字符串"""


class SystemConstants:
    """系统常量类

    定义系统运行状态、功能类型、业务类型等常量
    """

    class Common:
        """通用协议常量"""

        HTTP = "http://"
        HTTPS = "https://"
        WWW = "www."

    class Running:
        """系统运行模式常量

        定义系统的运行环境模式
        """

        DEV = "dev"
        """当前系统运行状态为开发模式"""

        PROD = "prod"
        """当前系统运行状态为生产模式"""

    class Status:
        """系统状态常量

        定义系统中各种状态的标识，如数据状态、用户状态等
        """

        NORMAL = "0"
        """正常状态"""

        DISABLED = "1"
        """停用状态"""

        DELETED = "2"
        """已删除状态"""

        YES = "Y"
        """是"""

        NO = "N"
        """否"""

    class AccessLevel:
        """文件访问级别，对应 sys_upload_access_level 字典"""

        PRIVATE = "1"
        """私密访问级别，文件仅上传者可访问"""

        PROTECTED = "2"
        """仅平台登录用户可访问"""

        PUBLIC = "3"
        """公共访问级别，任何人可访问"""

    class UserType:
        """用户类型常量，对应 sys_user_type 字典"""

        STUDENT = "1"
        """后台用户类型，具有管理系统的权限"""

        TEACHER = "2"
        """手机端用户类型，使用移动设备访问系统"""

        ADMIN = "3"
        """微信用户类型，通过微信登录访问系统"""

        OTHER = "4"
        """其它用户类型，未分类的用户类型"""

    class StorageType:
        """文件存储类型，对应 sys_upload_storage_type 字典"""

        OSS = "1"
        """对象存储（OSS）类型，文件存储在第三方对象存储服务"""

        LOCAL = "2"
        """本地存储类型，文件存储在服务器本地磁盘"""

        CDN = "3"
        """CDN存储类型，文件存储在CDN加速服务上"""

    class FileCategory:
        """文件分类常量，对应 sys_upload_file_category 字典"""

        AVATAR = "1"
        """头像文件分类，用户个人头像图片"""

        COURSE_COVER = "2"
        """课程封面文件分类，课程的封面图片"""

        BOOK_COVER = "3"
        """图书封面文件分类，图书的封面图片"""

        BOOK_FILE = "4"
        """图书文件分类，图书的内容文件（如PDF）"""

        ATTACHMENT = "5"
        """附件文件分类，其他类型的附件文件"""

        HOMEWORK_FILE = "6"
        """作业文件分类，学生提交的作业文件"""

        TEACHING_MATERIAL = "7"
        """教学资料文件分类，教师上传的教学资料文件"""

    class FunctionType:
        """功能类型常量

        定义系统中不同功能的类型标识（使用字符串枚举）：
        - DIR: 目录（用于构建菜单层级结构）
        - MENU: 菜单项（可点击跳转的页面）
        - BUTTON: 按钮（页面内操作权限控制）
        - INTERFACE: 接口（API接口访问控制）
        - GROUP: 菜单分组（菜单中分组显示）
        - DIVIDER: 菜单分隔线（菜单视觉分隔）
        """

        DIR = "DIR"
        """目录类型，用于 sys_function.function_type 字段"""
        MENU = "MENU"
        """菜单类型，用于 sys_function.function_type 字段"""
        BUTTON = "BUTTON"
        """按钮类型，用于 sys_function.function_type 字段"""
        INTERFACE = "INTERFACE"
        """接口类型，用于 sys_function.function_type 字段"""
        GROUP = "GROUP"
        """分组类型，用于 sys_function.function_type 字段"""
        DIVIDER = "DIVIDER"
        """分隔线类型，用于 sys_function.function_type 字段"""

    class BusinessType:
        """业务操作类型常量，对应 sys_oper_log_business_type 字典

        定义系统中各种业务操作的类型标识，用于日志记录和权限控制

        Attributes:
            OTHER: 其它操作
            INSERT: 新增操作
            UPDATE: 修改操作
            DELETE: 删除操作
            GRANT: 授权操作
            EXPORT: 导出操作
            IMPORT: 导入操作
            FORCE: 强退操作
            GENCODE: 生成代码操作
            CLEAN: 清空数据操作
        """

        OTHER = "0"
        INSERT = "1"
        UPDATE = "2"
        DELETE = "3"
        GRANT = "4"
        EXPORT = "5"
        IMPORT = "6"
        FORCE = "7"
        GENCODE = "8"
        CLEAN = "9"

    class OperatorType:
        """操作人类别常量，对应 sys_oper_log_operator_type 字典

        定义系统中操作人的类别标识，用于日志记录和权限控制

        Attributes:
            OTHER: 其它
            MANAGE: 后台用户
            MOBILE: 手机端用户
            WECHAT: 微信用户
            API: API接口
        """

        OTHER = "0"
        MANAGE = "1"
        MOBILE = "2"
        WECHAT = "3"
        API = "4"

    class Datascope:
        """数据权限范围常量，对应 sys_role_data_scope 字典

        定义角色数据权限的访问范围：
        - ALL: 全部数据权限
        - CUSTOM: 自定义数据权限
        - DEPT_ONLY: 本部门数据权限
        - DEPT_AND_CHILD: 本部门及以下数据权限
        - SELF_ONLY: 仅本人数据权限
        """

        ALL = "1"
        """全部数据权限"""

        CUSTOM = "2"
        """自定义数据权限"""

        DEPT_ONLY = "3"
        """本部门数据权限"""

        DEPT_AND_CHILD = "4"
        """本部门及以下数据权限"""

        SELF_ONLY = "5"
        """仅本人数据权限"""

    class Config:
        """系统配置项键常量

        定义系统中可配置的配置项键名，用于动态配置系统行为
        """

        CAPTCHA_ENABLED = "sys.account.captchaEnabled"
        """是否启用验证码配置项键"""

        REGISTER_ENABLED = "sys.account.registerEnabled"
        """是否启用注册配置项键"""

    class ProcessStatus:
        """文档、文档索引、GraphRAG 处理状态（通用）"""

        PENDING = "0"
        """准备就绪、未处理状态，表示流程已准备好但尚未开始执行"""

        RUNNING = "1"
        """运行中状态，表示流程正在执行中"""

        COMPLETED = "2"
        """已完成状态，表示流程已成功执行完毕"""

        ERROR = "3"
        """失败状态，流程执行失败，可能由于异常或错误导致未能完成"""

        CANCELLED = "4"
        """已取消状态，流程被用户主动取消"""

        NO_ACTION = "9"
        """无需处理"""
