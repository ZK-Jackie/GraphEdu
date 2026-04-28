# GraphEdu 异常处理体系文档

## 概述

GraphEdu 采用了一套完整的分层异常处理体系，提供统一的错误码、多语言错误消息和全局异常处理机制。

## 目录结构

```
graphedu/common/exceptions/
├── __init__.py           # 统一导出所有异常
├── base.py               # 基础异常类 AppException
├── handler.py            # FastAPI 全局异常处理器
├── config.py             # 配置相关异常
├── resource.py           # 资源层异常（数据库、缓存、存储等）
├── utils.py              # 工具类异常（文件、并发、LLM等）
├── services/             # API层业务异常
│   ├── base.py           # ServiceException/ServiceWarning 基类
│   ├── codes.py          # 错误码枚举定义
│   └── system/           # 系统模块异常
│       ├── auth.py       # 认证授权异常
│       ├── user.py       # 用户管理异常
│       ├── dept.py       # 部门管理异常
│       ├── role.py       # 角色管理异常
│       ├── dict.py       # 数据字典异常
│       ├── job.py        # 定时任务异常
│       ├── upload.py     # 文件上传下载异常
│       └── function.py   # 功能权限异常
└── messages/             # 多语言错误消息
    ├── __init__.py       # 消息获取接口
    ├── zh_cn.py          # 中文错误消息
    └── en_us.py          # 英文错误消息
```

## 核心设计

### 1. 分层错误码

错误码采用 `模块.编号` 格式，便于快速定位错误来源和类型。

#### 错误码分配表

| 模块  | 范围          | 说明         |
|-----|-------------|------------|
| SYS  | 1xxx, 9xxx  | 系统通用错误     |
| AUTH | 10xxx-13xxx | 认证授权       |
|     | 10xxx       | 认证基础       |
|     | 11xxx       | 登录相关       |
|     | 12xxx       | 注册相关       |
|     | 13xxx       | 密码相关       |
| USER | 20xxx-21xxx | 用户管理       |
| DEPT | 30xxx       | 部门管理       |
| ROLE | 40xxx       | 角色权限       |
| FUNCTION | 41xxx   | 功能权限       |
| DICT | 50xxx       | 数据字典       |
| FILE | 60xxx       | 文件操作       |
| UPLOAD | 70xxx     | 文件上传       |
| DOWNLOAD | 71xxx   | 文件下载       |
| LLM  | 80xxx       | LLM/AI 相关  |
| LOG  | 90xxx       | 日志审计       |
| JOB  | 60xxx       | 定时任务管理     |
| EDU  | 100xxx-105xxx | 教育管理    |

#### 错误码枚举类

```python
class ErrorCode(StrEnum):
    """分层错误码定义：模块.编号"""

    # 每个错误码包含错误码字符串和默认HTTP状态码
    AUTH_TOKEN_EXPIRED = ("AUTH.10002", 401)
    LOGIN_PASSWORD_ERROR = ("AUTH.11002", 401)
    USER_NOT_FOUND = ("USER.20001", 404)

    @property
    def module(self) -> str:
        """获取模块名"""
        return self.value.split(".")[0]

    @property
    def code_num(self) -> int:
        """获取错误码数字部分"""
        return int(self.value.split(".")[1])
```

### 2. 异常类型层次

```
Exception
├── AppException                    # 应用基础异常
│   ├── ConfigurationException      # 配置异常
│   ├── ResourceException          # 资源层异常
│   │   ├── DatabaseException      # 数据库异常
│   │   ├── CacheException         # 缓存异常
│   │   ├── StorageException       # 存储异常
│   │   ├── GraphDatabaseException # 图数据库异常
│   │   └── HTTPException          # HTTP客户端异常
│   └── UtilsException             # 工具类异常
│       ├── FileException          # 文件操作异常
│       ├── ConcurrentException    # 并发异常
│       ├── LLMException           # LLM异常
│       └── ...
└── ServiceException               # API层业务异常
    ├── LoginException             # 登录异常
    ├── RegisterException          # 注册异常
    ├── UserException              # 用户异常
    └── ...
```

### 3. 异常类型对比

