"""错误码定义

使用分层错误码：模块.编号

模块编号分配：
- SYS:    系统通用     1xxx, 9xxx
- AUTH:   认证授权     10xxx-13xxx
          10xxx: 认证基础
          11xxx: 登录
          12xxx: 注册
          13xxx: 密码
- USER:   用户管理     20xxx-21xxx
          20xxx: 用户基础
          21xxx: 用户操作
- DEPT:   部门管理     30xxx
- ROLE:   角色权限     40xxx
- FUNCTION: 功能权限   41xxx
- DICT:   数据字典     50xxx
- FILE:   文件操作     60xxx
- UPLOAD: 文件上传     70xxx
- DOWNLOAD: 文件下载   71xxx
- LLM:    LLM/AI      80xxx
- SYLLABUS_GRAPH: 大纲图谱 85xxx
- LOG:    日志审计     90xxx
"""

from enum import StrEnum

from fastapi import status as HttpStatus


class ErrorCode(StrEnum):
    """分层错误码定义：模块.编号

    每个错误码是一个元组：(错误码字符串, 默认HTTP状态码)

    Example:
        >>> ErrorCode.AUTH_TOKEN_EXPIRED.value
        ("AUTH.10001", 401)
        >>> ErrorCode.AUTH_TOKEN_EXPIRED.code
        "AUTH.10001"
        >>> ErrorCode.AUTH_TOKEN_EXPIRED.http_status
        401
    """

    http_status: int

    def __new__(cls, code: str, http_status: int):
        """创建枚举成员

        Args:
            code: 错误码字符串 (如 "AUTH.10001")
            http_status: 默认HTTP状态码 (如 401)
        """
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.http_status = http_status
        return obj

    @property
    def code(self) -> str:
        """获取错误码字符串"""
        return self.value

    @property
    def module(self) -> str:
        """获取模块名"""
        return self.value.split(".")[0]

    @property
    def code_num(self) -> int:
        """获取错误码数字部分"""
        return int(self.value.split(".")[1])

    # ============================================================================
    # 系统通用错误 1xxx, 9xxx
    # ============================================================================

    # 基础系统错误 1xxx

    SYSTEM_ERROR = ("SYS.1000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """系统错误，请稍后再试"""

    SYSTEM_BUSY = ("SYS.1001", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """系统繁忙，请稍后再试"""

    SYSTEM_TIMEOUT = ("SYS.1002", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """系统超时，请稍后再试"""

    SYSTEM_CONFIG_ERROR = ("SYS.1003", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """系统配置错误"""

    SYSTEM_DATABASE_ERROR = ("SYS.1004", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """数据库错误，请稍后再试"""

    SYSTEM_NETWORK_ERROR = ("SYS.1005", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """网络错误，请检查网络连接"""

    # 文件相关 9xxx

    FILE_NOT_FOUND = ("SYS.9001", HttpStatus.HTTP_404_NOT_FOUND)
    """文件不存在"""

    FILE_READ_ERROR = ("SYS.9002", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """文件读取失败"""

    FILE_WRITE_ERROR = ("SYS.9003", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """文件写入失败"""

    FILE_PARSE_ERROR = ("SYS.9004", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """文件解析失败"""

    FILE_DELETE_ERROR = ("SYS.9005", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """文件删除失败"""

    # 配置相关

    CONFIG_READ_ERROR = ("SYS.9101", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """配置文件读取失败"""

    CONFIG_VALIDATION_ERROR = ("SYS.9102", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """配置验证失败"""

    # 验证相关

    VALIDATION_ERROR = ("SYS.9201", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """数据验证失败"""

    TYPE_CONVERSION_ERROR = ("SYS.9202", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """类型转换失败"""

    JSON_PARSE_ERROR = ("SYS.9203", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """JSON解析失败"""

    JSON_VALIDATION_ERROR = ("SYS.9204", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """JSON验证失败"""

    # 并发相关

    RATE_LIMIT_ERROR = ("SYS.9301", HttpStatus.HTTP_429_TOO_MANY_REQUESTS)
    """请求过于频繁，请稍后再试"""

    TIMEOUT_ERROR = ("SYS.9302", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """操作超时，请稍后再试"""

    LOCK_ERROR = ("SYS.9303", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """系统繁忙，请稍后再试"""

    # ============================================================================
    # 认证授权 10xxx-13xxx
    # ============================================================================

    # 认证基础 10xxx

    AUTH_FAILED = ("AUTH.10000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """认证失败"""

    AUTH_TOKEN_MISSING = ("AUTH.10001", HttpStatus.HTTP_401_UNAUTHORIZED)
    """缺少认证令牌"""

    AUTH_TOKEN_EXPIRED = ("AUTH.10002", HttpStatus.HTTP_401_UNAUTHORIZED)
    """认证令牌已过期"""

    AUTH_TOKEN_INVALID = ("AUTH.10003", HttpStatus.HTTP_401_UNAUTHORIZED)
    """认证令牌无效"""

    AUTH_TOKEN_MALFORMED = ("AUTH.10004", HttpStatus.HTTP_401_UNAUTHORIZED)
    """认证令牌格式错误"""

    AUTH_TOKEN_SIGNATURE_INVALID = ("AUTH.10005", HttpStatus.HTTP_401_UNAUTHORIZED)
    """认证令牌签名无效"""

    AUTH_TOKEN_REFRESH_FAILED = ("AUTH.10006", HttpStatus.HTTP_401_UNAUTHORIZED)
    """认证令牌刷新失败"""

    AUTH_NO_PERMISSION = ("AUTH.10020", HttpStatus.HTTP_403_FORBIDDEN)
    """当前操作没有权限"""

    AUTH_NO_INTERFACE_PERMISSION = ("AUTH.10021", HttpStatus.HTTP_403_FORBIDDEN)
    """当前用户没有接口访问权限"""

    AUTH_NO_FUNCTION_PERMISSION = ("AUTH.10022", HttpStatus.HTTP_403_FORBIDDEN)
    """当前用户没有功能访问权限"""

    # 登录相关 11xxx

    LOGIN_FAILED = ("AUTH.11000", HttpStatus.HTTP_401_UNAUTHORIZED)
    """登录失败"""

    LOGIN_USER_NOT_FOUND = ("AUTH.11001", HttpStatus.HTTP_401_UNAUTHORIZED)
    """用户不存在"""

    LOGIN_PASSWORD_ERROR = ("AUTH.11002", HttpStatus.HTTP_401_UNAUTHORIZED)
    """用户名或密码错误"""

    LOGIN_USERNAME_LOCKED = ("AUTH.11031", HttpStatus.HTTP_403_FORBIDDEN)
    """账号已被锁定，请尝试使用其他登录方式"""

    LOGIN_ACCOUNT_LOCKED = ("AUTH.11032", HttpStatus.HTTP_403_FORBIDDEN)
    """账号已被锁定"""

    LOGIN_ACCOUNT_DISABLED = ("AUTH.11033", HttpStatus.HTTP_403_FORBIDDEN)
    """账号已被禁用"""

    LOGIN_ACCOUNT_EXPIRED = ("AUTH.11004", HttpStatus.HTTP_401_UNAUTHORIZED)
    """账号已过期"""

    LOGIN_ACCOUNT_NOT_ACTIVATED = ("AUTH.11034", HttpStatus.HTTP_403_FORBIDDEN)
    """账号未激活"""

    LOGIN_ACCOUNT_PENDING_REVIEW = ("AUTH.11035", HttpStatus.HTTP_403_FORBIDDEN)
    """账号待审核"""

    LOGIN_ACCOUNT_REJECTED = ("AUTH.11036", HttpStatus.HTTP_403_FORBIDDEN)
    """账号审核未通过"""

    LOGIN_IP_INVALID = ("AUTH.11037", HttpStatus.HTTP_403_FORBIDDEN)
    """登录网络环境异常"""

    LOGIN_CREDENTIALS_EXPIRED = ("AUTH.11005", HttpStatus.HTTP_401_UNAUTHORIZED)
    """用户凭证已过期"""

    LOGIN_SESSION_EXPIRED = ("AUTH.11006", HttpStatus.HTTP_401_UNAUTHORIZED)
    """登录会话已过期"""

    LOGIN_SESSION_INVALID = ("AUTH.11007", HttpStatus.HTTP_401_UNAUTHORIZED)
    """登录会话无效"""

    LOGIN_CAPTCHA_ERROR = ("AUTH.11010", HttpStatus.HTTP_400_BAD_REQUEST)
    """验证码错误"""

    LOGIN_CAPTCHA_EXPIRED = ("AUTH.11011", HttpStatus.HTTP_400_BAD_REQUEST)
    """验证码已过期"""

    LOGIN_CAPTCHA_REQUIRED = ("AUTH.11012", HttpStatus.HTTP_400_BAD_REQUEST)
    """请输入验证码"""

    LOGIN_TIMEOUT = ("AUTH.11013", HttpStatus.HTTP_408_REQUEST_TIMEOUT)
    """登录超时"""

    LOGIN_UNSUPPORTED = ("AUTH.11014", HttpStatus.HTTP_400_BAD_REQUEST)
    """不支持的登录方式"""

    LOGIN_USER_NOT_LOCKED = ("AUTH.11015", HttpStatus.HTTP_400_BAD_REQUEST)
    """用户未被锁定"""

    LOGIN_TOO_MANY_ATTEMPTS = ("AUTH.11029", HttpStatus.HTTP_429_TOO_MANY_REQUESTS)
    """登录尝试次数过多，请稍后再试"""

    LOGIN_STUDENT_NOT_FOUND = ("AUTH.11040", HttpStatus.HTTP_401_UNAUTHORIZED)
    """学号不存在或未关联用户账号"""

    LOGIN_TEACHER_NOT_FOUND = ("AUTH.11041", HttpStatus.HTTP_401_UNAUTHORIZED)
    """工号不存在或未关联用户账号"""

    LOGIN_PHONE_NOT_FOUND = ("AUTH.11042", HttpStatus.HTTP_401_UNAUTHORIZED)
    """手机号未注册"""

    # 注册相关 12xxx

    REGISTER_FAILED = ("AUTH.12000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """注册失败"""

    REGISTER_FUNCTION_DISABLED = ("AUTH.12030", HttpStatus.HTTP_403_FORBIDDEN)
    """注册功能已关闭，暂不支持新用户注册"""

    REGISTER_ILLEGAL_USERNAME = ("AUTH.12101", HttpStatus.HTTP_400_BAD_REQUEST)
    """用户名不合法"""

    REGISTER_ILLEGAL_EMAIL = ("AUTH.12102", HttpStatus.HTTP_400_BAD_REQUEST)
    """邮箱不合法"""

    REGISTER_ILLEGAL_PHONE = ("AUTH.12103", HttpStatus.HTTP_400_BAD_REQUEST)
    """手机号不合法"""

    REGISTER_ILLEGAL_PASSWORD = ("AUTH.12104", HttpStatus.HTTP_400_BAD_REQUEST)
    """密码非法，请重新设置"""

    REGISTER_ILLEGAL_DOUBLE_PASSWORD = ("AUTH.12105", HttpStatus.HTTP_400_BAD_REQUEST)
    """两次输入的密码不一致，请重新输入"""

    REGISTER_USERNAME_ALREADY_EXISTS = ("AUTH.12201", HttpStatus.HTTP_409_CONFLICT)
    """用户注册失败，用户名已被注册"""

    REGISTER_PHONENUMBER_ALREADY_EXISTS = ("AUTH.12202", HttpStatus.HTTP_409_CONFLICT)
    """用户注册失败，手机号已被注册"""

    REGISTER_EMAIL_ALREADY_EXISTS = ("AUTH.12203", HttpStatus.HTTP_409_CONFLICT)
    """用户注册失败，邮箱已被注册"""

    # 密码相关 13xxx

    PASSWORD_TOO_WEAK = ("AUTH.13010", HttpStatus.HTTP_400_BAD_REQUEST)
    """密码强度不足"""

    PASSWORD_SAME_AS_OLD = ("AUTH.13011", HttpStatus.HTTP_400_BAD_REQUEST)
    """新密码不能与旧密码相同"""

    PASSWORD_INCORRECT = ("AUTH.13012", HttpStatus.HTTP_400_BAD_REQUEST)
    """用户名或密码错误"""

    PASSWORD_EXPIRED = ("AUTH.13030", HttpStatus.HTTP_403_FORBIDDEN)
    """密码已过期，请修改密码"""

    PASSWORD_RESET_REQUIRED = ("AUTH.13031", HttpStatus.HTTP_403_FORBIDDEN)
    """需要重置密码"""

    PASSWORD_RESET_SMS_CODE_EXPIRED = ("AUTH.13040", HttpStatus.HTTP_400_BAD_REQUEST)
    """短信验证码已过期"""

    PASSWORD_RESET_SMS_CODE_ERROR = ("AUTH.13041", HttpStatus.HTTP_400_BAD_REQUEST)
    """短信验证码错误"""

    PASSWORD_RESET_SMS_CODE_SEND_TOO_FREQUENT = ("AUTH.13042", HttpStatus.HTTP_429_TOO_MANY_REQUESTS)
    """短信验证码发送过于频繁，请稍后再试"""

    # ============================================================================
    # 用户管理 20xxx-21xxx
    # ============================================================================

    # 用户基础 20xxx

    USER_NOT_FOUND = ("USER.20001", HttpStatus.HTTP_404_NOT_FOUND)
    """用户不存在"""

    USER_DISABLED = ("USER.20030", HttpStatus.HTTP_403_FORBIDDEN)
    """用户已被禁用"""

    USER_DEACTIVATED = ("USER.20031", HttpStatus.HTTP_403_FORBIDDEN)
    """用户已被停用"""

    USER_ALREADY_EXISTS = ("USER.20200", HttpStatus.HTTP_409_CONFLICT)
    """用户已存在"""

    USER_EMAIL_ALREADY_EXISTS = ("USER.20201", HttpStatus.HTTP_409_CONFLICT)
    """邮箱已被注册"""

    USER_PHONE_ALREADY_EXISTS = ("USER.20202", HttpStatus.HTTP_409_CONFLICT)
    """手机号已被注册"""

    # 用户操作 21xxx

    USER_OPERATION_FAILED = ("USER.21000", HttpStatus.HTTP_400_BAD_REQUEST)
    """操作失败，请稍后重试"""

    USER_RESET_PASSWORD_OLD_INCORRECT = ("USER.21101", HttpStatus.HTTP_400_BAD_REQUEST)
    """重置密码失败，旧密码不正确"""

    USER_RESET_PASSWORD_UNCHANGED = ("USER.21102", HttpStatus.HTTP_400_BAD_REQUEST)
    """重置密码失败，新密码不能与旧密码相同"""

    USER_UPDATE_FAILED = ("USER.21900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """用户信息更新失败"""

    USER_DELETE_FAILED = ("USER.21901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """用户删除失败"""

    USER_DELETE_ADMIN = ("USER.21030", HttpStatus.HTTP_403_FORBIDDEN)
    """不允许删除超级管理员用户"""

    USER_DELETE_SELF = ("USER.21031", HttpStatus.HTTP_403_FORBIDDEN)
    """不允许删除当前登录用户"""

    # 用户身份绑定 21200-21251

    USER_IDENTITY_ALREADY_BOUND = ("USER.21200", HttpStatus.HTTP_409_CONFLICT)
    """用户已绑定身份"""

    USER_IDENTITY_NOT_BOUND = ("USER.21201", HttpStatus.HTTP_400_BAD_REQUEST)
    """用户未绑定身份"""

    USER_IDENTITY_NOT_FOUND = ("USER.21202", HttpStatus.HTTP_404_NOT_FOUND)
    """待绑定的身份信息不存在"""

    USER_IDENTITY_ALREADY_BOUND_BY_OTHER = ("USER.21203", HttpStatus.HTTP_409_CONFLICT)
    """该身份已被其他用户绑定"""

    USER_IDENTITY_MISMATCH = ("USER.21204", HttpStatus.HTTP_400_BAD_REQUEST)
    """身份ID与用户ID不匹配"""

    # ============================================================================
    # 部门管理 30xxx
    # ============================================================================

    DEPT_NOT_FOUND = ("DEPT.30001", HttpStatus.HTTP_404_NOT_FOUND)
    """部门不存在"""

    DEPT_ALREADY_EXISTS = ("DEPT.30200", HttpStatus.HTTP_409_CONFLICT)
    """部门已存在"""

    DEPT_NAME_ALREADY_EXISTS = ("DEPT.30201", HttpStatus.HTTP_409_CONFLICT)
    """部门名称已存在"""

    DEPT_KEY_ALREADY_EXISTS = ("DEPT.30202", HttpStatus.HTTP_409_CONFLICT)
    """部门编码已存在"""

    DEPT_PARENT_NOT_FOUND = ("DEPT.30002", HttpStatus.HTTP_404_NOT_FOUND)
    """父部门不存在"""

    DEPT_PARENT_DISABLED = ("DEPT.30101", HttpStatus.HTTP_400_BAD_REQUEST)
    """父部门已停用，不允许新增子部门"""

    DEPT_PARENT_IS_ITSELF = ("DEPT.30102", HttpStatus.HTTP_400_BAD_REQUEST)
    """上级部门不能是自己"""

    DEPT_PARENT_CYCLE = ("DEPT.30103", HttpStatus.HTTP_400_BAD_REQUEST)
    """不能将父部门设为自己的子部门"""

    DEPT_HAS_ACTIVE_CHILDREN = ("DEPT.30104", HttpStatus.HTTP_400_BAD_REQUEST)
    """部门包含未停用的子部门"""

    DEPT_HAS_CHILDREN = ("DEPT.30105", HttpStatus.HTTP_400_BAD_REQUEST)
    """该部门存在子部门，无法删除"""

    DEPT_HAS_USERS = ("DEPT.30106", HttpStatus.HTTP_400_BAD_REQUEST)
    """该部门存在用户，无法删除"""

    DEPT_CREATE_FAILED = ("DEPT.30900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """部门创建失败"""

    DEPT_UPDATE_FAILED = ("DEPT.30901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """部门更新失败"""

    DEPT_DELETE_FAILED = ("DEPT.30902", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """部门删除失败"""

    DEPT_ID_LIST_EMPTY = ("DEPT.30107", HttpStatus.HTTP_400_BAD_REQUEST)
    """部门ID列表为空"""

    DEPT_NO_PERMISSION = ("DEPT.30108", HttpStatus.HTTP_403_FORBIDDEN)
    """没有权限访问该部门数据"""

    # ============================================================================
    # 角色权限 40xxx
    # ============================================================================

    ROLE_NOT_FOUND = ("ROLE.40001", HttpStatus.HTTP_404_NOT_FOUND)
    """角色不存在"""

    ROLE_ALREADY_EXISTS = ("ROLE.40200", HttpStatus.HTTP_409_CONFLICT)
    """角色已存在"""

    ROLE_NAME_ALREADY_EXISTS = ("ROLE.40201", HttpStatus.HTTP_409_CONFLICT)
    """角色名称已存在"""

    ROLE_KEY_ALREADY_EXISTS = ("ROLE.40202", HttpStatus.HTTP_409_CONFLICT)
    """角色标识已存在"""

    ROLE_ID_LIST_EMPTY = ("ROLE.40101", HttpStatus.HTTP_400_BAD_REQUEST)
    """角色ID列表为空"""

    ROLE_MODIFY_ADMIN_FORBIDDEN = ("ROLE.40301", HttpStatus.HTTP_403_FORBIDDEN)
    """不允许修改超级管理员角色"""

    ROLE_DELETE_ADMIN_FORBIDDEN = ("ROLE.40302", HttpStatus.HTTP_403_FORBIDDEN)
    """不允许删除超级管理员角色"""

    ROLE_CHANGE_ADMIN_STATUS_FORBIDDEN = ("ROLE.40303", HttpStatus.HTTP_403_FORBIDDEN)
    """不允许修改超级管理员角色状态"""

    ROLE_HAS_USERS = ("ROLE.40102", HttpStatus.HTTP_400_BAD_REQUEST)
    """该角色已分配用户，无法删除"""

    ROLE_CREATE_FAILED = ("ROLE.40900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """角色创建失败"""

    ROLE_UPDATE_FAILED = ("ROLE.40901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """角色更新失败"""

    ROLE_DELETE_FAILED = ("ROLE.40902", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """角色删除失败"""

    ROLE_NO_PERMISSION = ("ROLE.40304", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该角色"""

    ROLE_AUTHORIZE_USERS_FAILED = ("ROLE.40903", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """批量授权用户失败"""

    ROLE_REVOKE_USERS_FAILED = ("ROLE.40904", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """取消用户角色授权失败"""

    ROLE_REVOKE_USERS_BATCH_FAILED = ("ROLE.40905", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """批量取消用户角色授权失败"""

    ROLE_UPDATE_DATA_SCOPE_FAILED = ("ROLE.40906", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """修改角色数据权限范围失败"""

    # ============================================================================
    # 功能权限 41xxx
    # ============================================================================

    FUNCTION_NOT_FOUND = ("FUNCTION.41001", HttpStatus.HTTP_404_NOT_FOUND)
    """功能不存在"""

    FUNCTION_ALREADY_EXISTS = ("FUNCTION.41200", HttpStatus.HTTP_409_CONFLICT)
    """功能已存在"""

    FUNCTION_NAME_ALREADY_EXISTS = ("FUNCTION.41201", HttpStatus.HTTP_409_CONFLICT)
    """功能名称已存在"""

    FUNCTION_EXTERNAL_LINK_INVALID = ("FUNCTION.41101", HttpStatus.HTTP_400_BAD_REQUEST)
    """外链地址格式无效"""

    FUNCTION_PARENT_IS_ITSELF = ("FUNCTION.41102", HttpStatus.HTTP_400_BAD_REQUEST)
    """上级功能不能选择自己"""

    FUNCTION_HAS_CHILDREN = ("FUNCTION.41103", HttpStatus.HTTP_400_BAD_REQUEST)
    """功能存在子功能，不允许删除"""

    FUNCTION_ASSIGNED_TO_ROLE = ("FUNCTION.41104", HttpStatus.HTTP_400_BAD_REQUEST)
    """功能已分配给角色，不允许删除"""

    FUNCTION_CREATE_FAILED = ("FUNCTION.41900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """功能创建失败"""

    FUNCTION_UPDATE_FAILED = ("FUNCTION.41901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """功能更新失败"""

    FUNCTION_DELETE_FAILED = ("FUNCTION.41902", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """功能删除失败"""

    # ============================================================================
    # 数据字典 50xxx
    # ============================================================================

    DICT_NOT_FOUND = ("DICT.50001", HttpStatus.HTTP_404_NOT_FOUND)
    """字典不存在"""

    DICT_ALREADY_EXISTS = ("DICT.50200", HttpStatus.HTTP_409_CONFLICT)
    """字典已存在"""

    DICT_TYPE_NOT_FOUND = ("DICT.50002", HttpStatus.HTTP_404_NOT_FOUND)
    """字典类型不存在"""

    DICT_TYPE_ALREADY_EXISTS = ("DICT.50201", HttpStatus.HTTP_409_CONFLICT)
    """字典类型已存在"""

    DICT_TYPE_HAS_DATA = ("DICT.50101", HttpStatus.HTTP_400_BAD_REQUEST)
    """字典类型已分配字典数据，不能删除"""

    DICT_TYPE_ID_LIST_EMPTY = ("DICT.50102", HttpStatus.HTTP_400_BAD_REQUEST)
    """字典类型ID列表为空"""

    DICT_DATA_ID_LIST_EMPTY = ("DICT.50103", HttpStatus.HTTP_400_BAD_REQUEST)
    """字典数据ID列表为空"""

    DICT_TYPE_CREATE_FAILED = ("DICT.50900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """字典类型创建失败"""

    DICT_TYPE_UPDATE_FAILED = ("DICT.50901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """字典类型更新失败"""

    DICT_TYPE_DELETE_FAILED = ("DICT.50902", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """字典类型删除失败"""

    DICT_DATA_CREATE_FAILED = ("DICT.50903", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """字典数据创建失败"""

    DICT_DATA_UPDATE_FAILED = ("DICT.50904", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """字典数据更新失败"""

    DICT_DATA_DELETE_FAILED = ("DICT.50905", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """字典数据删除失败"""

    # ============================================================================
    # 文件操作 60xxx
    # ============================================================================

    IMPORT_FAILED = ("FILE.60001", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """导入失败"""

    EXPORT_FAILED = ("FILE.60002", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """导出失败"""

    FILE_TYPE_NOT_SUPPORTED = ("FILE.60100", HttpStatus.HTTP_400_BAD_REQUEST)
    """不支持的文件类型"""

    # ============================================================================
    # 文件上传 70xxx
    # ============================================================================

    UPLOAD_FAILED = ("UPLOAD.70000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """文件上传失败"""

    UPLOAD_FILE_NOT_FOUND = ("UPLOAD.70001", HttpStatus.HTTP_404_NOT_FOUND)
    """文件不存在"""

    UPLOAD_FILE_TOO_LARGE = ("UPLOAD.70100", HttpStatus.HTTP_400_BAD_REQUEST)
    """文件大小超出限制"""

    UPLOAD_FILE_TYPE_NOT_ALLOWED = ("UPLOAD.70101", HttpStatus.HTTP_400_BAD_REQUEST)
    """不允许上传此类型的文件"""

    UPLOAD_FILENAME_EMPTY = ("UPLOAD.70102", HttpStatus.HTTP_400_BAD_REQUEST)
    """文件名不能为空"""

    UPLOAD_S3_CLIENT_NOT_INITIALIZED = ("UPLOAD.70900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """S3客户端未初始化"""

    UPLOAD_S3_CONFIG_NOT_INITIALIZED = ("UPLOAD.70901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """S3配置未初始化"""

    # ============================================================================
    # 文件下载 71xxx
    # ============================================================================

    DOWNLOAD_FAILED = ("DOWNLOAD.71000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """文件下载失败"""

    DOWNLOAD_FILE_NOT_FOUND = ("DOWNLOAD.71001", HttpStatus.HTTP_404_NOT_FOUND)
    """文件不存在"""

    DOWNLOAD_NO_PERMISSION = ("DOWNLOAD.71030", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该文件"""

    DOWNLOAD_NOT_ALLOWED = ("DOWNLOAD.71031", HttpStatus.HTTP_403_FORBIDDEN)
    """该文件不允许下载"""

    # ============================================================================
    # LLM/AI 相关 80xxx
    # ============================================================================

    LLM_CONNECTION_ERROR = ("LLM.80001", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """AI服务连接失败，请检查网络"""

    LLM_RATE_LIMIT_ERROR = ("LLM.80029", HttpStatus.HTTP_429_TOO_MANY_REQUESTS)
    """AI服务请求过于频繁，请稍后再试"""

    LLM_TOKEN_LIMIT_ERROR = ("LLM.80002", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """输入内容过长，请缩短后重试"""

    LLM_RESPONSE_ERROR = ("LLM.80000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """AI服务响应异常"""

    LLM_TIMEOUT_ERROR = ("LLM.80003", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """AI服务请求超时，请稍后再试"""

    # ============================================================================
    # 大纲图谱 SYLLABUS_GRAPH 85xxx
    # ============================================================================

    SYLLABUS_GRAPH_NODE_NOT_FOUND = ("SYLLABUS_GRAPH.85002", HttpStatus.HTTP_404_NOT_FOUND)
    """知识点节点不存在"""

    SYLLABUS_GRAPH_NODE_CREATE_FAILED = ("SYLLABUS_GRAPH.85003", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """知识点节点创建失败"""

    SYLLABUS_GRAPH_RELATIONSHIP_NOT_FOUND = ("SYLLABUS_GRAPH.85004", HttpStatus.HTTP_404_NOT_FOUND)
    """知识点关系不存在"""

    SYLLABUS_GRAPH_RELATIONSHIP_CREATE_FAILED = ("SYLLABUS_GRAPH.85005", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """知识点关系创建失败"""

    # ============================================================================
    # 日志审计 90xxx
    # ============================================================================

    LOG_UNEXPECTED_ERROR = ("LOG.90000", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """日志操作意外错误"""

    LOG_ID_LIST_EMPTY = ("LOG.90100", HttpStatus.HTTP_400_BAD_REQUEST)
    """日志ID列表为空"""

    LOG_CREATE_FAILED = ("LOG.90900", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """日志创建失败"""

    LOG_DELETE_FAILED = ("LOG.90901", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """日志删除失败"""

    LOG_CLEAR_FAILED = ("LOG.90902", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """日志清空失败"""

    # ============================================================================
    # 教育管理 100xxx-101xxx
    # ============================================================================

    # 学生管理 100xxx

    STUDENT_NOT_FOUND = ("EDU.100001", HttpStatus.HTTP_404_NOT_FOUND)
    """学生不存在"""

    STUDENT_ALREADY_EXISTS = ("EDU.100002", HttpStatus.HTTP_409_CONFLICT)
    """学生已存在"""

    STUDENT_NO_ALREADY_EXISTS = ("EDU.100010", HttpStatus.HTTP_409_CONFLICT)
    """学号已存在"""

    STUDENT_ID_LIST_EMPTY = ("EDU.100020", HttpStatus.HTTP_400_BAD_REQUEST)
    """学生ID列表为空"""

    STUDENT_CREATE_FAILED = ("EDU.100030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """学生新增失败"""

    STUDENT_UPDATE_FAILED = ("EDU.100031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """学生更新失败"""

    STUDENT_DELETE_FAILED = ("EDU.100032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """学生删除失败"""

    STUDENT_CHANGE_STATUS_FAILED = ("EDU.100033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """学生状态修改失败"""

    STUDENT_USER_NOT_FOUND = ("EDU.100040", HttpStatus.HTTP_404_NOT_FOUND)
    """关联的用户不存在"""

    STUDENT_NO_PERMISSION = ("EDU.100050", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该学生数据"""

    STUDENT_ALREADY_BOUND = ("EDU.100060", HttpStatus.HTTP_409_CONFLICT)
    """学生已绑定其他用户"""

    # 教师管理 101xxx

    TEACHER_NOT_FOUND = ("EDU.101001", HttpStatus.HTTP_404_NOT_FOUND)
    """教师不存在"""

    TEACHER_ALREADY_EXISTS = ("EDU.101002", HttpStatus.HTTP_409_CONFLICT)
    """教师已存在"""

    TEACHER_NO_ALREADY_EXISTS = ("EDU.101010", HttpStatus.HTTP_409_CONFLICT)
    """工号已存在"""

    TEACHER_ID_LIST_EMPTY = ("EDU.101020", HttpStatus.HTTP_400_BAD_REQUEST)
    """教师ID列表为空"""

    TEACHER_CREATE_FAILED = ("EDU.101030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """教师新增失败"""

    TEACHER_UPDATE_FAILED = ("EDU.101031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """教师更新失败"""

    TEACHER_DELETE_FAILED = ("EDU.101032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """教师删除失败"""

    TEACHER_CHANGE_STATUS_FAILED = ("EDU.101033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """教师状态修改失败"""

    TEACHER_USER_NOT_FOUND = ("EDU.101040", HttpStatus.HTTP_404_NOT_FOUND)
    """关联的用户不存在"""

    TEACHER_NO_PERMISSION = ("EDU.101050", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该教师数据"""

    TEACHER_MAX_STUDENT_COUNT_EXCEEDED = ("EDU.101060", HttpStatus.HTTP_400_BAD_REQUEST)
    """教师带教学生数量已达上限"""

    TEACHER_ALREADY_BOUND = ("EDU.101070", HttpStatus.HTTP_409_CONFLICT)
    """教师已绑定其他用户"""

    # 知识图谱管理 102xxx

    KNOWLEDGE_GRAPH_NOT_FOUND = ("EDU.102001", HttpStatus.HTTP_404_NOT_FOUND)
    """知识图谱不存在"""

    KNOWLEDGE_GRAPH_ALREADY_EXISTS = ("EDU.102002", HttpStatus.HTTP_409_CONFLICT)
    """知识图谱已存在"""

    KNOWLEDGE_GRAPH_NAME_ALREADY_EXISTS = ("EDU.102010", HttpStatus.HTTP_409_CONFLICT)
    """知识图谱名称已存在"""

    KNOWLEDGE_GRAPH_ID_LIST_EMPTY = ("EDU.102020", HttpStatus.HTTP_400_BAD_REQUEST)
    """知识图谱ID列表为空"""

    KNOWLEDGE_GRAPH_CREATE_FAILED = ("EDU.102030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """知识图谱新增失败"""

    KNOWLEDGE_GRAPH_UPDATE_FAILED = ("EDU.102031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """知识图谱更新失败"""

    KNOWLEDGE_GRAPH_DELETE_FAILED = ("EDU.102032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """知识图谱删除失败"""

    KNOWLEDGE_GRAPH_CHANGE_STATUS_FAILED = ("EDU.102033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """知识图谱状态修改失败"""

    KNOWLEDGE_GRAPH_BOOK_NOT_FOUND = ("EDU.102040", HttpStatus.HTTP_404_NOT_FOUND)
    """关联的书籍不存在"""

    KNOWLEDGE_GRAPH_NO_PERMISSION = ("EDU.102050", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该知识图谱"""

    # 课程管理 103xxx

    COURSE_NOT_FOUND = ("EDU.103001", HttpStatus.HTTP_404_NOT_FOUND)
    """课程不存在"""

    COURSE_ALREADY_EXISTS = ("EDU.103002", HttpStatus.HTTP_409_CONFLICT)
    """课程已存在"""

    COURSE_CODE_ALREADY_EXISTS = ("EDU.103010", HttpStatus.HTTP_409_CONFLICT)
    """课程代码已存在"""

    COURSE_NAME_ALREADY_EXISTS = ("EDU.103011", HttpStatus.HTTP_409_CONFLICT)
    """课程名称已存在"""

    COURSE_ID_LIST_EMPTY = ("EDU.103020", HttpStatus.HTTP_400_BAD_REQUEST)
    """课程ID列表为空"""

    COURSE_CREATE_FAILED = ("EDU.103030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程新增失败"""

    COURSE_UPDATE_FAILED = ("EDU.103031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程更新失败"""

    COURSE_DELETE_FAILED = ("EDU.103032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程删除失败"""

    COURSE_CHANGE_STATUS_FAILED = ("EDU.103033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程状态修改失败"""

    COURSE_NO_PERMISSION = ("EDU.103040", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该课程数据"""

    # 书籍管理 104xxx

    BOOK_NOT_FOUND = ("EDU.104001", HttpStatus.HTTP_404_NOT_FOUND)
    """书籍不存在"""

    BOOK_ALREADY_EXISTS = ("EDU.104002", HttpStatus.HTTP_409_CONFLICT)
    """书籍已存在"""

    BOOK_ISBN_ALREADY_EXISTS = ("EDU.104010", HttpStatus.HTTP_409_CONFLICT)
    """ISBN编号已存在"""

    BOOK_ID_LIST_EMPTY = ("EDU.104020", HttpStatus.HTTP_400_BAD_REQUEST)
    """书籍ID列表为空"""

    BOOK_CREATE_FAILED = ("EDU.104030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """书籍新增失败"""

    BOOK_UPDATE_FAILED = ("EDU.104031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """书籍更新失败"""

    BOOK_DELETE_FAILED = ("EDU.104032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """书籍删除失败"""

    BOOK_CHANGE_STATUS_FAILED = ("EDU.104033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """书籍状态修改失败"""

    # 选课管理 105xxx

    STUDENT_COURSE_NOT_FOUND = ("EDU.105001", HttpStatus.HTTP_404_NOT_FOUND)
    """选课记录不存在"""

    STUDENT_COURSE_ALREADY_EXISTS = ("EDU.105002", HttpStatus.HTTP_409_CONFLICT)
    """学生已选过该课程"""

    COURSE_NOT_AVAILABLE = ("EDU.105010", HttpStatus.HTTP_400_BAD_REQUEST)
    """课程不可选（停用或未公开）"""

    STUDENT_COURSE_ID_LIST_EMPTY = ("EDU.105020", HttpStatus.HTTP_400_BAD_REQUEST)
    """选课ID列表为空"""

    ENROLL_COURSE_FAILED = ("EDU.105030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """选课失败"""

    DROP_COURSE_FAILED = ("EDU.105031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """退课失败"""

    UPDATE_PROGRESS_FAILED = ("EDU.105032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """更新学习进度失败"""

    # ============================================================================
    # 定时任务管理 60xxx
    # ============================================================================

    # 任务资源 600xx

    JOB_NOT_FOUND = ("JOB.60001", HttpStatus.HTTP_404_NOT_FOUND)
    """定时任务不存在"""

    JOB_ALREADY_EXISTS = ("JOB.60002", HttpStatus.HTTP_409_CONFLICT)
    """定时任务已存在"""

    JOB_NAME_ALREADY_EXISTS = ("JOB.60003", HttpStatus.HTTP_409_CONFLICT)
    """任务名称已存在"""

    # 任务参数/配置 601xx

    JOB_ID_LIST_EMPTY = ("JOB.60100", HttpStatus.HTTP_400_BAD_REQUEST)
    """任务ID列表为空"""

    JOB_CRON_INVALID = ("JOB.60101", HttpStatus.HTTP_400_BAD_REQUEST)
    """Cron表达式无效"""

    JOB_TARGET_INVALID = ("JOB.60102", HttpStatus.HTTP_400_BAD_REQUEST)
    """调用目标非法"""

    JOB_CONFIG_INVALID = ("JOB.60103", HttpStatus.HTTP_400_BAD_REQUEST)
    """任务配置无效"""

    # 任务操作失败 602xx

    JOB_EXECUTE_FAILED = ("JOB.60200", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务执行失败"""

    JOB_CHANGE_STATUS_FAILED = ("JOB.60201", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务状态修改失败"""

    JOB_CREATE_FAILED = ("JOB.60202", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务创建失败"""

    JOB_UPDATE_FAILED = ("JOB.60203", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务更新失败"""

    JOB_DELETE_FAILED = ("JOB.60204", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务删除失败"""

    # 任务权限 603xx

    JOB_NO_PERMISSION = ("JOB.60300", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问该任务"""

    # 任务日志资源 604xx

    JOB_LOG_NOT_FOUND = ("JOB.60401", HttpStatus.HTTP_404_NOT_FOUND)
    """任务日志不存在"""

    JOB_LOG_ID_LIST_EMPTY = ("JOB.60400", HttpStatus.HTTP_400_BAD_REQUEST)
    """任务日志ID列表为空"""

    JOB_LOG_DELETE_FAILED = ("JOB.60402", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务日志删除失败"""

    JOB_LOG_CLEAR_FAILED = ("JOB.60403", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """任务日志清空失败"""

    # ============================================================================
    # 章节管理 106xxx
    # ============================================================================

    CHAPTER_NOT_FOUND = ("EDU.106001", HttpStatus.HTTP_404_NOT_FOUND)
    """章节不存在"""

    CHAPTER_NAME_ALREADY_EXISTS = ("EDU.106010", HttpStatus.HTTP_409_CONFLICT)
    """章节名称已存在（同一课程下）"""

    CHAPTER_ID_LIST_EMPTY = ("EDU.106020", HttpStatus.HTTP_400_BAD_REQUEST)
    """章节ID列表为空"""

    CHAPTER_CREATE_FAILED = ("EDU.106030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """章节新增失败"""

    CHAPTER_UPDATE_FAILED = ("EDU.106031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """章节更新失败"""

    CHAPTER_DELETE_FAILED = ("EDU.106032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """章节删除失败"""

    CHAPTER_CHANGE_STATUS_FAILED = ("EDU.106033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """章节状态修改失败"""

    CHAPTER_NO_PERMISSION = ("EDU.106040", HttpStatus.HTTP_403_FORBIDDEN)
    """无权操作该章节数据"""

    CHAPTER_HAS_CHILDREN = ("EDU.106050", HttpStatus.HTTP_400_BAD_REQUEST)
    """章节包含子章节，无法删除"""

    CHAPTER_LOOP = ("EDU.106051", HttpStatus.HTTP_400_BAD_REQUEST)
    """章节父级设置会形成循环"""

    # 章节资料管理 107xxx

    CHAPTER_RESOURCE_NOT_FOUND = ("EDU.107001", HttpStatus.HTTP_404_NOT_FOUND)
    """章节资料不存在"""

    CHAPTER_RESOURCE_ID_LIST_EMPTY = ("EDU.107020", HttpStatus.HTTP_400_BAD_REQUEST)
    """资料ID列表为空"""

    CHAPTER_RESOURCE_CREATE_FAILED = ("EDU.107030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """资料新增失败"""

    CHAPTER_RESOURCE_UPDATE_FAILED = ("EDU.107031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """资料更新失败"""

    CHAPTER_RESOURCE_DELETE_FAILED = ("EDU.107032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """资料删除失败"""

    CHAPTER_RESOURCE_CHANGE_STATUS_FAILED = ("EDU.107033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """资料状态修改失败"""

    # 课程练习管理 111xxx

    COURSE_EXERCISE_NOT_FOUND = ("EDU.111001", HttpStatus.HTTP_404_NOT_FOUND)
    """课程练习不存在"""

    COURSE_EXERCISE_ID_LIST_EMPTY = ("EDU.111020", HttpStatus.HTTP_400_BAD_REQUEST)
    """课程练习ID列表为空"""

    COURSE_EXERCISE_CREATE_FAILED = ("EDU.111030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程练习新增失败"""

    COURSE_EXERCISE_UPDATE_FAILED = ("EDU.111031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程练习更新失败"""

    COURSE_EXERCISE_DELETE_FAILED = ("EDU.111032", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程练习删除失败"""

    COURSE_EXERCISE_CHANGE_STATUS_FAILED = ("EDU.111033", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程练习状态修改失败"""

    COURSE_EXERCISE_BATCH_GENERATE_FAILED = ("EDU.111034", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """课程练习批量生成失败"""

    # 习题作答记录管理 112xxx

    EXERCISE_ATTEMPT_NOT_FOUND = ("EDU.112001", HttpStatus.HTTP_404_NOT_FOUND)
    """作答记录不存在"""

    EXERCISE_ATTEMPT_CREATE_FAILED = ("EDU.112030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """作答记录创建失败"""

    EXERCISE_ATTEMPT_EXERCISE_NOT_FOUND = ("EDU.112031", HttpStatus.HTTP_404_NOT_FOUND)
    """关联习题不存在"""

    # 聊天会话管理 108xxx

    CHAT_SESSION_NOT_FOUND = ("EDU.108001", HttpStatus.HTTP_404_NOT_FOUND)
    """聊天会话不存在"""

    CHAT_SESSION_ACCESS_DENIED = ("EDU.108002", HttpStatus.HTTP_403_FORBIDDEN)
    """无权访问聊天会话"""

    CHAT_SESSION_CREATE_FAILED = ("EDU.108030", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """聊天会话创建失败"""

    CHAT_MESSAGE_SEND_FAILED = ("EDU.108031", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """聊天消息发送失败"""

    CHAT_AGENT_NOT_INITIALIZED = ("EDU.108040", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """聊天服务未初始化"""

    # 外部服务 109xxx

    # GraphRAG 任务管理 110xxx

    GRAPHRAG_TASK_NOT_FOUND = ("EDU.110001", HttpStatus.HTTP_404_NOT_FOUND)
    """GraphRAG 任务不存在"""

    GRAPHRAG_TASK_ID_LIST_EMPTY = ("EDU.110020", HttpStatus.HTTP_400_BAD_REQUEST)
    """GraphRAG 任务ID列表为空"""

    GRAPHRAG_TASK_CANNOT_ENABLE = ("EDU.110030", HttpStatus.HTTP_400_BAD_REQUEST)
    """GraphRAG 任务无法启用（未构建成功）"""

    GRAPHRAG_TASK_CANNOT_RETRY = ("EDU.110040", HttpStatus.HTTP_400_BAD_REQUEST)
    """GraphRAG 任务无法重试（非失败/已取消状态）"""

    MINERU_API_ERROR = ("EDU.109001", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """MinerU API 调用失败"""

    GRAPHRAG_ERROR = ("EDU.109002", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """GraphRAG 操作失败"""

    # ============================================================================
    # 通用异步任务 61xxx
    # ============================================================================

    ASYNC_TASK_NOT_FOUND = ("ASYNC_TASK.61001", HttpStatus.HTTP_404_NOT_FOUND)
    """异步任务不存在"""

    ASYNC_TASK_CANNOT_CANCEL = ("ASYNC_TASK.61002", HttpStatus.HTTP_400_BAD_REQUEST)
    """异步任务无法取消（非 pending/processing 状态）"""

    ASYNC_TASK_CANNOT_RETRY = ("ASYNC_TASK.61003", HttpStatus.HTTP_400_BAD_REQUEST)
    """异步任务无法重试（非 failed/cancelled 状态）"""

    ASYNC_TASK_CREATE_FAILED = ("ASYNC_TASK.61004", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """异步任务创建失败"""

    ASYNC_TASK_UPDATE_FAILED = ("ASYNC_TASK.61005", HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR)
    """异步任务状态更新失败"""
