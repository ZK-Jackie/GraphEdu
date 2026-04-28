# SQL → ORM 转换规范

## 概述

根据 PostgreSQL DDL 生成模块化的 SQLAlchemy ORM 实体类。

## 核心原则

**采用模块化设计**: 根据表名前缀将表归类到不同的模块文件中 (例如 `sys_user` → `system.py`),并为每个模块生成独立的 `declarative_base()` 基类,确保业务逻辑的物理隔离。

## PostgreSQL 类型映射

严格使用 SQLAlchemy 的 PostgreSQL 方言类型进行映射:

| SQL 类型 (PostgreSQL)         | SQLAlchemy 类型                | Python 导入                        |
|------------------------------|-------------------------------|----------------------------------|
| `INTEGER`, `INT4`            | `Integer`                     | `sqlalchemy`                     |
| `BIGINT`, `INT8`             | `BigInteger`                  | `sqlalchemy`                     |
| `VARCHAR(n)`, `CHAR(n)`      | `String(n)`                   | `sqlalchemy`                     |
| `TEXT`                       | `Text`                        | `sqlalchemy`                     |
| `BOOLEAN`, `BOOL`            | `Boolean`                     | `sqlalchemy`                     |
| `NUMERIC(m, d)`, `DECIMAL`   | `Numeric(m, d)`               | `sqlalchemy`                     |
| `TIMESTAMP`, `TIMESTAMPTZ`    | `DateTime` 或 `TIMESTAMP`      | `sqlalchemy`                     |
| `DATE`                       | `Date`                        | `sqlalchemy`                     |
| `JSON`, `JSONB`              | `JSONB`                       | `sqlalchemy.dialects.postgresql` |
| `UUID`                       | `UUID(as_uuid=True)`          | `sqlalchemy.dialects.postgresql` |
| `BYTEA`                      | `LargeBinary`                 | `sqlalchemy`                     |
| `SMALLINT`                   | `SmallInteger`                | `sqlalchemy`                     |

**重要**: 务必导入 `from sqlalchemy.dialects.postgresql import JSONB, UUID`,否则无法识别 PostgreSQL 特定类型。

## 表到模块的映射规则

### 默认前缀映射

| 表名前缀  | 模块名      | 模块文件       |
|----------|------------|---------------|
| `sys_`   | `system`   | `system.py`   |
| `biz_`   | `business` | `business.py` |
| `gen_`   | `general`  | `general.py`  |
| `act_`   | `activity` | `activity.py` |
| `edu_`   | `education`| `education.py`|
| 无前缀    | (推断完整词) | 如 `user_detail` → `user.py` |

### 模块文件结构

每个模块文件应遵循以下结构:

```python
"""{模块名称} ORM 实体类
包含所有 {prefix}_ 开头的数据库表对应的实体类
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Index, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

# 定义模块基类
{Module}Base = declarative_base()


class {ClassName}({Module}Base):
    """{表注释}"""

    __tablename__ = '{table_name}'

    # 主键 (通常为 BIGINT)
    {id_field}: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="{主键描述}"
    )

    # 普通字段
    {field_name}: Mapped[str] = mapped_column(
        String({length}), nullable=False, default="{default}", comment="{字段描述}"
    )

    {field_name}: Mapped[str | None] = mapped_column(
        String({length}), nullable=True, comment="{可选字段描述}"
    )

    # 时间戳字段
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), comment="创建时间"
    )

    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间"
    )

    # JSONB 字段示例
    # ext_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="扩展信息")

    # UUID 字段示例
    # uuid_col: Mapped[UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, comment="唯一标识")

    __table_args__ = (
        Index('idx_{table}_{field}', '{field}'),
        {'comment': '{表注释}'}
    )
```

## 命名转换规则

| 项目            | 命名风格        | 示例                                |
|----------------|----------------|------------------------------------|
| 模块文件名       | snake_case     | `system.py`, `education.py`        |
| Base 类名       | PascalCase + Base | `SystemBase`, `EducationBase`    |
| 表类名          | PascalCase     | `sys_user` → `SysUser`             |
|                |                | `edu_course` → `EduCourse`         |
| 字段名          | snake_case     | 保持数据库字段命名,如 `create_time` |

### 表名到类名转换

```python
sys_user           → SysUser
sys_dept           → SysDept
sys_user_dept      → SysUserDept
edu_course_student → EduCourseStudent
```

## 字段解析规则

### 主键识别

```sql
-- PostgreSQL 主键定义
user_id BIGINT PRIMARY KEY
-- 或
PRIMARY KEY (user_id)
```

生成:
```python
user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
```

### 默认值处理