| 类型                | 用途                | 继承关系          | 错误码 | i18n  |
|-------------------|-------------------|-------------|-----|------|
| ServiceException   | API层业务异常        | ServiceException | ✅   | ✅   |
| ServiceWarning     | 非中断警告信息          | ServiceWarning | ❌   | ❌   |
| AppException       | 应用基础异常           | AppException   | ❌   | ❌   |
| ResourceException  | 资源层异常（数据库、缓存等）   | ResourceException | ❌   | ❌   |
| UtilsException     | 工具类异常（文件、LLM等）  | UtilsException  | ❌   | ❌   |

**选择建议：**
- **ServiceException**: 用于需要返回给客户端的业务逻辑错误
- **ServiceWarning**: 用于需要告知客户端但不中断流程的信息
- **AppException/ResourceException**: 用于内部系统错误（配置、资源连接失败等）
- **UtilsException**: 用于工具函数中的错误

## 使用指南

### 1. 抛出业务异常（ServiceException）

#### 基础用法

```python
from graphedu.common.exceptions import (
    RegisterUsernameExistsException,
    ErrorCode
)

# 方式1：使用预定义异常类（推荐）
raise RegisterUsernameExistsException(username="zhangsan")

# 方式2：使用通用 ServiceException
from graphedu.common.exceptions.services.base import ServiceException
raise ServiceException(
    error_code=ErrorCode.USER_NOT_FOUND.value,
    message="用户不存在",  # 可选，不提供则从i18n获取
)
```

#### 带参数的错误消息

```python
# 异常类支持通过 kwargs 传递参数进行消息格式化
raise RegisterUsernameExistsException(username="zhangsan")

# 对应的错误消息模板（zh_cn.py）:
# "用户注册失败，用户名{username}已被注册"

# 最终输出: "用户注册失败，用户名zhangsan已被注册"
```

### 2. 抛出警告（ServiceWarning）

```python
from graphedu.common.exceptions.services.base import ServiceWarning

raise ServiceWarning(
    message="数据已存在，跳过创建",
    data={"existing_id": 123}
)
```

### 3. 抛出资源层异常

```python
from graphedu.common.exceptions import (
    DatabaseConnectionException,
    CacheOperationException
)

# 数据库连接失败
raise DatabaseConnectionException(
    db_type="PostgreSQL",
    reason="connection timeout"
)

# 缓存操作失败
raise CacheOperationException(
    operation="set",
    key="user:123",
    reason="Redis connection lost"
)
```

### 4. 自定义业务异常

#### 步骤1：在 codes.py 中定义错误码

```python
class ErrorCode(StrEnum):
    # 在对应模块范围内添加新错误码
    CUSTOM_OPERATION_FAILED = ("CUSTOM.10001", 500)
```

#### 步骤2：在 messages/zh_cn.py 中添加中文消息

```python
MESSAGES_ZH_CN = {
    ErrorCode.CUSTOM_OPERATION_FAILED: "自定义操作失败: {reason}",
}
```

#### 步骤3：创建异常类

```python
# 在对应模块文件中（如 services/system/custom.py）
from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode

class CustomException(ServiceException):
    """自定义操作失败"""

    def __init__(self, reason: str, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.CUSTOM_OPERATION_FAILED.value,
            message=message,
            reason=reason,
            **kwargs
        )
```

## 全局异常处理

### 处理器注册

在 `graphedu/api/service.py` 中注册全局异常处理器：

```python
from fastapi import FastAPI
from graphedu.common.exceptions.handler import handle_exception

app = FastAPI()
handle_exception(app)  # 注册所有异常处理器
```

### 异常处理顺序

异常处理器按以下顺序匹配：

1. **ServiceWarning** - 警告信息（HTTP 200，带 warning 标识）
2. **HTTPException** - FastAPI 内置 HTTP 异常
3. **RequestValidationError** - 请求参数验证失败
4. **ServiceException** - 业务异常（带错误码和 i18n 消息）
5. **AppException** - 应用级异常
6. **ValidationError** - Pydantic 验证异常
7. **Exception** - 未捕获的通用异常（HTTP 500）

### 响应格式

