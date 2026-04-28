# ORM → VO/DTO 转换规范

## 概述

从 SQLAlchemy ORM 实体类自动生成 Pydantic VO (响应) 和 DTO (请求) 模型。

## 核心原则

### VO (View Object - 响应模型)

**用途**: 定义 API 响应的数据结构
**特点**:
- 继承 `BaseModel`
- 配置 `ConfigDict(from_attributes=True)` (支持从 ORM 对象创建)
- **排除敏感字段**: password
- **包含关联信息**: role_ids, dept_ids, avatar_url (计算字段)

### DTO (Data Transfer Object - 请求模型)

**用途**: 定义 API 请求的数据验证
**类型**:
- **CreateDTO**: 创建操作,必填业务字段 (排除 id, 时间戳)
- **UpdateDTO**: 更新操作,可选业务字段
- **QueryDTO**: 查询操作,继承 `PageQuery`,包含查询条件字段

## 字段映射规则

### 基础类型映射

| SQLAlchemy 类型 | Pydantic 字段类型 | 说明 |
|----------------|-----------------|------|
| `Mapped[int]` (BigInteger) | `int` | 整数 |
| `Mapped[str]` (String) | `str` | 字符串 |
| `Mapped[str | None]` | `str | None` | 可选字符串 |
| `Mapped[datetime]` (TIMESTAMP) | `datetime` | 日期时间 |
| `Mapped[bool]` (Boolean) | `bool` | 布尔值 |
| `Mapped[dict]` (JSONB) | `dict` | JSON 对象 |

### 字段命名

- **保持 ORM 的字段命名** (snake_case),例如 `user_id`, `create_time`
- **不进行 camelCase 转换**,转换仅在后端→前端时发生

### 字段描述

- 从 ORM 的 `comment` 参数提取字段描述
- 如果 ORM 没有注释,根据字段名推断默认描述

## VO 生成规则

### 标准字段包含

✅ **包含字段**:
- 业务主键: `{entity}_id` (如 `user_id`, `dept_id`)
- 显示字段: `name`, `title`, `key` 等展示用字段
- 状态字段: `status`, `enabled`, `is_*`
- 时间戳: `create_time`, `update_time`, `login_date`
- 关联 ID: `dept_id`, `role_id`, `parent_id`
- 扩展字段: `remark`, `description`

❌ **排除字段**:
- `password`, `pwd` - 密码字段
- 内部计数器

### VO 模板

```python
"""{模块}相关 VO 模型 (View Objects - 响应模型)

职责:
1. 定义 API 响应的数据结构
2. 配置序列化规则 (from_attributes=True 支持从 ORM 对象创建)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class {Entity}DetailVO(BaseModel):
    """{表注释}详细信息 VO"""

    model_config = ConfigDict(from_attributes=True)

    # 主键
    {entity_id}: int = Field(description="{主键描述}")

    # 基础字段
    {field_name}: str = Field(description="{字段描述}")
    {field_name}: str | None = Field(default=None, description="{可选字段描述}")

    # 时间字段
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_time: datetime | None = Field(default=None, description="更新时间")


class {Entity}ListVO(BaseModel):
    """{表注释}列表项 VO"""

    model_config = ConfigDict(from_attributes=True)

    {entity_id}: int = Field(description="{主键}")
    {field_name}: str = Field(description="{字段}")
    create_time: datetime | None = Field(default=None, description="创建时间")
```

### 关联字段处理

对于包含关联的表 (如用户-角色、部门):

```python
class UserDetailVO(BaseModel):
    """用户详细信息 VO"""

    # ... 基础字段 ...

    # 关联 ID 列表 (从关联表查询获得)
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
```

## DTO 生成规则

### CreateDTO (创建)

**包含字段**:
- ✅ 业务必填字段 (如 `user_name`, `nick_name`, `password`)
- ✅ 可选业务字段 (如 `email`, `phonenumber`)
- ❌ 主键 ID (由数据库生成)
- ❌ 时间戳 (由数据库/框架自动设置)

**模板**:
```python
class {Entity}CreateDTO(DTO):
    """创建{实体} DTO

    用于管理员创建新{实体}

    Attributes:
        {field}: {字段描述}
    """

    {required_field}: str = Field(description="{必填字段描述}")
    {optional_field}: str | None = Field(default=None, description="{可选字段描述}")
```

### UpdateDTO (更新)

**包含字段**:
- ✅ 所有可更新的业务字段 (全部设为可选)
- ❌ 主键 ID (放在路径参数中)
- ❌ 不可变字段 (如创建时间)

**模板**:
```python
class {Entity}UpdateDTO(DTO):
    """更新{实体} DTO

    用于管理员更新{实体}信息

    Attributes:
        {field}: {字段描述}
    """

    {field}: str | None = Field(default=None, description="{字段描述}")
```

### QueryDTO (查询)

**继承**: `PageQuery` (提供 `page`, `page_size`, `order_by`, `sort_order`)

**包含字段**:
- ✅ 常用查询条件字段
- ✅ 范围查询字段 (`begin_time`, `end_time`)
- ✅ 列表查询字段 (`role_ids`, `dept_ids`)