```sql
-- SQL 默认值
status VARCHAR(1) DEFAULT '0'
sort_order INTEGER DEFAULT 0
create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

生成:
```python
status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态")
sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.current_timestamp(), comment="创建时间")
```

### 可空字段

```sql
-- 可空字段
email VARCHAR(64)
phonenumber VARCHAR(16)
```

生成:
```python
email: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="邮箱")
phonenumber: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="手机号")
```

### 唯一约束

```sql
-- SQL 唯一约束
user_name VARCHAR(32) NOT NULL UNIQUE
```

生成:
```python
user_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="用户名")
```

### 索引定义

```sql
-- SQL 索引
CREATE INDEX idx_sys_user_user_name ON sys_user(user_name);
```

生成:
```python
__table_args__ = (
    Index('idx_sys_user_user_name', 'user_name'),
    {'comment': '用户表'}
)
```

## 完整示例

### 输入 SQL

```sql
CREATE TABLE sys_user
(
    user_id      BIGINT PRIMARY KEY,
    user_name    VARCHAR(32) NOT NULL UNIQUE,
    nick_name    VARCHAR(32) NOT NULL,
    password     VARCHAR(128) NOT NULL,
    email        VARCHAR(64) DEFAULT '',
    phonenumber  VARCHAR(16) DEFAULT '',
    user_type    VARCHAR(2) DEFAULT '4',
    status       CHAR(1) DEFAULT '0',
    create_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sys_user IS '用户基础信息表';
COMMENT ON COLUMN sys_user.user_id IS '用户ID';
COMMENT ON COLUMN sys_user.user_name IS '登录账号';
COMMENT ON COLUMN sys_user.nick_name IS '用户昵称';

CREATE INDEX idx_sys_user_user_name ON sys_user(user_name);
CREATE INDEX idx_sys_user_status ON sys_user(status);
```

### 输出 ORM (graphedu/common/models/orm/system.py)

```python
"""系统相关实体类
包含所有 sys_ 开头的数据库表对应的实体类
"""

from datetime import datetime
from sqlalchemy import BigInteger, Index, Integer, SmallInteger, String, func, CHAR
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

SystemBase = declarative_base()


class SysUser(SystemBase):
    """用户基础信息表。"""

    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="登录账号")
    nick_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="用户昵称")
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码")
    email: Mapped[str] = mapped_column(String(64), default="", comment="邮箱")
    phonenumber: Mapped[str] = mapped_column(String(16), default="", comment="手机号")
    user_type: Mapped[str] = mapped_column(String(2), default='4', comment="用户类型")
    status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp(), comment="更新时间")

    __table_args__ = (
        Index('idx_sys_user_user_name', 'user_name'),
        Index('idx_sys_user_status', 'status'),
        {'comment': '用户基础信息表'}
    )
```

## 常见 SQL 模式解析

### 自增主键

```sql
-- PostgreSQL IDENTITY (PostgreSQL 10+)
user_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY

-- 或使用 SERIAL
user_id BIGSERIAL PRIMARY KEY
```

生成:
```python
user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
```

### 枚举值字段

```sql
status CHAR(1) DEFAULT '0' -- 0正常 1停用
user_type SMALLINT -- 1-学生, 2-教师, 3-管理员
```

生成:
```python
status: Mapped[str] = mapped_column(CHAR(1), default="0", comment="状态（0正常 1停用）")
user_type: Mapped[int] = mapped_column(SmallInteger, comment="用户类型: 1-学生, 2-教师, 3-管理员")
```

### 外键关系

```sql
-- SQL 外键
dept_id BIGINT REFERENCES sys_dept(dept_id)
```

生成:
```python
# 简单外键 (仅定义字段)
dept_id: Mapped[int] = mapped_column(BigInteger, comment="部门ID")

# 或定义关系 (需要手动处理)
# dept: Mapped["SysDept"] = relationship("SysDept", foreign_keys=[dept_id])
```

**注意**: 复杂的外键关系建议手动定义,避免自动生成错误。

## 更新策略

### 覆盖模式 (推荐大版本更新)

1. 删除现有模块文件
2. 重新解析 SQL
3. 生成所有 Base 和 Class
4. **优点**: 结构清晰,无冗余代码
5. **缺点**: 丢失手动修改的关系定义

### 增量模式 (推荐日常开发)

1. 读取现有模块文件
2. 解析已有的 Base 和 Class
3. 仅添加新表对应的 Class
4. 保留 Base 定义不变
5. **优点**: 保留手动修改
6. **缺点**: 可能产生冗余代码

## 注意事项

### ⚠️ 方言导入

**必须导入 PostgreSQL 方言类型**:
```python
from sqlalchemy.dialects.postgresql import JSONB, UUID
```

否则会报错: `TypeError: object of type 'JSONB' is not JSON serializable`

### ⚠️ Base 隔离

不同模块的 Base 实例是独立的:
```python
# system.py
SystemBase = declarative_base()

# education.py
EducationBase = declarative_base()
```

这用于防止跨模块的错误关联,但在需要跨模块 JOIN 时需注意元数据管理。

### ⚠️ Timestamp 时区

```sql
TIMESTAMP WITH TIME ZONE  → DateTime(timezone=True)
TIMESTAMP                 → DateTime(timezone=False)
```

### ⚠️ JSON vs JSONB

- `JSON`: 保留输入的空格和键顺序 (性能较低)
- `JSONB`: 解析后的二进制格式 (推荐,性能更好)

建议在 Python 中优先使用 `JSONB`,除非需要保留原始格式。

### ⚠️ 关系映射

复杂的关系 (如 `relationship`) 通常需要手动定义:

```python
class SysUser(SystemBase):
    # ...
    # avatar_file: Mapped[Optional['SysUpload']] = relationship(
    #     'SysUpload', foreign_keys=[avatar_file_id]
    # )
```

自动生成时建议注释掉关系字段,由用户手动添加。

## 常见错误

### 错误 1: JSONB 类型未识别

```
NameError: name 'JSONB' is not defined
```

**解决**: 添加导入 `from sqlalchemy.dialects.postgresql import JSONB`

### 错误 2: UUID 类型错误

```
TypeError: UUID type is not supported
```

**解决**: 使用 `UUID(as_uuid=True)` 并导入 `from sqlalchemy.dialects.postgresql import UUID`

### 错误 3: 重复定义 Base

```
sqlalchemy.exc.InvalidRequestError: Table 'sys_user' is already defined
```

**解决**: 每个模块使用独立的 Base,或使用全局 `DeclarativeBase`