#### ServiceException 响应

```json
{
  "code": 409,
  "errorCode": "AUTH.12201",
  "msg": "用户注册失败，用户名zhangsan已被注册",
  "data": {},
  "time": "2025-01-15T12:00:00Z"
}
```

#### ServiceWarning 响应

```json
{
  "code": 200,
  "msg": "数据已存在，跳过创建",
  "data": {"existing_id": 123},
  "time": "2025-01-15T12:00:00Z",
  "warning": true
}
```

#### 通用错误响应

```json
{
  "code": 500,
  "msg": "系统错误，请稍后再试",
  "data": {},
  "time": "2025-01-15T12:00:00Z"
}
```

## 国际化支持

### 语言解析

通过 `Accept-Language` 请求头自动检测语言：

```python
def parse_accept_language(accept_language: str | None) -> str:
    """解析Accept-Language请求头

    Returns:
        zh_CN 或 en_US（默认 zh_CN）
    """
```

### 添加新语言

1. 创建 `messages/<locale>.py` 文件
2. 定义错误消息字典：

```python
# messages/en_us.py
MESSAGES_EN_US = {
    ErrorCode.AUTH_TOKEN_EXPIRED: "Authentication token has expired",
    ErrorCode.USER_NOT_FOUND: "User not found",
    # ...
}
```

3. 在 `messages/__init__.py` 中添加语言分支

## 错误码索引

### 系统通用错误 (SYS)

| 错误码          | HTTP | 说明            |
|---------------|------|---------------|
| SYS.1000      | 500  | 系统错误          |
| SYS.1001      | 500  | 系统繁忙          |
| SYS.1002      | 500  | 系统超时          |
| SYS.1003      | 500  | 系统配置错误        |
| SYS.1004      | 500  | 数据库错误         |
| SYS.1005      | 500  | 网络错误          |
| SYS.9001      | 404  | 文件不存在         |
| SYS.9101      | 500  | 配置文件读取失败      |
| SYS.9201      | 500  | 数据验证失败        |
| SYS.9301      | 429  | 请求过于频繁        |

### 认证授权 (AUTH)

#### 认证基础 (10xxx)

| 错误码                | HTTP | 说明         |
|---------------------|------|------------|
| AUTH.10000          | 500  | 认证失败       |
| AUTH.10001          | 401  | 缺少认证令牌     |
| AUTH.10002          | 401  | 认证令牌已过期    |
| AUTH.10003          | 401  | 认证令牌无效     |
| AUTH.10004          | 401  | 认证令牌格式错误   |
| AUTH.10005          | 401  | 认证令牌签名无效   |
| AUTH.10006          | 401  | 认证令牌刷新失败   |
| AUTH.10020          | 403  | 当前操作没有权限   |
| AUTH.10021          | 403  | 没有接口访问权限   |
| AUTH.10022          | 403  | 没有功能访问权限   |

#### 登录相关 (11xxx)

| 错误码             | HTTP | 说明           |
|------------------|------|--------------|
| AUTH.11000       | 401  | 登录失败         |
| AUTH.11001       | 401  | 用户不存在        |
| AUTH.11002       | 401  | 用户名或密码错误     |
| AUTH.11004       | 401  | 用户凭证已过期      |
| AUTH.11005       | 401  | 登录会话已过期      |
| AUTH.11006       | 401  | 登录会话无效       |
| AUTH.11007       | 401  | 登录会话无效       |
| AUTH.11010       | 400  | 验证码错误        |
| AUTH.11011       | 400  | 验证码已过期       |
| AUTH.11012       | 400  | 请输入验证码       |
| AUTH.11013       | 408  | 登录超时         |
| AUTH.11029       | 429  | 登录尝试次数过多     |
| AUTH.11031       | 403  | 账号已被锁定       |
| AUTH.11032       | 403  | 账号已被锁定       |
| AUTH.11033       | 403  | 账号已被禁用       |
| AUTH.11034       | 403  | 账号未激活        |
| AUTH.11035       | 403  | 账号待审核        |
| AUTH.11036       | 403  | 账号审核未通过      |
| AUTH.11037       | 403  | 登录网络环境异常     |

