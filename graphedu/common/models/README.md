# GraphEdu 数据模型设计文档

> 本文档详细说明了 GraphEdu 项目中数据模型的设计理念、分类规则和命名约定。

## 目录

- [模型分层架构](#模型分层架构)
- [命名规范](#命名规范)
- [ORM 模型设计](#orm-模型设计)
- [DTO 模型设计](#dto-模型设计)
- [VO 模型设计](#vo-模型设计)
- [BO 模型设计](#bo-模型设计)
- [常量定义](#常量定义)
- [字段类型规范](#字段类型规范)
- [索引设计规范](#索引设计规范)

---

## 模型分层架构

GraphEdu 采用分层模型设计，将数据模型分为五层，每层承担不同的职责：

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (API)                          │
│                    Request → Response                        │
├─────────────────────────────────────────────────────────────┤
│  DTO (数据传输对象)          │  VO (视图对象)                │
│  - API 请求参数验证          │  - API 响应数据               │
│  - 输入数据结构              │  - 输出数据序列化             │
│  - 命名后缀: DTO             │  - 命名后缀: VO               │
├─────────────────────────────────────────────────────────────┤
│                    业务层 (Service)                          │
│                    BO (业务对象)                             │
│  - 跨层数据封装               │  - 业务逻辑处理载体           │
│  - 命名后缀: 无 (业务含义)     │  - 命名后缀: 无 (业务含义)    │
├─────────────────────────────────────────────────────────────┤
│                    数据访问层 (Mapper)                       │
│                    ORM (对象关系映射)                        │
│  - 数据库表映射               │  - SQLAlchemy 实体            │
│  - 命名后缀: 无 (表名)         │  - 命名后缀: 无 (表名)        │
├─────────────────────────────────────────────────────────────┤
│                    数据库层 (Database)                       │
│                    PostgreSQL Tables                        │
└─────────────────────────────────────────────────────────────┘
```

### 各层职责说明

| 层级 | 名称 | 职责 | 位置 |
|-----|------|-----|------|
| **DTO** | Data Transfer Object | API 请求参数验证，定义输入数据结构和验证规则 | `common/models/dto/` |
| **VO** | View Object | API 响应数据封装，配置序列化规则 | `common/models/vo/` |
| **BO** | Business Object | 业务数据封装，跨层数据传递的中间对象 | `common/models/bo/` |
| **ORM** | Object-Relational Mapping | 数据库表映射，供数据访问层使用 | `common/models/orm/` |
| **Constants** | 常量 | 系统运行所需的各种常量定义 | `common/models/constants.py` |

---

## 命名规范

### 文件命名

| 类型 | 规范 | 示例 |
|-----|------|------|
| DTO 文件 | `{domain}.py` | `user.py`, `auth.py`, `education.py` |
| VO 文件 | `{domain}.py` | `user.py`, `role.py`, `dept.py` |
| BO 文件 | `{domain}.py` | `user.py`, `cli.py` |
| ORM 文件 | `{module}.py` | `system.py`, `education.py`, `generator.py` |

### 类命名

| 类型 | 规范 | 示例 |
|-----|------|------|
| DTO | `{操作}{实体}DTO` | `UserCreateDTO`, `UserQueryDTO`, `UserLoginByUsernameDTO` |
| VO | `{粒度}{实体}VO` | `UserDetailVO`, `UserListVO`, `UserInfoVO` |
| BO | `{业务含义}` | `UserDetail`, `CurrentUser` |
| ORM | `{表前缀}{实体名}` | `SysUser`, `EduStudent`, `GenTable` |

### 字段命名

- **Python 端**: 使用 `snake_case` 命名（如 `user_name`, `create_time`）
- **API 响应**: 自动转换为 `camelCase`（通过 `alias_generator=to_camel`）
- **数据库**: 使用 `snake_case` 命名

---

## ORM 模型设计

### 基类设计

所有 ORM 模型都继承自 SQLAlchemy 2.0 的声明式基类：

```python
# 系统模块基类
from graphedu.common.models.orm.base import Base

class SystemBase(DeclarativeBase):
    """系统模块 SQLAlchemy 2.0 声明式基类"""
    pass

# 教育模块基类
class EduBase(DeclarativeBase):
    """教育模块 SQLAlchemy 2.0 声明式基类"""
    pass

# 代码生成器模块基类
class GeneratorBase(DeclarativeBase):
    """代码生成器模块 SQLAlchemy 2.0 声明式基类"""
    pass
```

### 完整示例

```python
from datetime import datetime
from sqlalchemy import CHAR, TIMESTAMP, BigInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

class SysUser(SystemBase):
    """用户基础信息表"""

    __tablename__ = "sys_user"

    # 主键（必需）
    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="用户ID"
    )

    # 业务字段
    user_name: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, comment="登录账号"
    )
    nick_name: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="用户昵称"
    )

    # 状态字段（使用字符类型，便于扩展）
    status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="0",
        comment="用户状态，对照 sys_data_status（0正常 1停用 2已删除）"
    )

    # 审计字段（标准四字段）
    create_by: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="创建者"
    )
    create_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="创建时间"
    )
    update_by: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="更新者"
    )
    update_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp(), comment="更新时间"
    )

    # 索引和表注释
    __table_args__ = (
        Index("idx_sys_user_user_name", "user_name"),
        Index("idx_sys_user_status", "status"),
        {"comment": "用户基础信息表"},
    )
```

### 设计规则

#### 1. 字段类型选择

| 数据类型 | SQLAlchemy 类型 | 说明 |
|---------|----------------|------|
| 主键 ID | `BigInteger` | 64 位整数，自增 |
| 字符编码 | `String(n)` | 变长字符串，指定长度 |
| 状态标识 | `CHAR(1)` | 单字符，便于扩展 |
| 金额/数值 | `Numeric(m, d)` | 精确数值类型 |
| 时间戳 | `TIMESTAMP` | 日期时间 |
| JSON 数据 | `JSONB` | PostgreSQL JSON 类型 |
| 文本内容 | `Text` | 长文本 |

#### 2. 主键设计

```python
# 自增主键（推荐）
user_id: Mapped[int] = mapped_column(
    BigInteger, primary_key=True, autoincrement=True
)

# 联合主键（关联表）
user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
```

#### 3. 默认值设计

```python
# 时间戳默认当前时间
create_time: Mapped[datetime] = mapped_column(
    TIMESTAMP, default=func.current_timestamp()
)

# 字符串默认空字符串
email: Mapped[str] = mapped_column(String(64), default="")

# 状态默认正常
status: Mapped[str] = mapped_column(CHAR(1), default="0")
```

#### 4. 可空字段

```python
# 可选字段
avatar_file_id: Mapped[int | None] = mapped_column(
    BigInteger, nullable=True
)

# 必填字段
user_name: Mapped[str] = mapped_column(
    String(32), nullable=False
)
```

#### 5. 索引设计

```python
__table_args__ = (
    # 单列索引
    Index("idx_{table}_{column}", "column_name"),
    # 联合索引
    Index("idx_{table}_{col1}_{col2}", "col1", "col2"),
    # 唯一索引（在字段上定义 unique=True）
    # 表注释
    {"comment": "表注释"},
)
```

---

## DTO 模型设计

### 基类设计

所有 DTO 继承自 `DTO` 基类，自动获得以下特性：

```python
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class DTO(BaseModel):
    """DTO 基类

    提供：
    - alias_generator: snake_case → camelCase 转换
    - validate_by_alias: 同时验证别名和原始字段名
    - validate_by_name: 允许使用字段名验证
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True
    )
```

### 基础 DTO

```python
from graphedu.common.models.dto.base import DTO, PageQuery

# 分页查询基类
class UserQueryDTO(PageQuery):
    """用户查询 DTO"""
    user_name: str | None = Field(default=None, description="用户账号")
    status: Literal["0", "1"] | None = Field(default=None, description="状态")

# 创建 DTO
class UserCreateDTO(DTO):
    """创建用户 DTO"""
    user_name: str = Field(description="用户账号")
    nick_name: str = Field(description="用户昵称")
    password: str = Field(description="用户密码")
    email: str | None = Field(default=None, description="用户邮箱")
```

### DTO 设计规范

#### 1. 命名规范

| 场景 | 命名格式 | 示例 |
|-----|---------|------|
| 查询列表 | `{Entity}QueryDTO` | `UserQueryDTO`, `CourseQueryDTO` |
| 创建记录 | `{Entity}CreateDTO` | `UserCreateDTO`, `DeptCreateDTO` |
| 更新记录 | `{Entity}UpdateDTO` | `UserUpdateDTO`, `RoleUpdateDTO` |
| 特定操作 | `{Verb}{Entity}DTO` | `UserLoginByUsernameDTO` |

#### 2. 字段验证

```python
from pydantic import Field, field_validator
import re

class UserCreateDTO(DTO):
    """创建用户 DTO"""
    user_name: str = Field(
        min_length=3, max_length=32,
        description="用户账号（3-32字符）"
    )
    password: str = Field(
        min_length=6, max_length=128,
        description="用户密码（6-128字符）"
    )
    status: Literal["0", "1"] = Field(
        default="0",
        description="状态（0正常 1停用）"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码合法性"""
        pattern = r"""^[^<>"'|\\]+$"""
        if not re.match(pattern, v):
            raise ValueError("密码不能包含非法字符")
        return v
```

#### 3. 嵌套 DTO

```python
class UserRoleUpdateDTO(DTO):
    """更新用户角色 DTO"""
    user_id: int = Field(description="用户ID")
    role_ids: list[int] = Field(description="角色ID列表")
```

#### 4. 分页 DTO

```python
class UserQueryDTO(PageQuery):
    """继承分页基类，自动获得 page 和 size 字段"""
    # page: int | None = 1
    # size: int | None = 10
    user_name: str | None = Field(default=None, description="用户账号")
```

---

## VO 模型设计

### 基类设计

所有 VO 继承自 `BaseVO` 基类：

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class BaseVO(BaseModel):
    """VO 基类

    提供：
    - from_attributes=True: 支持从 ORM 对象创建
    - alias_generator=to_camel: 自动生成驼峰命名别名
    - populate_by_name=True: 允许使用字段名或别名
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True
    )
```

### VO 示例

```python
from pydantic import Field
from graphedu.common.models.vo.base import VO


class UserDetailVO(VO):
    """用户详细信息 VO"""
    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    status: str = Field(description="帐号状态（0正常 1停用）")

    # 关联信息
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")


class UserListVO(VO):
    """用户列表项 VO"""
    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    status: str = Field(description="帐号状态")
    # 关联的部门信息
    dept_name: str | None = Field(default=None, description="主部门名称")
```

### VO 设计规范

#### 1. 粒度划分

| 粒度 | 命名格式 | 用途 |
|-----|---------|------|
| 简要信息 | `{Entity}InfoVO` | 列表展示、下拉选择 |
| 列表项 | `{Entity}ListVO` | 列表页单条记录 |
| 详情信息 | `{Entity}DetailVO` | 详情页完整信息 |
| 组合对象 | `{Entity}ProfileVO` | 多对象组合展示 |

#### 2. 敏感字段处理

```python
class UserDetailVO(BaseVO):
    """用户详细信息 VO - 不包含密码"""
    user_id: int
    user_name: str
    # password: str  # VO 中不包含敏感字段
    email: str | None = None
```

#### 3. 关联字段

```python
class UserProfileVO(BaseVO):
    """用户个人信息 VO - 包含关联对象"""
    user: UserDetailVO = Field(description="用户详细信息")
    roles: list[RoleDetailVO] = Field(default_factory=list, description="角色列表")
    depts: list[DeptDetailVO] = Field(default_factory=list, description="部门列表")
```

---

## BO 模型设计

BO（Business Object）用于业务层的数据封装，通常包含 ORM 对象的聚合。

### 设计示例

```python
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from pydantic.alias_generators import to_camel
from graphedu.common.models.orm import SysDept, SysRole, SysUser

class UserDetail(BaseModel):
    """用户详细信息模型（业务对象）"""

    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
    depts: list[SysDept] = Field(default_factory=list, description="部门信息 ORM 对象列表")
    roles: list[SysRole] = Field(default_factory=list, description="角色信息 ORM 对象列表")
    user: SysUser | None = Field(default=None, description="用户信息 ORM 对象")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # 允许 SQLAlchemy 类型
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )

    @field_serializer("depts", "roles", "user", mode="plain")
    def sql_model_dump(self, values):
        """将 SQLAlchemy ORM 对象序列化为字典"""
        # 序列化逻辑...
```

### BO 使用场景

1. **跨层传递**: Service 层到 Controller 层的数据传递
2. **数据聚合**: 将多个 ORM 对象组合成一个业务对象
3. **缓存对象**: Redis 缓存的业务数据结构

---

## 常量定义

### 常量组织结构

```python
# 项目前缀
project_prefix = "graphedu:"

class CommonConstants:
    """通用常量"""
    HTTP = "http://"
    HTTPS = "https://"
    WWW = "www."

class RedisConstants:
    """Redis 键常量"""
    class Auth:
        """认证相关"""
        TOKEN_KEY = project_prefix + "auth:token"
        USER_CACHE_KEY = project_prefix + "auth:user_cache"

    class UserInfo:
        """用户信息缓存"""
        USER_INFO_KEY = project_prefix + "user:info"

class SystemConstants:
    """系统状态常量"""
    class Status:
        """数据状态"""
        NORMAL = "0"      # 正常
        DISABLED = "1"    # 停用
        DELETED = "2"     # 已删除

    class UserType:
        """用户类型"""
        STUDENT = "1"     # 学生
        TEACHER = "2"     # 教师
        ADMIN = "3"       # 管理员
        OTHER = "4"       # 其他
```

### 常量使用示例

```python
from graphedu.common.models.constants import SystemConstants

# 使用状态常量
status = SystemConstants.Status.NORMAL

# 使用用户类型常量
user_type = SystemConstants.UserType.STUDENT
```

---

## 字段类型规范

### 状态字段

| 字段名 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `status` | `CHAR(1)` | `"0"` | 数据状态（0正常 1停用 2已删除） |
| `is_enabled` / `enabled` | `CHAR(1)` | `"Y"` | 是否启用（Y是 N否） |
| `is_visible` / `visible` | `CHAR(1)` | `"Y"` | 是否可见（Y是 N否） |

### ID 字段

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `*_id` | `BigInteger` | 主键 ID |
| `user_id` | `BigInteger` | 用户 ID（外键） |
| `dept_id` | `BigInteger` | 部门 ID（外键） |
| `role_id` | `BigInteger` | 角色 ID（外键） |

### 审计字段（标准四字段）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `create_by` | `BigInteger | None` | 创建者 ID |
| `create_time` | `TIMESTAMP` | 创建时间（自动填充） |
| `update_by` | `BigInteger | None` | 更新者 ID |
| `update_time` | `TIMESTAMP` | 更新时间（需手动更新） |

---

## 索引设计规范

### 索引命名

```python
# 格式: idx_{表名}_{字段名}
Index("idx_sys_user_user_name", "user_name")
Index("idx_sys_user_status", "status")

# 联合索引: idx_{表名}_{字段1}_{字段2}
Index("idx_edu_student_faculty_major", "faculty", "major")
```

### 索引设计原则

1. **频繁查询字段**: 添加单列索引
2. **唯一约束字段**: 添加唯一索引（在字段上设置 `unique=True`）
3. **多字段组合查询**: 添加联合索引
4. **外键字段**: 建议添加索引

### 索引示例

```python
__table_args__ = (
    # 查询条件索引
    Index("idx_sys_user_status", "status"),
    Index("idx_sys_user_user_type", "user_type"),

    # 唯一索引（在字段定义）
    # user_name: Mapped[str] = mapped_column(unique=True)

    # 联合索引
    Index("idx_edu_student_faculty_major", "faculty", "major"),
    Index("idx_edu_chapter_progress_student_chapter", "student_id", "chapter_id"),
)
```

---

## 最佳实践

### 1. 模型分离

- **DTO**: 定义请求参数，关注输入验证
- **VO**: 定义响应数据，关注输出格式
- **ORM**: 定义数据库映射，关注存储结构

### 2. 字段注释

所有字段都应添加 `comment` 参数，便于生成数据库文档：

```python
user_name: Mapped[str] = mapped_column(
    String(32), nullable=False, comment="登录账号"
)
```

### 3. 类型注解

使用 `Mapped` 类型注解，获得更好的 IDE 支持：

```python
# 推荐
user_name: Mapped[str] = mapped_column(String(32))

# 不推荐
user_name = mapped_column(String(32))
```

### 4. 可空类型

明确区分可空和不可空字段：

```python
# 可选字段
email: Mapped[str | None] = mapped_column(nullable=True)

# 必填字段
user_name: Mapped[str] = mapped_column(nullable=False)
```

### 5. 枚举值使用

使用字符串类型的枚举值，便于数据库存储和扩展：

```python
# 推荐
status: Mapped[str] = mapped_column(CHAR(1), default="0")  # "0", "1", "2"

# 不推荐
from enum import Enum
class Status(Enum):
    NORMAL = 0
    DISABLED = 1
status: Mapped[Status] = ...
```

---

## 附录：完整示例

### 用户管理模型示例

```python
# ========== ORM 模型 ==========
class SysUser(SystemBase):
    """用户基础信息表"""
    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    nick_name: Mapped[str] = mapped_column(String(32), nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")
    # ... 其他字段

# ========== DTO 模型 ==========
class UserQueryDTO(PageQuery):
    """用户查询 DTO"""
    user_name: str | None = Field(default=None, description="用户账号")
    status: Literal["0", "1"] | None = Field(default=None)

class UserCreateDTO(DTO):
    """创建用户 DTO"""
    user_name: str = Field(description="用户账号")
    nick_name: str = Field(description="用户昵称")
    password: str = Field(description="用户密码")

# ========== VO 模型 ==========
class UserDetailVO(BaseVO):
    """用户详细信息 VO"""
    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    email: str | None = Field(default=None)

class UserListVO(BaseVO):
    """用户列表项 VO"""
    user_id: int
    user_name: str
    nick_name: str
    status: str
```