**模板**:
```python
class {Entity}QueryDTO(PageQuery):
    """{实体}查询 DTO"""

    {entity_id}: int | None = Field(default=None, description="{实体}ID")
    {field_name}: str | None = Field(default=None, description="{字段}")
    status: Literal["0", "1"] | None = Field(default=None, description="状态（0正常 1停用）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")
```

## 特殊字段处理

### 枚举字段

```python
# ORM
status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用）")

# VO/DTO
status: str = Field(description="状态")
user_type: str = Field(description="用户类型: 1-学生, 2-教师, 3-管理员")
```

### JSONB 字段

```python
# ORM
ext_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

# VO
ext_info: dict | None = Field(default=None, description="扩展信息")
```

### 密码字段

```python
# DTO - 仅在创建/重置密码时包含
password: str = Field(description="密码")
old_password: str | None = Field(default=None, description="旧密码")
new_password: str | None = Field(default=None, description="新密码")

# VO - 永不包含密码字段
```

## 文件组织

### 单文件结构

如果模块较小 (<3 个表),所有模型放在一个文件:

```python
# graphedu/common/models/vo/user.py
class UserDetailVO(BaseModel): ...
class UserListVO(BaseModel): ...
class UserProfileVO(BaseModel): ...
```

### 多文件结构

如果模块较大 (>3 个表),按业务拆分:

```python
# graphedu/common/models/vo/
├── user.py          # UserDetailVO, UserListVO
├── role.py          # RoleDetailVO, RoleListVO
└── dept.py          # DeptDetailVO, DeptListVO
```

## 导入规范

### 基础导入

```python
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field

from graphedu.common.models.dto.base import DTO, PageQuery
```

### 跨模块导入

如果 VO 需要引用其他模块的 VO:

```python
from graphedu.common.models.vo.systemv2.dept import DeptDetailVO
from graphedu.common.models.vo.systemv2.role import RoleDetailVO


class UserDetailVO(BaseModel):
   dept: DeptDetailVO | None = None
   roles: list[RoleDetailVO] = []
```

## 更新策略

### 增量更新模式 (推荐)

1. 读取现有 VO/DTO 文件
2. 解析已有的类定义
3. 仅添加新字段或新类
4. 保留用户自定义的验证器 (`@model_validator`)

### 覆盖更新模式

1. 删除现有文件
2. 根据 ORM 重新生成所有类
3. 适用于:
   - ORM 发生重大变更
   - 首次生成
   - 需要清理冗余代码

## 示例

### 输入: ORM 类

```python
class SysUser(SystemBase):
    """用户基础信息表。"""

    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="登录账号")
    nick_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="用户昵称")
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码（bcrypt加密）")
    email: Mapped[str] = mapped_column(String(64), default="", comment="用户邮箱")
    phonenumber: Mapped[str] = mapped_column(String(16), default="", comment="手机号码")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0", comment="帐号状态（0正常 1停用）")
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
```

### 输出 1: UserDetailVO

```python
class UserDetailVO(BaseModel):
    """用户详细信息 VO"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    email: str = Field(description="用户邮箱")
    phonenumber: str = Field(description="手机号码")
    status: str = Field(description="帐号状态（0正常 1停用）")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联字段 (手动添加或从关联表推断)
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
```

### 输出 2: UserCreateDTO

```python
class UserCreateDTO(DTO):
    """创建用户 DTO

    用于管理员创建新用户

    Attributes:
        user_name: 用户账号
        nick_name: 用户昵称
        password: 用户密码
        email: 用户邮箱（可选）
        phonenumber: 手机号码（可选）
    """

    user_name: str = Field(description="用户账号")
    nick_name: str = Field(description="用户昵称")
    password: str = Field(description="用户密码")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
```

### 输出 3: UserQueryDTO

```python
class UserQueryDTO(PageQuery):
    """用户查询 DTO"""

    user_id: int | None = Field(default=None, description="用户ID")
    user_name: str | None = Field(default=None, description="用户账号")
    nick_name: str | None = Field(default=None, description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    status: Literal["0", "1"] | None = Field(default=None, description="帐号状态（0正常 1停用）")
```

## 注意事项

### ⚠️ 关联字段推断

- ORM 的关系字段 (如 `relationship`) 在 VO 中可能需要转换为 ID 列表
- 复杂关联 (如 `user.roles`) 需要手动定义嵌套 VO

### ⚠️ 计算字段

某些字段 (如 `avatar_url`) 不在 ORM 中,由运行时计算:
- 需要在 VO 中手动添加
- 标注为运行时生成字段

### ⚠️ 验证器保留

如果现有 DTO 包含自定义验证器 (如密码合法性检查),增量更新时应保留:

```python
@model_validator(mode="after")
def check_password(self) -> "UserCreateDTO":
    pattern = r"""^[^<>"'|\\]+$"""
    if self.password is None or re.match(pattern, self.password):
        return self
    raise RegisterIllegalPasswordException(reason="密码不能包含非法字符")
```