#### 注册相关 (12xxx)

| 错误码                    | HTTP | 说明              |
|-------------------------|------|-----------------|
| AUTH.12000              | 500  | 注册失败            |
| AUTH.12030              | 403  | 注册功能已关闭         |
| AUTH.12101              | 400  | 用户名不合法          |
| AUTH.12102              | 400  | 邮箱不合法           |
| AUTH.12103              | 400  | 手机号不合法          |
| AUTH.12104              | 400  | 密码非法            |
| AUTH.12105              | 400  | 两次输入的密码不一致      |
| AUTH.12201              | 409  | 用户名已被注册         |
| AUTH.12202              | 409  | 手机号已被注册         |
| AUTH.12203              | 409  | 邮箱已被注册          |

#### 密码相关 (13xxx)

| 错误码              | HTTP | 说明          |
|-------------------|------|-------------|
| AUTH.13010        | 400  | 密码强度不足      |
| AUTH.13011        | 400  | 新密码不能与旧密码相同 |
| AUTH.13012        | 400  | 用户名或密码错误    |
| AUTH.13030        | 403  | 密码已过期      |
| AUTH.13031        | 403  | 需要重置密码     |

### 用户管理 (USER)

| 错误码                 | HTTP | 说明            |
|----------------------|------|---------------|
| USER.20001           | 404  | 用户不存在         |
| USER.20030           | 403  | 用户已被禁用        |
| USER.20031           | 403  | 用户已被停用        |
| USER.20200           | 409  | 用户已存在         |
| USER.20201           | 409  | 邮箱已被注册        |
| USER.20202           | 409  | 手机号已被注册       |
| USER.21000           | 400  | 操作失败          |
| USER.21030           | 403  | 不允许删除超级管理员用户  |
| USER.21031           | 403  | 不允许删除当前登录用户   |
| USER.21101           | 400  | 旧密码不正确        |
| USER.21102           | 400  | 新密码不能与旧密码相同   |
| USER.21900           | 500  | 用户信息更新失败      |
| USER.21901           | 500  | 用户删除失败        |

### 部门管理 (DEPT)

| 错误码                   | HTTP | 说明             |
|------------------------|------|----------------|
| DEPT.30001             | 404  | 部门不存在          |
| DEPT.30002             | 404  | 父部门不存在         |
| DEPT.30101             | 400  | 父部门已停用         |
| DEPT.30102             | 400  | 上级部门不能是自己     |
| DEPT.30103             | 400  | 不能将父部门设为自己的子部门 |
| DEPT.30104             | 400  | 部门包含未停用的子部门    |
| DEPT.30105             | 400  | 该部门存在子部门       |
| DEPT.30106             | 400  | 该部门存在用户        |
| DEPT.30107             | 400  | 部门ID列表为空       |
| DEPT.30108             | 403  | 没有权限访问该部门数据    |
| DEPT.30200             | 409  | 部门已存在          |
| DEPT.30201             | 409  | 部门名称已存在        |
| DEPT.30202             | 409  | 部门编码已存在        |
| DEPT.30900             | 500  | 部门创建失败         |
| DEPT.30901             | 500  | 部门更新失败         |
| DEPT.30902             | 500  | 部门删除失败         |

### 角色权限 (ROLE)

| 错误码                      | HTTP | 说明              |
|---------------------------|------|-----------------|
| ROLE.40001                | 404  | 角色不存在           |
| ROLE.40101                | 400  | 角色ID列表为空        |
| ROLE.40102                | 400  | 该角色已分配用户        |
| ROLE.40200                | 409  | 角色已存在           |
| ROLE.40201                | 409  | 角色名称已存在         |
| ROLE.40202                | 409  | 角色标识已存在         |
| ROLE.40301                | 403  | 不允许修改超级管理员角色    |
| ROLE.40302                | 403  | 不允许删除超级管理员角色    |
| ROLE.40303                | 403  | 不允许修改超级管理员角色状态  |
| ROLE.40304                | 403  | 无权访问该角色         |
| ROLE.40900                | 500  | 角色创建失败          |
| ROLE.40901                | 500  | 角色更新失败          |
| ROLE.40902                | 500  | 角色删除失败          |
| ROLE.40903                | 500  | 批量授权用户失败        |
| ROLE.40904                | 500  | 取消用户角色授权失败      |
| ROLE.40905                | 500  | 批量取消用户角色授权失败   |
| ROLE.40906                | 500  | 修改角色数据权限范围失败    |

