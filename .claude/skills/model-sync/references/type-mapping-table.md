# 完整类型映射表

本文档提供跨三层的完整类型映射参考。

## 层级概览

```
PostgreSQL SQL          SQLAlchemy ORM          Pydantic DTO/VO         TypeScript
    ↓                        ↓                       ↓                       ↓
  BIGINT           →    BigInteger       →       int           →       number
  VARCHAR(32)      →    String(32)       →       str           →       string
  JSONB            →    JSONB            →       dict          →       Record<string, any>
  TIMESTAMP        →    DateTime         →       datetime      →       string (ISO 8601)
```

## PostgreSQL → SQLAlchemy ORM

### 数值类型

| PostgreSQL 类型          | SQLAlchemy 类型           | Python 类型   | 示例                     |
|-------------------------|--------------------------|--------------|-------------------------|
| `SMALLINT`              | `SmallInteger`           | `int`        | 年龄、状态码              |
| `INTEGER`, `INT`        | `Integer`                | `int`        | 数量、计数                |
| `BIGINT`, `INT8`        | `BigInteger`             | `int`        | 主键 ID、外键 ID          |
| `NUMERIC(m, d)`         | `Numeric(m, d)`          | `Decimal`    | 金额、精确小数            |
| `REAL`                  | `Float`                  | `float`      | 浮点数                   |
| `DOUBLE PRECISION`      | `Float`                  | `float`      | 双精度浮点               |

### 字符串类型

| PostgreSQL 类型          | SQLAlchemy 类型           | Python 类型   | 示例                     |
|-------------------------|--------------------------|--------------|-------------------------|
| `CHAR(n)`               | `CHAR(n)`                | `str`        | 固定长度字符串 (如状态码)   |
| `VARCHAR(n)`            | `String(n)`              | `str`        | 变长字符串 (如用户名)      |
| `TEXT`                  | `Text`                   | `str`        | 长文本 (如备注、描述)      |

### 布尔类型

| PostgreSQL 类型          | SQLAlchemy 类型           | Python 类型   | 示例                     |
|-------------------------|--------------------------|--------------|-------------------------|
| `BOOLEAN`, `BOOL`       | `Boolean`                | `bool`       | 是否启用、是否删除         |

### 日期时间类型

| PostgreSQL 类型               | SQLAlchemy 类型              | Python 类型      | 示例                  |
|------------------------------|-----------------------------|-----------------|---------------------|
| `DATE`                       | `Date`                      | `datetime.date` | 出生日期             |
| `TIME`                       | `Time`                      | `datetime.time` | 时间                 |
| `TIMESTAMP`                  | `DateTime`                  | `datetime`      | 创建时间、更新时间     |
| `TIMESTAMPTZ`                | `DateTime(timezone=True)`   | `datetime`      | 带时区的时间戳        |
| `INTERVAL`                   | `Interval`                  | `datetime.timedelta` | 时间间隔      |

### 二进制类型

| PostgreSQL 类型          | SQLAlchemy 类型           | Python 类型   | 示例                     |
|-------------------------|--------------------------|--------------|-------------------------|
| `BYTEA`                 | `LargeBinary`             | `bytes`      | 文件二进制数据            |

### JSON 类型

| PostgreSQL 类型          | SQLAlchemy 类型           | Python 类型   | 示例                     |
|-------------------------|--------------------------|--------------|-------------------------|
| `JSON`                  | `JSON`                    | `dict`       | JSON 数据 (保留格式)      |
| `JSONB`                 | `JSONB`                   | `dict`       | JSON 数据 (二进制,推荐)   |

**重要**: `JSONB` 性能更好,推荐使用。需导入 `from sqlalchemy.dialects.postgresql import JSONB`。

### UUID 类型

| PostgreSQL 类型          | SQLAlchemy 类型               | Python 类型   | 示例                     |
|-------------------------|------------------------------|--------------|-------------------------|
| `UUID`                  | `UUID(as_uuid=True)`          | `UUID`       | 唯一标识符               |

**重要**: 需导入 `from sqlalchemy.dialects.postgresql import UUID`。

### 数组类型

| PostgreSQL 类型          | SQLAlchemy 类型           | Python 类型   | 示例                     |
|-------------------------|--------------------------|--------------|-------------------------|
| `INTEGER[]`             | `ARRAY(Integer)`          | `list[int]`  | 整数数组                 |
| `VARCHAR[]`             | `ARRAY(String)`           | `list[str]`  | 字符串数组               |
| `TEXT[]`                | `ARRAY(Text)`             | `list[str]`  | 文本数组                 |

## SQLAlchemy ORM → Pydantic DTO/VO

### 字段类型映射

