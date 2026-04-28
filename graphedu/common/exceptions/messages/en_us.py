"""English error messages"""

from graphedu.common.exceptions.services.codes import ErrorCode

# English message mapping
MESSAGES_EN_US: dict[ErrorCode, str] = {
    # ============================================================================
    # System common errors 1xxx, 9xxxx
    # ============================================================================
    ErrorCode.SYSTEM_ERROR: "System error, please try again later",
    ErrorCode.SYSTEM_BUSY: "System is busy, please try again later",
    ErrorCode.SYSTEM_TIMEOUT: "System timeout, please try again later",
    ErrorCode.SYSTEM_CONFIG_ERROR: "System configuration error",
    ErrorCode.SYSTEM_DATABASE_ERROR: "Database error, please try again later",
    ErrorCode.SYSTEM_NETWORK_ERROR: "Network error, please check your connection",
    # File related 9xxxx
    ErrorCode.FILE_NOT_FOUND: "File not found",
    ErrorCode.FILE_READ_ERROR: "File read failed",
    ErrorCode.FILE_WRITE_ERROR: "File write failed",
    ErrorCode.FILE_PARSE_ERROR: "File parse failed",
    ErrorCode.FILE_DELETE_ERROR: "File delete failed",
    # Config related
    ErrorCode.CONFIG_READ_ERROR: "Configuration file read failed",
    ErrorCode.CONFIG_VALIDATION_ERROR: "Configuration validation failed",
    # Validation related
    ErrorCode.VALIDATION_ERROR: "Data validation failed",
    ErrorCode.TYPE_CONVERSION_ERROR: "Type conversion failed",
    ErrorCode.JSON_PARSE_ERROR: "JSON parse failed",
    ErrorCode.JSON_VALIDATION_ERROR: "JSON validation failed",
    # Concurrency related
    ErrorCode.RATE_LIMIT_ERROR: "Too many requests, please try again later",
    ErrorCode.TIMEOUT_ERROR: "Operation timeout, please try again later",
    ErrorCode.LOCK_ERROR: "System is busy, please try again later",
    # ============================================================================
    # Authentication & Authorization 10xxx-13xxx
    # ============================================================================
    # Authentication base 10xxx
    ErrorCode.AUTH_FAILED: "Authentication failed",
    ErrorCode.AUTH_TOKEN_MISSING: "Authentication token missing",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Authentication token has expired",
    ErrorCode.AUTH_TOKEN_INVALID: "Authentication token is invalid",
    ErrorCode.AUTH_TOKEN_MALFORMED: "Authentication token format error",
    ErrorCode.AUTH_TOKEN_SIGNATURE_INVALID: "Authentication token signature is invalid",
    ErrorCode.AUTH_TOKEN_REFRESH_FAILED: "Authentication token refresh failed",
    ErrorCode.AUTH_NO_PERMISSION: "No permission for current operation",
    ErrorCode.AUTH_NO_INTERFACE_PERMISSION: "No interface access permission",
    ErrorCode.AUTH_NO_FUNCTION_PERMISSION: "No function access permission",
    # Login related 11xxx
    ErrorCode.LOGIN_FAILED: "Login failed",
    ErrorCode.LOGIN_USER_NOT_FOUND: "User not found",
    ErrorCode.LOGIN_PASSWORD_ERROR: "Incorrect username or password",
    ErrorCode.LOGIN_USERNAME_LOCKED: "Account is locked, please try another login method",
    ErrorCode.LOGIN_ACCOUNT_LOCKED: "Account is locked",
    ErrorCode.LOGIN_ACCOUNT_DISABLED: "Account is disabled",
    ErrorCode.LOGIN_ACCOUNT_EXPIRED: "Account has expired",
    ErrorCode.LOGIN_ACCOUNT_NOT_ACTIVATED: "Account is not activated",
    ErrorCode.LOGIN_ACCOUNT_PENDING_REVIEW: "Account is pending review",
    ErrorCode.LOGIN_ACCOUNT_REJECTED: "Account review was not approved",
    ErrorCode.LOGIN_IP_INVALID: "Login network environment is abnormal",
    ErrorCode.LOGIN_CREDENTIALS_EXPIRED: "User credentials have expired",
    ErrorCode.LOGIN_SESSION_EXPIRED: "Login session has expired",
    ErrorCode.LOGIN_SESSION_INVALID: "Login session is invalid",
    ErrorCode.LOGIN_CAPTCHA_ERROR: "Incorrect captcha",
    ErrorCode.LOGIN_CAPTCHA_EXPIRED: "Captcha has expired",
    ErrorCode.LOGIN_CAPTCHA_REQUIRED: "Please enter the captcha",
    ErrorCode.LOGIN_TIMEOUT: "Login timeout",
    ErrorCode.LOGIN_UNSUPPORTED: "Unsupported login method",
    ErrorCode.LOGIN_TOO_MANY_ATTEMPTS: (
        "Too many login attempts within {try_time_range}, please try again after {wait_time_range}"
    ),
    # Register related 12xxx
    ErrorCode.REGISTER_FAILED: "Registration failed",
    ErrorCode.REGISTER_FUNCTION_DISABLED: "Registration is closed, new user registration is not supported",
    ErrorCode.REGISTER_ILLEGAL_USERNAME: "Invalid username",
    ErrorCode.REGISTER_ILLEGAL_EMAIL: "Invalid email",
    ErrorCode.REGISTER_ILLEGAL_PHONE: "Invalid phone number",
    ErrorCode.REGISTER_ILLEGAL_PASSWORD: "Invalid password, please reset",
    ErrorCode.REGISTER_ILLEGAL_DOUBLE_PASSWORD: ("The two passwords entered do not match, please re-enter"),
    ErrorCode.REGISTER_USERNAME_ALREADY_EXISTS: ("User registration failed, username {username} already exists"),
    ErrorCode.REGISTER_PHONENUMBER_ALREADY_EXISTS: ("User registration failed, phone number already registered"),
    ErrorCode.REGISTER_EMAIL_ALREADY_EXISTS: ("User registration failed, email already registered"),
    # Password related
    ErrorCode.PASSWORD_TOO_WEAK: "Password is too weak",
    ErrorCode.PASSWORD_SAME_AS_OLD: "New password cannot be the same as the old password",
    ErrorCode.PASSWORD_INCORRECT: "Incorrect username or password",
    ErrorCode.PASSWORD_EXPIRED: "Password has expired, please change it",
    ErrorCode.PASSWORD_RESET_REQUIRED: "Password reset required",
    # ============================================================================
    # User management 20xxx-23xxx
    # ============================================================================
    # User base 20xxx
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.USER_DISABLED: "User is disabled",
    ErrorCode.USER_DEACTIVATED: "User is deactivated",
    ErrorCode.USER_ALREADY_EXISTS: "User already exists",
    ErrorCode.USER_EMAIL_ALREADY_EXISTS: "Email {email} already registered",
    ErrorCode.USER_PHONE_ALREADY_EXISTS: "Phone number {phone} already registered",
    # User operations 21xxx
    ErrorCode.USER_OPERATION_FAILED: "Operation failed, please try again later",
    ErrorCode.USER_RESET_PASSWORD_OLD_INCORRECT: ("Password reset failed, old password is incorrect"),
    ErrorCode.USER_RESET_PASSWORD_UNCHANGED: ("Password reset failed, new password cannot be the same as old password"),
    ErrorCode.USER_UPDATE_FAILED: "User information update failed",
    ErrorCode.USER_DELETE_FAILED: "User delete failed",
    ErrorCode.USER_DELETE_ADMIN: (
        'User with ID "{user_id}" is an administrator, deletion of super administrator is not allowed'
    ),
    # ============================================================================
    # Department management 30xxx
    # ============================================================================
    ErrorCode.DEPT_NOT_FOUND: "Department {dept_id} does not exist",
    ErrorCode.DEPT_ALREADY_EXISTS: "Department already exists",
    ErrorCode.DEPT_NAME_ALREADY_EXISTS: (
        "Failed to add department '{dept_name}', department name already exists under the same parent department"
    ),
    ErrorCode.DEPT_KEY_ALREADY_EXISTS: (
        "Failed to add department '{dept_name}', department code '{dept_key}' already exists"
    ),
    ErrorCode.DEPT_PARENT_NOT_FOUND: "Parent department does not exist",
    ErrorCode.DEPT_PARENT_DISABLED: (
        "Parent department '{parent_name}' is disabled, adding child departments is not allowed"
    ),
    ErrorCode.DEPT_PARENT_IS_ITSELF: ("Failed to modify department, parent department cannot be itself"),
    ErrorCode.DEPT_PARENT_CYCLE: ("Failed to modify department, cannot set parent department as its child department"),
    ErrorCode.DEPT_HAS_ACTIVE_CHILDREN: (
        "Failed to modify department '{dept_name}', it contains active child departments"
    ),
    ErrorCode.DEPT_HAS_CHILDREN: "Department {dept_name} has child departments, deletion is not allowed",
    ErrorCode.DEPT_HAS_USERS: "Department {dept_name} has associated users, deletion is not allowed",
    ErrorCode.DEPT_DELETE_FAILED: "Department delete failed",
    ErrorCode.DEPT_ID_LIST_EMPTY: "Department ID list is empty",
    ErrorCode.DEPT_NO_PERMISSION: "No permission to access department data",
    # ============================================================================
    # Role & Permission 40xxx
    # ============================================================================
    ErrorCode.ROLE_NOT_FOUND: "Role {role_id} does not exist",
    ErrorCode.ROLE_ALREADY_EXISTS: "Role already exists",
    ErrorCode.ROLE_NAME_ALREADY_EXISTS: "Failed to add role '{role_name}', role name already exists",
    ErrorCode.ROLE_KEY_ALREADY_EXISTS: "Failed to add role '{role_name}', role code '{role_key}' already exists",
    ErrorCode.ROLE_ID_LIST_EMPTY: "Role ID list is empty",
    ErrorCode.ROLE_MODIFY_ADMIN_FORBIDDEN: "Modifying super administrator role is not allowed",
    ErrorCode.ROLE_DELETE_ADMIN_FORBIDDEN: "Deleting super administrator role is not allowed",
    ErrorCode.ROLE_CHANGE_ADMIN_STATUS_FORBIDDEN: "Changing super administrator role status is not allowed",
    ErrorCode.ROLE_HAS_USERS: "Role '{role_name}' has been assigned to users, deletion is not allowed",
    ErrorCode.ROLE_DELETE_FAILED: "Role delete failed",
    ErrorCode.ROLE_NO_PERMISSION: "No permission to access role {role_id}",
    ErrorCode.ROLE_AUTHORIZE_USERS_FAILED: "Batch user authorization failed: {reason}",
    ErrorCode.ROLE_REVOKE_USERS_FAILED: "Cancel user role authorization failed: {reason}",
    ErrorCode.ROLE_REVOKE_USERS_BATCH_FAILED: ("Batch cancel user role authorization failed: {reason}"),
    ErrorCode.ROLE_UPDATE_DATA_SCOPE_FAILED: ("Failed to update role data permission scope: {reason}"),
    # ============================================================================
    # Function permission 41xxx
    # ============================================================================
    ErrorCode.FUNCTION_NOT_FOUND: "Function {function_id} does not exist",
    ErrorCode.FUNCTION_ALREADY_EXISTS: "Function already exists",
    ErrorCode.FUNCTION_NAME_ALREADY_EXISTS: ("Failed to add function '{function_name}', function name already exists"),
    ErrorCode.FUNCTION_EXTERNAL_LINK_INVALID: (
        "Failed to add function '{function_name}', external link must start with http(s)://"
    ),
    ErrorCode.FUNCTION_PARENT_IS_ITSELF: "Failed to modify function, parent function cannot be itself",
    ErrorCode.FUNCTION_HAS_CHILDREN: "Function '{function_name}' has child functions, deletion is not allowed",
    ErrorCode.FUNCTION_ASSIGNED_TO_ROLE: (
        "Function '{function_name}' has been assigned to roles, deletion is not allowed"
    ),
    # ============================================================================
    # Data dictionary 50xxx
    # ============================================================================
    ErrorCode.DICT_NOT_FOUND: "Dictionary {dict_code} does not exist",
    ErrorCode.DICT_ALREADY_EXISTS: "Dictionary already exists",
    ErrorCode.DICT_TYPE_NOT_FOUND: "Dictionary type {dict_type} does not exist",
    ErrorCode.DICT_TYPE_ALREADY_EXISTS: (
        "Failed to add dictionary '{dict_name}', dictionary type '{dict_type}' already exists"
    ),
    ErrorCode.DICT_TYPE_HAS_DATA: "Dictionary type '{dict_name}' has assigned dictionary data, cannot delete",
    ErrorCode.DICT_TYPE_ID_LIST_EMPTY: "Dictionary type ID list is empty",
    ErrorCode.DICT_DATA_ID_LIST_EMPTY: "Dictionary data ID list is empty",
    # ============================================================================
    # LLM/AI related 80xxx
    # ============================================================================
    ErrorCode.LLM_CONNECTION_ERROR: "AI service connection failed, please check network",
    ErrorCode.LLM_RATE_LIMIT_ERROR: "AI service requests too frequent, please try again later",
    ErrorCode.LLM_TOKEN_LIMIT_ERROR: "Input content is too long, please shorten and retry",
    ErrorCode.LLM_RESPONSE_ERROR: "AI service response error",
    ErrorCode.LLM_TIMEOUT_ERROR: "AI service request timeout, please try again later",
    # ============================================================================
    # Import/Export 60xxx
    # ============================================================================
    ErrorCode.IMPORT_FAILED: "Import failed",
    ErrorCode.EXPORT_FAILED: "Export failed",
    ErrorCode.FILE_TYPE_NOT_SUPPORTED: "Unsupported file type",
    # ============================================================================
    # Upload/Download 70xxx
    # ============================================================================
    ErrorCode.UPLOAD_FAILED: "File '{filename}' upload failed: {reason}",
    ErrorCode.UPLOAD_FILE_NOT_FOUND: "File {file_id} does not exist",
    ErrorCode.UPLOAD_FILE_TOO_LARGE: (
        "File '{filename}' size {file_size} bytes exceeds limit, maximum allowed {max_size} bytes"
    ),
    ErrorCode.UPLOAD_FILE_TYPE_NOT_ALLOWED: "This file type is not allowed to upload: {filename}",
    ErrorCode.UPLOAD_FILENAME_EMPTY: "Filename cannot be empty",
    ErrorCode.UPLOAD_S3_CLIENT_NOT_INITIALIZED: "S3 client is not initialized",
    ErrorCode.UPLOAD_S3_CONFIG_NOT_INITIALIZED: "S3 configuration is not initialized",
    ErrorCode.DOWNLOAD_FAILED: "File {file_id} download failed: {reason}",
    ErrorCode.DOWNLOAD_FILE_NOT_FOUND: "File {file_id} does not exist",
    ErrorCode.DOWNLOAD_NO_PERMISSION: "No permission to access file {file_id}",
    ErrorCode.DOWNLOAD_NOT_ALLOWED: "File '{filename}' is not allowed to download",
    # ============================================================================
    # Scheduled job management 60xxx
    # ============================================================================
    # Job resource 600xx
    ErrorCode.JOB_NOT_FOUND: "Scheduled job not found (Job ID: {job_id})",
    ErrorCode.JOB_ALREADY_EXISTS: "Scheduled job already exists",
    ErrorCode.JOB_NAME_ALREADY_EXISTS: "Job name '{job_name}' already exists, please use another name",
    # Job parameter/config 601xx
    ErrorCode.JOB_ID_LIST_EMPTY: "Job ID list cannot be empty",
    ErrorCode.JOB_CRON_INVALID: "Cron expression '{cron_expression}' format is invalid",
    ErrorCode.JOB_TARGET_INVALID: "Invoke target '{invoke_target}' is invalid, please check target format",
    ErrorCode.JOB_CONFIG_INVALID: "Job configuration is invalid: {reason}",
    # Job operation failed 602xx
    ErrorCode.JOB_EXECUTE_FAILED: "Job '{job_name}' execution failed: {reason}",
    ErrorCode.JOB_CHANGE_STATUS_FAILED: "Failed to change job status (Job ID: {job_id})",
    ErrorCode.JOB_CREATE_FAILED: "Failed to create job '{job_name}', please try again later",
    ErrorCode.JOB_UPDATE_FAILED: "Failed to update job (Job ID: {job_id})",
    ErrorCode.JOB_DELETE_FAILED: "Failed to delete job, please try again later",
    # Job permission 603xx
    ErrorCode.JOB_NO_PERMISSION: "No permission to access this job (Job ID: {job_id})",
    # Job log 604xx
    ErrorCode.JOB_LOG_NOT_FOUND: "Job log not found (Log ID: {job_log_id})",
    ErrorCode.JOB_LOG_ID_LIST_EMPTY: "Log ID list cannot be empty",
    ErrorCode.JOB_LOG_DELETE_FAILED: "Failed to delete job log, please try again later",
    ErrorCode.JOB_LOG_CLEAR_FAILED: "Failed to clear job logs, please try again later",
    # Chat session related
    ErrorCode.CHAT_SESSION_NOT_FOUND: "Session not found",
    ErrorCode.CHAT_SESSION_ACCESS_DENIED: "No permission to access this session",
    ErrorCode.CHAT_SESSION_CREATE_FAILED: "Failed to create session",
    ErrorCode.CHAT_MESSAGE_SEND_FAILED: "Failed to send message",
    ErrorCode.CHAT_AGENT_NOT_INITIALIZED: "Chat service is not initialized",
    ErrorCode.GRAPHRAG_TASK_NOT_FOUND: "GraphRAG task not found",
    ErrorCode.GRAPHRAG_TASK_ID_LIST_EMPTY: "GraphRAG task ID list cannot be empty",
}