### 数据字典 (DICT)

| 错误码                       | HTTP | 说明            |
|----------------------------|------|---------------|
| DICT.50001                 | 404  | 字典不存在         |
| DICT.50002                 | 404  | 字典类型不存在       |
| DICT.50101                 | 400  | 字典类型已分配字典数据   |
| DICT.50102                 | 400  | 字典类型ID列表为空    |
| DICT.50103                 | 400  | 字典数据ID列表为空    |
| DICT.50200                 | 409  | 字典已存在         |
| DICT.50201                 | 409  | 字典类型已存在       |
| DICT.50900                 | 500  | 字典类型创建失败      |
| DICT.50901                 | 500  | 字典类型更新失败      |
| DICT.50902                 | 500  | 字典类型删除失败      |
| DICT.50903                 | 500  | 字典数据创建失败      |
| DICT.50904                 | 500  | 字典数据更新失败      |
| DICT.50905                 | 500  | 字典数据删除失败      |

### 文件上传下载 (UPLOAD/DOWNLOAD)

| 错误码                             | HTTP | 说明           |
|----------------------------------|------|--------------|
| UPLOAD.70000                     | 500  | 文件上传失败       |
| UPLOAD.70001                     | 404  | 文件不存在        |
| UPLOAD.70100                     | 400  | 文件大小超出限制     |
| UPLOAD.70101                     | 400  | 不允许上传此类型的文件  |
| UPLOAD.70102                     | 400  | 文件名不能为空      |
| UPLOAD.70900                     | 500  | S3客户端未初始化    |
| UPLOAD.70901                     | 500  | S3配置未初始化     |
| DOWNLOAD.71000                   | 500  | 文件下载失败       |
| DOWNLOAD.71001                   | 404  | 文件不存在        |
| DOWNLOAD.71030                   | 403  | 无权访问该文件      |
| DOWNLOAD.71031                   | 403  | 该文件不允许下载     |

### 定时任务 (JOB)

| 错误码                       | HTTP | 说明          |
|----------------------------|------|-------------|
| JOB.60001                  | 404  | 定时任务不存在     |
| JOB.60002                  | 409  | 定时任务已存在     |
| JOB.60003                  | 409  | 任务名称已存在     |
| JOB.60100                  | 400  | 任务ID列表为空    |
| JOB.60101                  | 400  | Cron表达式无效    |
| JOB.60102                  | 400  | 调用目标非法      |
| JOB.60103                  | 400  | 任务配置无效      |
| JOB.60200                  | 500  | 任务执行失败      |
| JOB.60201                  | 500  | 任务状态修改失败    |
| JOB.60202                  | 500  | 任务创建失败      |
| JOB.60203                  | 500  | 任务更新失败      |
| JOB.60204                  | 500  | 任务删除失败      |
| JOB.60300                  | 403  | 无权访问该任务     |
| JOB.60400                  | 400  | 任务日志ID列表为空  |
| JOB.60401                  | 404  | 任务日志不存在     |
| JOB.60402                  | 500  | 任务日志删除失败    |
| JOB.60403                  | 500  | 任务日志清空失败    |

### 教育管理 (EDU)

#### 学生管理 (100xxx)

| 错误码                        | HTTP | 说明         |
|-----------------------------|------|------------|
| EDU.100001                  | 404  | 学生不存在      |
| EDU.100002                  | 409  | 学生已存在      |
| EDU.100010                  | 409  | 学号已存在      |
| EDU.100020                  | 400  | 学生ID列表为空  |
| EDU.100030                  | 500  | 学生新增失败     |
| EDU.100031                  | 500  | 学生更新失败     |
| EDU.100032                  | 500  | 学生删除失败     |
| EDU.100033                  | 500  | 学生状态修改失败   |
| EDU.100040                  | 404  | 关联的用户不存在   |
| EDU.100050                  | 403  | 无权访问该学生数据 |