| ORM 字段类型 (Mapped)        | Pydantic 字段类型         | VO/DTO 适用   | 示例                     |
|------------------------------|-------------------------|--------------|-------------------------|
| `Mapped[int]`                | `int`                   | 两者          | user_id, dept_id        |
| `Mapped[str]`                | `str`                   | 两者          | user_name, nick_name    |
| `Mapped[str | None]`         | `str | None`            | 两者          | email, phonenumber      |
| `Mapped[bool]`               | `bool`                  | 两者          | is_enabled, is_deleted  |
| `Mapped[float]`              | `float`                 | 两者          | price, score            |
| `Mapped[datetime]`           | `datetime`              | 两者          | create_time, update_time|
| `Mapped[dict]` (JSONB)       | `dict`                  | 两者          | ext_info, metadata      |
| `Mapped[list[T]]`            | `list[T]`               | 两者          | tags, role_ids (关联)   |

### 可选性处理

| ORM 定义                     | DTO 字段 (请求)            | VO 字段 (响应)            | 说明             |
|------------------------------|-------------------------|-------------------------|-----------------|
| `nullable=False`             | 必填字段                  | 必填字段                  | 创建时必须提供     |
| `nullable=True`              | 可选字段 (`| None`)       | 可选字段 (`| None`)       | 可选             |
| `default="value"`            | 可选字段 (有默认值)        | 可选字段 (有默认值)        | 通常标记为可选     |
| 主键 ID                      | ❌ 不包含                 | ✅ 包含                   | DTO 不含主键      |

### 特殊字段处理

#### 密码字段

```python
# ORM
password: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码")

# CreateDTO - 包含
password: str = Field(description="密码")

# UpdateDTO - 可选
password: str | None = Field(default=None, description="新密码")

# DetailVO - 永不包含
# (无密码字段)
```

#### 时间戳字段

```python
# ORM
create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp())

# CreateDTO - 不包含 (自动生成)
# (无此字段)

# DetailVO - 包含
create_time: datetime | None = Field(default=None, description="创建时间")
```

#### 关联字段

```python
# ORM (多对多关系)
# roles: Mapped[list["SysRole"]] = relationship(secondary="sys_user_role")

# DetailVO - 包含 ID 列表
role_ids: list[int] | None = Field(default=None, description="角色ID列表")

# QueryDTO - 支持 ID 列表查询
role_ids: list[int] | None = Field(default=None, description="角色ID列表")
```

## Pydantic DTO/VO → TypeScript

### 基础类型映射

| Python 类型                     | TypeScript 类型            | 可选标记?      | 示例                     |
|-------------------------------|--------------------------|--------------|-------------------------|
| `int`                         | `number`                 | ❌           | user_id, dept_id        |
| `str`                         | `string`                 | ❌           | user_name, nick_name    |
| `bool`                        | `boolean`                | ❌           | is_enabled              |
| `float`                       | `number`                 | ❌           | price                   |
| `datetime`                    | `string`                 | ✅           | create_time (ISO 8601)  |
| `dict`                        | `Record<string, any>`    | ✅           | ext_info                |
| `list[int]`                   | `number[]`               | ✅           | role_ids                |
| `list[str]`                   | `string[]`               | ✅           | tags                    |
| `T | None`                    | `T`                      | ✅ (添加 `?`)| 可选字段                 |
| `Optional[T]`                 | `T`                      | ✅ (添加 `?`)| 可选字段                 |
| `Literal['0', '1']`           | `'0' \| '1'`             | ❌           | status 字面量            |

### 可选字段处理

**Python 可选字段** → **TypeScript 可选属性**

```python
# Python (Pydantic)
email: str | None = Field(default=None, description="邮箱")
phonenumber: str | None = Field(default=None, description="手机号")

# TypeScript
email?: string  // 自动添加 ?
phonenumber?: string
```

### 泛型处理

**分页响应**:

```python
# Python
class PageResponse(BaseModel):
    total: int
    items: list[T]

# TypeScript
export interface PageResponse<T> {
    total: number
    items: T[]
}
```

**通用响应**:

```python
# Python
class ResponseType(BaseModel):
    code: str
    data: T
    msg: str

# TypeScript
export interface ResponseType<T> {
    code: string
    data: T
    msg: string
}
```

### 字面量类型

**Python `Literal`** → **TypeScript 联合类型**

```python
# Python
status: Literal["0", "1"] = Field(description="状态")
user_type: Literal[1, 2, 3] = Field(description="用户类型")

# TypeScript
status: '0' | '1'
user_type: 1 | 2 | 3
```

## 命名转换

### 表名 / 类名转换

| 数据库表名         | ORM 类名        | VO/DTO 类名      | TypeScript 接口  |
|------------------|----------------|-----------------|-----------------|
| `sys_user`       | `SysUser`       | `UserDetailVO`   | `UserDetailVO`  |
| `sys_dept`       | `SysDept`       | `DeptDetailVO`   | `DeptDetailVO`  |
| `edu_course`     | `EduCourse`     | `CourseDetailVO` | `CourseDetailVO`|
| `biz_order`      | `BizOrder`      | `OrderDetailVO`  | `OrderDetailVO` |

