"""中文错误消息"""

from graphedu.common.exceptions.services.codes import ErrorCode

# 中文消息映射
MESSAGES_ZH_CN: dict[ErrorCode, str] = {
    # ============================================================================
    # 系统通用错误 1xxx, 9xxxx
    # ============================================================================
    ErrorCode.SYSTEM_ERROR: "系统错误，请稍后再试",
    ErrorCode.SYSTEM_BUSY: "系统繁忙，请稍后再试",
    ErrorCode.SYSTEM_TIMEOUT: "系统超时，请稍后再试",
    ErrorCode.SYSTEM_CONFIG_ERROR: "系统配置错误",
    ErrorCode.SYSTEM_DATABASE_ERROR: "数据库错误，请稍后再试",
    ErrorCode.SYSTEM_NETWORK_ERROR: "网络错误，请检查网络连接",
    # 文件相关 9xxxx
    ErrorCode.FILE_NOT_FOUND: "文件不存在",
    ErrorCode.FILE_READ_ERROR: "文件读取失败",
    ErrorCode.FILE_WRITE_ERROR: "文件写入失败",
    ErrorCode.FILE_PARSE_ERROR: "文件解析失败",
    ErrorCode.FILE_DELETE_ERROR: "文件删除失败",
    # 配置相关
    ErrorCode.CONFIG_READ_ERROR: "配置文件读取失败",
    ErrorCode.CONFIG_VALIDATION_ERROR: "配置验证失败",
    # 验证相关
    ErrorCode.VALIDATION_ERROR: "数据验证失败",
    ErrorCode.TYPE_CONVERSION_ERROR: "类型转换失败",
    ErrorCode.JSON_PARSE_ERROR: "JSON解析失败",
    ErrorCode.JSON_VALIDATION_ERROR: "JSON验证失败",
    # 并发相关
    ErrorCode.RATE_LIMIT_ERROR: "请求过于频繁，请稍后再试",
    ErrorCode.TIMEOUT_ERROR: "操作超时，请稍后再试",
    ErrorCode.LOCK_ERROR: "系统繁忙，请稍后再试",
    # ============================================================================
    # 认证授权 10xxx-13xxx
    # ============================================================================
    # 认证基础 10xxx
    ErrorCode.AUTH_FAILED: "认证失败",
    ErrorCode.AUTH_TOKEN_MISSING: "缺少认证令牌",
    ErrorCode.AUTH_TOKEN_EXPIRED: "认证令牌已过期",
    ErrorCode.AUTH_TOKEN_INVALID: "认证令牌无效",
    ErrorCode.AUTH_TOKEN_MALFORMED: "认证令牌格式错误",
    ErrorCode.AUTH_TOKEN_SIGNATURE_INVALID: "认证令牌签名无效",
    ErrorCode.AUTH_TOKEN_REFRESH_FAILED: "认证令牌刷新失败",
    ErrorCode.AUTH_NO_PERMISSION: "当前操作没有权限",
    ErrorCode.AUTH_NO_INTERFACE_PERMISSION: "当前用户没有接口访问权限",
    ErrorCode.AUTH_NO_FUNCTION_PERMISSION: "当前用户没有功能访问权限",
    # 登录相关 11xxx
    ErrorCode.LOGIN_FAILED: "登录失败",
    ErrorCode.LOGIN_USER_NOT_FOUND: "用户不存在",
    ErrorCode.LOGIN_PASSWORD_ERROR: "用户名或密码错误",
    ErrorCode.LOGIN_USERNAME_LOCKED: "账号已被锁定，请尝试使用其他登录方式",
    ErrorCode.LOGIN_ACCOUNT_LOCKED: "账号已被锁定",
    ErrorCode.LOGIN_ACCOUNT_DISABLED: "账号已被禁用",
    ErrorCode.LOGIN_ACCOUNT_EXPIRED: "账号已过期",
    ErrorCode.LOGIN_ACCOUNT_NOT_ACTIVATED: "账号未激活",
    ErrorCode.LOGIN_ACCOUNT_PENDING_REVIEW: "账号待审核",
    ErrorCode.LOGIN_ACCOUNT_REJECTED: "账号审核未通过",
    ErrorCode.LOGIN_IP_INVALID: "登录网络环境异常",
    ErrorCode.LOGIN_CREDENTIALS_EXPIRED: "用户凭证已过期",
    ErrorCode.LOGIN_SESSION_EXPIRED: "登录会话已过期",
    ErrorCode.LOGIN_SESSION_INVALID: "登录会话无效",
    ErrorCode.LOGIN_CAPTCHA_ERROR: "验证码错误",
    ErrorCode.LOGIN_CAPTCHA_EXPIRED: "验证码已过期",
    ErrorCode.LOGIN_CAPTCHA_REQUIRED: "请输入验证码",
    ErrorCode.LOGIN_TIMEOUT: "登录超时",
    ErrorCode.LOGIN_UNSUPPORTED: "不支持的登录方式",
    ErrorCode.LOGIN_TOO_MANY_ATTEMPTS: "{try_time_range}内登录尝试次数过多，请{wait_time_range}后再试",
    # 注册相关 12xxx
    ErrorCode.REGISTER_FAILED: "注册失败",
    ErrorCode.REGISTER_FUNCTION_DISABLED: "注册功能已关闭，暂不支持新用户注册",
    ErrorCode.REGISTER_ILLEGAL_USERNAME: "用户名不合法",
    ErrorCode.REGISTER_ILLEGAL_EMAIL: "邮箱不合法",
    ErrorCode.REGISTER_ILLEGAL_PHONE: "手机号不合法",
    ErrorCode.REGISTER_ILLEGAL_PASSWORD: "密码非法，请重新设置",
    ErrorCode.REGISTER_ILLEGAL_DOUBLE_PASSWORD: "两次输入的密码不一致，请重新输入",
    ErrorCode.REGISTER_USERNAME_ALREADY_EXISTS: "用户注册失败，用户名{username}已被注册",
    ErrorCode.REGISTER_PHONENUMBER_ALREADY_EXISTS: "用户注册失败，手机号已被注册",
    ErrorCode.REGISTER_EMAIL_ALREADY_EXISTS: "用户注册失败，邮箱已被注册",
    # 密码相关
    ErrorCode.PASSWORD_TOO_WEAK: "密码强度不足",
    ErrorCode.PASSWORD_SAME_AS_OLD: "新密码不能与旧密码相同",
    ErrorCode.PASSWORD_INCORRECT: "用户名或密码错误",
    ErrorCode.PASSWORD_EXPIRED: "密码已过期，请修改密码",
    ErrorCode.PASSWORD_RESET_REQUIRED: "需要重置密码",
    # ============================================================================
    # 用户管理 20xxx-23xxx
    # ============================================================================
    # 用户基础 20xxx
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.USER_DISABLED: "用户已被禁用",
    ErrorCode.USER_DEACTIVATED: "用户已被停用",
    ErrorCode.USER_ALREADY_EXISTS: "用户已存在",
    ErrorCode.USER_EMAIL_ALREADY_EXISTS: "邮箱{email}已被注册",
    ErrorCode.USER_PHONE_ALREADY_EXISTS: "手机号{phone}已被注册",
    # 用户操作 21xxx
    ErrorCode.USER_OPERATION_FAILED: "操作失败，请稍后重试",
    ErrorCode.USER_RESET_PASSWORD_OLD_INCORRECT: "重置密码失败，旧密码不正确",
    ErrorCode.USER_RESET_PASSWORD_UNCHANGED: "重置密码失败，新密码不能与旧密码相同",
    ErrorCode.USER_UPDATE_FAILED: "用户信息更新失败",
    ErrorCode.USER_DELETE_FAILED: "用户删除失败",
    ErrorCode.USER_DELETE_ADMIN: "ID 为：“{user_id}”的用户为管理员，不允许删除超级管理员用户",
    # ============================================================================
    # 部门管理 30xxx
    # ============================================================================
    ErrorCode.DEPT_NOT_FOUND: "部门{dept_id}不存在",
    ErrorCode.DEPT_ALREADY_EXISTS: "部门已存在",
    ErrorCode.DEPT_NAME_ALREADY_EXISTS: "新增部门'{dept_name}'失败，同一父部门下已存在该部门名称",
    ErrorCode.DEPT_KEY_ALREADY_EXISTS: "新增部门'{dept_name}'失败，部门编码'{dept_key}'已存在",
    ErrorCode.DEPT_PARENT_NOT_FOUND: "父部门不存在",
    ErrorCode.DEPT_PARENT_DISABLED: "父部门'{parent_name}'已停用，不允许新增子部门",
    ErrorCode.DEPT_PARENT_IS_ITSELF: "修改部门失败，上级部门不能是自己",
    ErrorCode.DEPT_PARENT_CYCLE: "修改部门失败，不能将父部门设为自己的子部门",
    ErrorCode.DEPT_HAS_ACTIVE_CHILDREN: "修改部门'{dept_name}'失败，该部门包含未停用的子部门",
    ErrorCode.DEPT_HAS_CHILDREN: "部门{dept_name}存在子部门，不允许删除",
    ErrorCode.DEPT_HAS_USERS: "部门{dept_name}存在关联用户，不允许删除",
    ErrorCode.DEPT_DELETE_FAILED: "部门删除失败",
    ErrorCode.DEPT_ID_LIST_EMPTY: "部门ID列表为空",
    ErrorCode.DEPT_NO_PERMISSION: "没有权限访问该部门数据",
    # ============================================================================
    # 角色权限 40xxx
    # ============================================================================
    ErrorCode.ROLE_NOT_FOUND: "角色{role_id}不存在",
    ErrorCode.ROLE_ALREADY_EXISTS: "角色已存在",
    ErrorCode.ROLE_NAME_ALREADY_EXISTS: "新增角色'{role_name}'失败，角色名称已存在",
    ErrorCode.ROLE_KEY_ALREADY_EXISTS: "新增角色'{role_name}'失败，角色标识'{role_key}'已存在",
    ErrorCode.ROLE_ID_LIST_EMPTY: "角色ID列表为空",
    ErrorCode.ROLE_MODIFY_ADMIN_FORBIDDEN: "不允许修改超级管理员角色",
    ErrorCode.ROLE_DELETE_ADMIN_FORBIDDEN: "不允许删除超级管理员角色",
    ErrorCode.ROLE_CHANGE_ADMIN_STATUS_FORBIDDEN: "不允许修改超级管理员角色状态",
    ErrorCode.ROLE_HAS_USERS: "角色'{role_name}'已分配给用户，不允许删除",
    ErrorCode.ROLE_DELETE_FAILED: "角色删除失败",
    ErrorCode.ROLE_NO_PERMISSION: "无权访问角色{role_id}",
    ErrorCode.ROLE_AUTHORIZE_USERS_FAILED: "批量授权用户失败: {reason}",
    ErrorCode.ROLE_REVOKE_USERS_FAILED: "取消用户角色授权失败: {reason}",
    ErrorCode.ROLE_REVOKE_USERS_BATCH_FAILED: "批量取消用户角色授权失败: {reason}",
    ErrorCode.ROLE_UPDATE_DATA_SCOPE_FAILED: "修改角色数据权限范围失败: {reason}",
    # ============================================================================
    # 功能权限 41xxx
    # ============================================================================
    ErrorCode.FUNCTION_NOT_FOUND: "功能{function_id}不存在",
    ErrorCode.FUNCTION_ALREADY_EXISTS: "功能已存在",
    ErrorCode.FUNCTION_NAME_ALREADY_EXISTS: "新增功能'{function_name}'失败，功能名称已存在",
    ErrorCode.FUNCTION_EXTERNAL_LINK_INVALID: "新增功能'{function_name}'失败，外链地址必须以http(s)://开头",
    ErrorCode.FUNCTION_PARENT_IS_ITSELF: "修改功能失败，上级功能不能选择自己",
    ErrorCode.FUNCTION_HAS_CHILDREN: "功能'{function_name}'存在子功能，不允许删除",
    ErrorCode.FUNCTION_ASSIGNED_TO_ROLE: "功能'{function_name}'已分配给角色，不允许删除",
    # ============================================================================
    # 数据字典 50xxx
    # ============================================================================
    ErrorCode.DICT_NOT_FOUND: "字典{dict_code}不存在",
    ErrorCode.DICT_ALREADY_EXISTS: "字典已存在",
    ErrorCode.DICT_TYPE_NOT_FOUND: "字典类型{dict_type}不存在",
    ErrorCode.DICT_TYPE_ALREADY_EXISTS: "新增字典'{dict_name}'失败，字典类型'{dict_type}'已存在",
    ErrorCode.DICT_TYPE_HAS_DATA: "字典类型'{dict_name}'已分配字典数据，不能删除",
    ErrorCode.DICT_TYPE_ID_LIST_EMPTY: "字典类型 ID 列表为空",
    ErrorCode.DICT_DATA_ID_LIST_EMPTY: "字典数据 ID 列表为空",
    # ============================================================================
    # 教育模块 10xxxx (学生/教师管理)
    # ============================================================================
    # 学生相关
    ErrorCode.STUDENT_NOT_FOUND: "学生不存在",
    ErrorCode.STUDENT_ALREADY_EXISTS: "学生已存在",
    ErrorCode.STUDENT_NO_ALREADY_EXISTS: "学号{student_no}已存在",
    ErrorCode.STUDENT_ID_LIST_EMPTY: "学生ID列表不能为空",
    ErrorCode.STUDENT_CREATE_FAILED: "学生新增失败",
    ErrorCode.STUDENT_UPDATE_FAILED: "学生更新失败",
    ErrorCode.STUDENT_DELETE_FAILED: "学生删除失败",
    ErrorCode.STUDENT_CHANGE_STATUS_FAILED: "学生状态修改失败",
    ErrorCode.STUDENT_USER_NOT_FOUND: "关联的用户不存在",
    ErrorCode.STUDENT_NO_PERMISSION: "无权访问该学生数据",
    # 教师相关
    ErrorCode.TEACHER_NOT_FOUND: "教师不存在",
    ErrorCode.TEACHER_ALREADY_EXISTS: "教师已存在",
    ErrorCode.TEACHER_NO_ALREADY_EXISTS: "工号{teacher_no}已存在",
    ErrorCode.TEACHER_ID_LIST_EMPTY: "教师ID列表不能为空",
    ErrorCode.TEACHER_CREATE_FAILED: "教师新增失败",
    ErrorCode.TEACHER_UPDATE_FAILED: "教师更新失败",
    ErrorCode.TEACHER_DELETE_FAILED: "教师删除失败",
    ErrorCode.TEACHER_CHANGE_STATUS_FAILED: "教师状态修改失败",
    ErrorCode.TEACHER_USER_NOT_FOUND: "关联的用户不存在",
    ErrorCode.TEACHER_NO_PERMISSION: "无权访问该教师数据",
    ErrorCode.TEACHER_MAX_STUDENT_COUNT_EXCEEDED: "教师带教学生数量已达上限",
    # 聊天会话相关
    ErrorCode.CHAT_SESSION_NOT_FOUND: "会话不存在",
    ErrorCode.CHAT_SESSION_ACCESS_DENIED: "无权访问该会话",
    ErrorCode.CHAT_SESSION_CREATE_FAILED: "会话创建失败",
    ErrorCode.CHAT_MESSAGE_SEND_FAILED: "消息发送失败",
    ErrorCode.CHAT_AGENT_NOT_INITIALIZED: "聊天服务未初始化",
    ErrorCode.GRAPHRAG_TASK_NOT_FOUND: "GraphRAG 任务不存在",
    ErrorCode.GRAPHRAG_TASK_ID_LIST_EMPTY: "GraphRAG 任务ID列表不能为空",
    # ============================================================================
    # 书籍管理 104xxx
    # ============================================================================
    ErrorCode.BOOK_NOT_FOUND: "书籍ID {book_id} 不存在",
    ErrorCode.BOOK_ALREADY_EXISTS: "书籍已存在",
    ErrorCode.BOOK_ISBN_ALREADY_EXISTS: "ISBN编号 {isbn} 已存在",
    ErrorCode.BOOK_ID_LIST_EMPTY: "书籍ID列表不能为空",
    ErrorCode.BOOK_CREATE_FAILED: "创建书籍 '{title}' 失败",
    ErrorCode.BOOK_UPDATE_FAILED: "更新书籍ID {book_id} 失败",
    ErrorCode.BOOK_DELETE_FAILED: "删除书籍失败",
    ErrorCode.BOOK_CHANGE_STATUS_FAILED: "修改书籍ID {book_id} 状态失败",
    # ============================================================================
    # LLM/AI 相关 80xxx
    # ============================================================================
    ErrorCode.LLM_CONNECTION_ERROR: "AI服务连接失败，请检查网络",
    ErrorCode.LLM_RATE_LIMIT_ERROR: "AI服务请求过于频繁，请稍后再试",
    ErrorCode.LLM_TOKEN_LIMIT_ERROR: "输入内容过长，请缩短后重试",
    ErrorCode.LLM_RESPONSE_ERROR: "AI服务响应异常",
    ErrorCode.LLM_TIMEOUT_ERROR: "AI服务请求超时，请稍后再试",
    # ============================================================================
    # 导入导出 60xxx
    # ============================================================================
    ErrorCode.IMPORT_FAILED: "导入失败",
    ErrorCode.EXPORT_FAILED: "导出失败",
    ErrorCode.FILE_TYPE_NOT_SUPPORTED: "不支持的文件类型",
    # ============================================================================
    # 上传下载 70xxx
    # ============================================================================
    ErrorCode.UPLOAD_FAILED: "文件'{filename}'上传失败: {reason}",
    ErrorCode.UPLOAD_FILE_NOT_FOUND: "文件{file_id}不存在",
    ErrorCode.UPLOAD_FILE_TOO_LARGE: "文件'{filename}'大小{file_size}字节超出限制，最大允许{max_size}字节",
    ErrorCode.UPLOAD_FILE_TYPE_NOT_ALLOWED: "不允许上传此类型的文件: {filename}",
    ErrorCode.UPLOAD_FILENAME_EMPTY: "文件名不能为空",
    ErrorCode.UPLOAD_S3_CLIENT_NOT_INITIALIZED: "S3客户端未初始化",
    ErrorCode.UPLOAD_S3_CONFIG_NOT_INITIALIZED: "S3配置未初始化",
    ErrorCode.DOWNLOAD_FAILED: "文件{file_id}下载失败: {reason}",
    ErrorCode.DOWNLOAD_FILE_NOT_FOUND: "文件{file_id}不存在",
    ErrorCode.DOWNLOAD_NO_PERMISSION: "无权访问文件{file_id}",
    ErrorCode.DOWNLOAD_NOT_ALLOWED: "文件'{filename}'不允许下载",
    # ============================================================================
    # 知识图谱管理 102xxx
    # ============================================================================
    ErrorCode.KNOWLEDGE_GRAPH_NOT_FOUND: "知识图谱ID {graph_id} 不存在",
    ErrorCode.KNOWLEDGE_GRAPH_ALREADY_EXISTS: "知识图谱已存在",
    ErrorCode.KNOWLEDGE_GRAPH_NAME_ALREADY_EXISTS: "知识图谱名称 '{graph_name}' 已存在",
    ErrorCode.KNOWLEDGE_GRAPH_ID_LIST_EMPTY: "知识图谱ID列表不能为空",
    ErrorCode.KNOWLEDGE_GRAPH_CREATE_FAILED: "知识图谱新增失败",
    ErrorCode.KNOWLEDGE_GRAPH_UPDATE_FAILED: "知识图谱更新失败",
    ErrorCode.KNOWLEDGE_GRAPH_DELETE_FAILED: "知识图谱删除失败",
    ErrorCode.KNOWLEDGE_GRAPH_CHANGE_STATUS_FAILED: "知识图谱状态修改失败",
    ErrorCode.KNOWLEDGE_GRAPH_BOOK_NOT_FOUND: "关联的书籍ID {book_id} 不存在",
    ErrorCode.KNOWLEDGE_GRAPH_NO_PERMISSION: "无权访问该知识图谱数据",
    # ============================================================================
    # 定时任务管理 60xxx
    # ============================================================================
    ErrorCode.JOB_NOT_FOUND: "定时任务不存在（任务ID：{job_id}）",
    ErrorCode.JOB_ALREADY_EXISTS: "定时任务已存在",
    ErrorCode.JOB_NAME_ALREADY_EXISTS: "任务名称'{job_name}'已存在，请使用其他名称",
    ErrorCode.JOB_ID_LIST_EMPTY: "任务ID列表不能为空",
    ErrorCode.JOB_CRON_INVALID: "Cron表达式'{cron_expression}'格式无效",
    ErrorCode.JOB_TARGET_INVALID: "调用目标'{invoke_target}'非法，请检查目标格式",
    ErrorCode.JOB_CONFIG_INVALID: "任务配置无效：{reason}",
    ErrorCode.JOB_EXECUTE_FAILED: "任务'{job_name}'执行失败：{reason}",
    ErrorCode.JOB_CHANGE_STATUS_FAILED: "修改任务状态失败（任务ID：{job_id}）",
    ErrorCode.JOB_CREATE_FAILED: "任务'{job_name}'创建失败，请稍后重试",
    ErrorCode.JOB_UPDATE_FAILED: "任务更新失败（任务ID：{job_id}）",
    ErrorCode.JOB_DELETE_FAILED: "任务删除失败，请稍后重试",
    ErrorCode.JOB_NO_PERMISSION: "无权访问该任务（任务ID：{job_id}）",
    ErrorCode.JOB_LOG_NOT_FOUND: "任务日志不存在（日志ID：{job_log_id}）",
    ErrorCode.JOB_LOG_ID_LIST_EMPTY: "日志ID列表不能为空",
    ErrorCode.JOB_LOG_DELETE_FAILED: "任务日志删除失败，请稍后重试",
    ErrorCode.JOB_LOG_CLEAR_FAILED: "任务日志清空失败，请稍后重试",
}