#### 教师管理 (101xxx)

| 错误码                        | HTTP | 说明           |
|-----------------------------|------|--------------|
| EDU.101001                  | 404  | 教师不存在        |
| EDU.101002                  | 409  | 教师已存在        |
| EDU.101010                  | 409  | 工号已存在        |
| EDU.101020                  | 400  | 教师ID列表为空    |
| EDU.101030                  | 500  | 教师新增失败       |
| EDU.101031                  | 500  | 教师更新失败       |
| EDU.101032                  | 500  | 教师删除失败       |
| EDU.101033                  | 500  | 教师状态修改失败     |
| EDU.101040                  | 404  | 关联的用户不存在     |
| EDU.101050                  | 403  | 无权访问该教师数据    |
| EDU.101060                  | 400  | 教师带教学生数量已达上限 |

#### 知识图谱管理 (102xxx)

| 错误码                          | HTTP | 说明          |
|-------------------------------|------|-------------|
| EDU.102001                    | 404  | 知识图谱不存在     |
| EDU.102002                    | 409  | 知识图谱已存在     |
| EDU.102010                    | 409  | 知识图谱名称已存在   |
| EDU.102020                    | 400  | 知识图谱ID列表为空 |
| EDU.102030                    | 500  | 知识图谱新增失败    |
| EDU.102031                    | 500  | 知识图谱更新失败    |
| EDU.102032                    | 500  | 知识图谱删除失败    |
| EDU.102033                    | 500  | 知识图谱状态修改失败  |
| EDU.102040                    | 404  | 关联的书籍不存在    |
| EDU.102050                    | 403  | 无权访问该知识图谱  |

#### 课程管理 (103xxx)

| 错误码                        | HTTP | 说明         |
|-----------------------------|------|------------|
| EDU.103001                  | 404  | 课程不存在      |
| EDU.103002                  | 409  | 课程已存在      |
| EDU.103010                  | 409  | 课程代码已存在    |
| EDU.103011                  | 409  | 课程名称已存在    |
| EDU.103020                  | 400  | 课程ID列表为空  |
| EDU.103030                  | 500  | 课程新增失败     |
| EDU.103031                  | 500  | 课程更新失败     |
| EDU.103032                  | 500  | 课程删除失败     |
| EDU.103033                  | 500  | 课程状态修改失败   |
| EDU.103040                  | 403  | 无权访问该课程数据 |

#### 书籍管理 (104xxx)

| 错误码                        | HTTP | 说明         |
|-----------------------------|------|------------|
| EDU.104001                  | 404  | 书籍不存在      |
| EDU.104002                  | 409  | 书籍已存在      |
| EDU.104010                  | 409  | ISBN编号已存在  |
| EDU.104020                  | 400  | 书籍ID列表为空  |
| EDU.104030                  | 500  | 书籍新增失败     |
| EDU.104031                  | 500  | 书籍更新失败     |
| EDU.104032                  | 500  | 书籍删除失败     |
| EDU.104033                  | 500  | 书籍状态修改失败   |

#### 选课管理 (105xxx)

| 错误码                          | HTTP | 说明          |
|-------------------------------|------|-------------|
| EDU.105001                    | 404  | 选课记录不存在     |
| EDU.105002                    | 409  | 学生已选过该课程    |
| EDU.105010                    | 400  | 课程不可选       |
| EDU.105020                    | 400  | 选课ID列表为空   |
| EDU.105030                    | 500  | 选课失败        |
| EDU.105031                    | 500  | 退课失败        |
| EDU.105032                    | 500  | 更新学习进度失败    |

## 最佳实践

### 1. 选择合适的异常类型

```python
# ✅ 正确：API 层使用 ServiceException
@router.post("/users")
async def create_user(user_data: UserDTO):
    if await user_exists(user_data.username):
        raise RegisterUsernameExistsException(username=user_data.username)

# ✅ 正确：资源层使用 ResourceException
async def get_db_connection():
    try:
        return await asyncpg.connect(...)
    except Exception as e:
        raise DatabaseConnectionException(db_type="PostgreSQL", reason=str(e))

# ❌ 错误：不要在 Service 层使用通用 Exception
def process_user(user_id: int):
    if not user_id:
        raise Exception("Invalid user id")  # 应使用 ServiceException
```