**规则**:
- **ORM**: 表名转大驼峰 (PascalCase)
- **VO/DTO**: 实体名 + 类型后缀 (如 `UserDetailVO`, `UserCreateDTO`)
- **TypeScript**: 保持 VO/DTO 命名

### 字段名转换 (snake_case ↔ camelCase)

| Python (后端)       | TypeScript (前端) | 说明       |
|-------------------|------------------|-----------|
| `user_id`         | `userId`         | ID 字段   |
| `user_name`       | `userName`       | 普通字段    |
| `nick_name`       | `nickName`       | 普通字段    |
| `phone_number`    | `phoneNumber`    | 普通字段    |
| `avatar_file_id`  | `avatarFileId`   | 多词字段   |
| `create_time`     | `createTime`     | 时间字段    |
| `update_time`     | `updateTime`     | 时间字段    |
| `role_ids`        | `roleIds`        | 列表字段    |
| `dept_ids`        | `deptIds`        | 列表字段    |

**转换函数** (TypeScript):
```typescript
function snakeToCamel(str: string): string {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}
```

## 完整示例: 用户表

### PostgreSQL SQL

```sql
CREATE TABLE sys_user (
    user_id      BIGINT PRIMARY KEY,
    user_name    VARCHAR(32) NOT NULL UNIQUE,
    nick_name    VARCHAR(32) NOT NULL,
    password     VARCHAR(128) NOT NULL,
    email        VARCHAR(64) DEFAULT '',
    phonenumber  VARCHAR(16) DEFAULT '',
    user_type    SMALLINT DEFAULT 1,
    status       CHAR(1) DEFAULT '0',
    create_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### SQLAlchemy ORM

```python
class SysUser(SystemBase):
    """用户基础信息表。"""

    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="登录账号")
    nick_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="用户昵称")
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码")
    email: Mapped[str] = mapped_column(String(64), default="", comment="邮箱")
    phonenumber: Mapped[str] = mapped_column(String(16), default="", comment="手机号")
    user_type: Mapped[int] = mapped_column(SmallInteger, default=1, comment="用户类型")
    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), comment="更新时间")
```

### Pydantic VO

```python
class UserDetailVO(BaseModel):
    """用户详细信息 VO"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    email: str = Field(description="邮箱")
    phonenumber: str = Field(description="手机号")
    user_type: int = Field(description="用户类型")
    status: str = Field(description="状态")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_time: datetime | None = Field(default=None, description="更新时间")
```

### Pydantic DTO

```python
class UserCreateDTO(DTO):
    """创建用户 DTO"""

    user_name: str = Field(description="用户账号")
    nick_name: str = Field(description="用户昵称")
    password: str = Field(description="密码")
    email: str | None = Field(default=None, description="邮箱")
    phonenumber: str | None = Field(default=None, description="手机号")
```

### TypeScript

```typescript
// 类型定义
export interface UserDetailVO {
    /** 用户ID */
    userId: number

    /** 登录账号 */
    userName: string

    /** 用户昵称 */
    nickName: string

    /** 邮箱 */
    email: string

    /** 手机号 */
    phonenumber: string

    /** 用户类型 */
    userType: number

    /** 状态 */
    status: string

    /** 创建时间 */
    createTime?: string

    /** 更新时间 */
    updateTime?: string
}

export interface UserCreateDTO {
    /** 用户账号 */
    userName: string

    /** 用户昵称 */
    nickName: string

    /** 密码 */
    password: string

    /** 邮箱 */
    email?: string

    /** 手机号 */
    phonenumber?: string
}

// API 函数
export function addUser(data: UserCreateDTO): Promise<ResponseType<UserDetailVO>> {
    return request({
        url: '/system/user',
        method: 'post',
        data: data
    })
}
```

## 特殊场景

### 枚举值字段

```python
# Python ORM
user_type: Mapped[int] = mapped_column(SmallInteger, comment="用户类型: 1-学生, 2-教师, 3-管理员")

# Python VO
user_type: int = Field(description="用户类型: 1-学生, 2-教师, 3-管理员")

# TypeScript
userType: number  // 或使用字面量: 1 | 2 | 3
```

### JSONB 字段

```python
# Python ORM
ext_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="扩展信息")

# Python VO
ext_info: dict | None = Field(default=None, description="扩展信息")

# TypeScript
extInfo?: Record<string, any>
```

### 时间范围查询

```python
# Python DTO
begin_time: datetime | None = Field(default=None, description="开始时间")
end_time: datetime | None = Field(default=None, description="结束时间")

# TypeScript
beginTime?: string
endTime?: string
```

### 列表查询

```python
# Python DTO
role_ids: list[int] | None = Field(default=None, description="角色ID列表")

# TypeScript
roleIds?: number[]
```