### 2. 提供有用的错误信息

```python
# ✅ 正确：包含具体的错误上下文
raise UserNotFoundException(user_id=123)

# ✅ 正确：提供原因和上下文
raise DatabaseConnectionException(
    db_type="PostgreSQL",
    reason="Connection timeout after 30s"
)

# ❌ 错误：过于模糊
raise Exception("Database error")
```

### 3. 保持异常链

```python
# ✅ 正确：使用 raise ... from ... 保留原始异常
try:
    await user.save()
except DatabaseError as e:
    raise UserUpdateFailed(reason="Database error") from e
```

### 4. 日志记录

全局异常处理器已包含日志记录，无需在异常抛出时额外记录：

```python
# ✅ 正确：只抛出异常，让全局处理器处理
raise UserNotFoundException(user_id=123)

# ❌ 不必要：不要手动记录业务异常
logger.error(f"User {user_id} not found")  # 全局处理器会记录
raise UserNotFoundException(user_id=123)
```

### 5. 客户端错误处理建议

前端应根据 `errorCode` 进行错误处理，而非依赖 `msg`：

```typescript
// ✅ 正确：基于错误码处理
if (response.errorCode === 'AUTH.10002') {
  // Token 过期，刷新 Token
  await refreshToken();
} else if (response.errorCode === 'AUTH.11002') {
  // 密码错误，提示用户
  showMessage('用户名或密码错误');
}

// ❌ 错误：依赖消息文本匹配
if (response.msg.includes('expired')) {
  // 文本可能变化，且不支持国际化
}
```

## 扩展指南

### 添加新的业务模块异常

1. **定义错误码**（在 `services/codes.py`）：

```python
class ErrorCode(StrEnum):
    # 新模块使用新的编号范围
    NEW_MODULE_NOT_FOUND = ("NEWMOD.10001", 404)
    NEW_MODULE_CREATE_FAILED = ("NEWMOD.10900", 500)
```

2. **添加错误消息**（在 `messages/zh_cn.py` 和 `messages/en_us.py`）：

```python
# zh_cn.py
MESSAGES_ZH_CN = {
    ErrorCode.NEW_MODULE_NOT_FOUND: "新模块资源不存在",
    ErrorCode.NEW_MODULE_CREATE_FAILED: "新模块创建失败: {reason}",
}

# en_us.py
MESSAGES_EN_US = {
    ErrorCode.NEW_MODULE_NOT_FOUND: "New module resource not found",
    ErrorCode.NEW_MODULE_CREATE_FAILED: "New module creation failed: {reason}",
}
```

3. **创建异常类**（新建 `services/new_module.py`）：

```python
from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode

class NewModuleException(ServiceException):
    """新模块异常基类"""

    def __init__(self, error_code: str, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)

class NewModuleNotFoundException(NewModuleException):
    """新模块资源不存在"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.NEW_MODULE_NOT_FOUND.value,
            message=message,
            **kwargs
        )

class NewModuleCreateFailedException(NewModuleException):
    """新模块创建失败"""

    def __init__(self, reason: str, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.NEW_MODULE_CREATE_FAILED.value,
            message=message,
            reason=reason,
            **kwargs
        )
```

4. **导出异常**（在 `__init__.py` 中）：

```python
from .services.new_module import (
    NewModuleException,
    NewModuleNotFoundException,
    NewModuleCreateFailedException,
)

__all__ = [
    # ...
    "NewModuleException",
    "NewModuleNotFoundException",
    "NewModuleCreateFailedException",
]
```

## 相关文件

- `graphedu/api/service.py` - FastAPI 应用配置和异常处理器注册
- `graphedu/common/exceptions/handler.py` - 全局异常处理器实现
- `graphedu/common/exceptions/services/codes.py` - 完整错误码定义
- `graphedu/common/exceptions/messages/` - 多语言错误消息
