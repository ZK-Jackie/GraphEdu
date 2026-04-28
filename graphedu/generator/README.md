# Generator 模块文档

> GraphEdu 代码生成器 - 基于数据库表结构自动生成全栈 CRUD 代码

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [核心功能](#核心功能)
- [工作原理](#工作原理)
- [详细配置](#详细配置)
- [模板系统](#模板系统)
- [API 参考](#api-参考)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 概述

Generator 是 GraphEdu 项目的代码生成器模块，能够从 PostgreSQL 数据库表结构自动生成符合项目架构规范的全栈代码。生成的代码包括：

- **后端**：ORM 实体、DTO/VO、Mapper、Service、API Controller
- **前端**：Vue 3 组件、TypeScript 类型、API 接口、国际化文件
- **SQL**：菜单权限 SQL 脚本

### 特性

- ⚡ **快速生成**：一键生成完整 CRUD 代码
- 🎯 **类型安全**：完整的类型定义和验证
- 🌳 **树形支持**：支持树形结构表生成
- 📦 **分层规范**：严格遵循项目分层架构
- 🎨 **模板化**：基于 Jinja2 的灵活模板系统
- 🌍 **国际化**：自动生成中英文翻译文件
- 🔒 **权限集成**：自动生成菜单和权限 SQL

## 快速开始

### 生成 ORM 模型

```bash
# 生成单个表的 ORM 实体
uv run -m graphedu generate code model edu_course

# 指定模块名
uv run -m graphedu generate code model edu_course -m course
```

### 生成完整 CRUD 代码

```bash
# 基础 CRUD（使用表名推断模块）
uv run -m graphedu generate code crud course

# 指定表名
uv run -m graphedu generate code crud student --table edu_student

# 树形结构
uv run -m graphedu generate code crud dept --template tree
```

### 查看可用模板

```bash
uv run -m graphedu generate code list
```

## 目录结构

```
graphedu/generator/
├── __init__.py                 # 模块入口
├── core/                       # 核心工具
│   ├── __init__.py
│   ├── gen_util.py            # 常量和工具方法
│   └── template_util.py       # 模板处理工具
├── services/                   # 生成服务
│   ├── __init__.py
│   ├── cli_generator.py       # CLI 代码生成器
│   ├── env_generator_service.py # 环境变量生成
│   └── schema_generator_service.py # Schema 生成
└── templates/                  # Jinja2 模板
    ├── env/                    # 环境变量模板
    ├── locales/                # 国际化模板
    ├── python/                 # Python 代码模板
    ├── sql/                    # SQL 脚本模板
    ├── typescript/             # TypeScript 模板
    └── vue/                    # Vue 组件模板
```

## 核心功能

### 1. 代码生成服务 (cli_generator.py)

核心生成服务，支持从数据库元数据生成全栈代码。

#### 主要函数

##### `generate_model(table_name, **kwargs)`

生成 ORM 实体模型。

**参数：**
- `table_name` (str): 数据库表名
- `schema` (str, optional): 数据库 schema，默认 'public'
- `module` (str, optional): 模块名
- `output_root` (str, optional): 输出根目录，默认 'graphedu'
- `db_url` (str, optional): 数据库连接 URL

**示例：**
```python
from graphedu.generator.services.cli_generator import generate_model

generate_model(
    table_name="edu_course",
    module="course",
    output_root="graphedu"
)
```

##### `generate_crud(module, **kwargs)`

生成完整 CRUD 代码（后端 + 前端）。

**参数：**
- `module` (str): 模块名
- `table_name` (str, optional): 表名，默认为 `{domain}_{module}`
- `schema` (str, optional): 数据库 schema
- `template` (str, optional): 模板类型 ('crud' | 'tree' | 'sub')
- `with_api` (bool, optional): 是否生成 API 层，默认 True
- `with_frontend` (bool, optional): 是否生成前端代码，默认 True
- `author` (str, optional): 作者名称

**示例：**
```python
from graphedu.generator.services.cli_generator import generate_crud

generate_crud(
    module="course",
    table_name="edu_course",
    template="crud",
    with_api=True,
    with_frontend=True,
    author="Your Name"
)
```

#### 生成的文件结构

```
graphedu/
├── api/services/education/
│   └── course.py                    # API Controller
├── services/education/
│   └── course.py                    # Service
├── mapper/
│   └── course.py                    # Mapper
└── common/models/
    ├── orm/education.py             # ORM（需手动合并）
    ├── dto/education/course.py      # DTO
    └── vo/education/course.py       # VO

graphedu-ui/src/
├── api/education/
│   └── course.ts                    # API 接口
├── types/api/
│   └── education.ts                 # 类型定义
├── views/education/course/
│   └── index.vue                    # Vue 页面
└── locales/
    ├── zh-CN.json                   # 中文
    └── en-US.json                   # 英文
```

### 2. 环境变量生成服务 (env_generator_service.py)

从 YAML 配置生成 .env 文件。

**特性：**
- 支持模板插值语法 `${path.to.config}`
- 支持默认值 `${path:default}`
- 敏感字段脱敏处理

**示例：**
```python
from graphedu.generator.services.env_generator_service import EnvGeneratorService

generator = EnvGeneratorService(
    config_file="dev.config.yaml",
    template_path="graphedu/generator/templates/env/.env.template"
)
generator.generate_env_file(output_path=".env")
```

**模板语法：**
```bash
# .env.template
DATABASE_URL=${database.postgresql.dsn}
REDIS_URL=${database.redis.dsn:redis://localhost:6379/0}
SECRET_KEY=${security.secret_key:default-secret-key}
```

### 3. 核心工具类 (core/gen_util.py)

#### GenConstant

定义生成器使用的常量：

```python
# 模板类型
TEMPLATE_CRUD = "crud"
TEMPLATE_TREE = "tree"
TEMPLATE_SUB = "sub"

# 前端模板类型
WEB_FRAME_ELEMENT_UI = "element-ui"
WEB_FRAME_ELEMENT_PLUS = "element-plus"
WEB_FRAME_ANTD_VUE = "antd-vue"

# 查询方式
QUERY_EQ = "EQ"      # 等于
QUERY_NE = "NE"      # 不等于
QUERY_GT = "GT"      # 大于
QUERY_LIKE = "LIKE"  # 模糊查询

# HTML 控件类型
HTML_INPUT = "input"
HTML_SELECT = "select"
HTML_RADIO = "radio"
HTML_DATE = "date"
HTML_IMAGE_UPLOAD = "imageUpload"

# 数据库类型映射
PostgreSQL_TYPE_MAPPING = {
    "varchar": "String",
    "integer": "Integer",
    "boolean": "Boolean",
    "text": "Text",
    "timestamp": "DateTime"
}
```

#### GenUtils

实用工具方法集合：

```python
# 命名转换
GenUtils.camel_to_snake("userName")  # "user_name"
GenUtils.snake_to_camel("user_name") # "userName"
GenUtils.snake_to_pascal("user_name") # "UserName"

# 初始化表信息
table_info = GenUtils.init_table_info(table_name, columns)

# 初始化字段信息
field_info = GenUtils.init_field_info(column, table_name)
```

## 工作原理

### 生成流程

```
1. 输入表名和配置
   ↓
2. 查询 PostgreSQL 元数据
   - 表信息（名称、注释）
   - 列信息（类型、约束、注释）
   ↓
3. 构建生成上下文
   - 类名、模块名、业务名
   - 字段属性（是否必填、是否查询等）
   - HTML 控件类型
   ↓
4. 选择模板并渲染
   - 根据生成类型选择模板
   - 填充上下文变量
   ↓
5. 输出文件到指定目录
```

### 类型推断逻辑

#### 领域推断

| 表名前缀 | 领域名       |
|---------|------------|
| `edu_`  | education  |
| `sys_`  | system     |
| `gen_`  | generator  |

#### 命名规则

```
表名: edu_student
├── 领域: education
├── 模块: student
├── 类名: Student / EduStudent
├── 包路径: education/
└── 文件名: student.py
```

#### 字段属性自动设置

**必填字段：**
```python
# 根据 is_nullable 判断
is_nullable='NO' → required=True
```

**查询字段：**
```python
# 排除以下字段
excluded_fields = ['id', 'created_by', 'created_time', 'updated_by', 'updated_time']
```

**HTML 控件推断：**
```python
# 字段名模式匹配
if field_name in ['status', 'state']:
    html_type = "radio"
elif field_name.endswith('type'):
    html_type = "select"
elif field_name.endswith('image'):
    html_type = "imageUpload"
elif field_name == 'content':
    html_type = "editor"
```

## 详细配置

### 数据库配置

代码生成器从项目配置文件读取数据库连接信息：

```yaml
# dev.config.yaml
database:
  postgresql:
    dsn: "postgresql://user:pass@localhost:5432/graphedu"
```

### 生成器配置

**命令行参数：**

| 参数              | 说明                  | 默认值      |
|-----------------|---------------------|-----------|
| `--table`       | 数据库表名              | {domain}_{module} |
| `--schema`      | 数据库 schema          | public    |
| `--template`    | 模板类型 (crud/tree/sub) | crud      |
| `--module` / `-m` | 模块名                | -         |
| `--output`      | 输出根目录              | graphedu  |
| `--author`      | 作者名称                | -         |
| `--no-api`      | 不生成 API 层          | False     |
| `--no-frontend` | 不生成前端代码           | False     |

### 类型映射配置

#### PostgreSQL → Python

| PostgreSQL 类型 | Python 类型   | SQLAlchemy 类型      |
|---------------|-------------|-------------------|
| varchar       | str         | String            |
| integer       | int         | Integer           |
| bigint        | int         | BigInteger        |
| boolean       | bool        | Boolean           |
| text          | str         | Text              |
| timestamp     | datetime    | DateTime          |
| date          | date        | Date              |
| decimal       | Decimal     | Numeric           |
| json / jsonb  | dict / list | JSON              |

## 模板系统

### 模板结构

```
templates/
├── python/                    # 后端代码模板
│   ├── orm.py.jinja2         # SQLAlchemy 实体
│   ├── dto.py.jinja2         # 数据传输对象
│   ├── service.py.jinja2     # 业务逻辑层
│   ├── service-tree.py.jinja2 # 树形 Service
│   ├── mapper.py.jinja2      # 数据访问层
│   ├── mapper-tree.py.jinja2 # 树形 Mapper
│   ├── api.py.jinja2         # API Controller
│   └── api-tree.py.jinja2    # 树形 API
├── typescript/               # 前端类型模板
│   ├── api.ts.jinja2         # API 接口
│   └── types.ts.jinja2       # 类型定义
├── vue/                      # Vue 组件模板
│   └── antd/
│       ├── index.vue.jinja2  # 列表页
│       └── index-tree.vue.jinja2 # 树形列表页
├── sql/                      # SQL 脚本
│   └── sql.jinja2            # 菜单权限 SQL
└── locales/                  # 国际化
    ├── zh.json.jinja2        # 中文
    └── en.json.jinja2        # 英文
```

### 模板变量

每个模板可用的上下文变量：

```python
{
    # 表信息
    "table_name": "edu_student",        # 表名
    "table_comment": "学生表",           # 表注释

    # 命名
    "module_name": "student",            # 模块名
    "domain": "education",              # 领域名
    "class_name": "Student",            # 类名（短）
    "orm_class_name": "EduStudent",     # ORM 类名（完整）
    "business_name": "student",         # 业务名
    "function_name": "学生",             # 功能名称

    # 字段
    "columns": [                         # 列信息列表
        {
            "column_name": "student_name",
            "column_comment": "姓名",
            "column_type": "varchar",
            "python_type": "str",
            "is_pk": "1",
            "is_required": True,
            "is_insert": True,
            "is_edit": True,
            "is_list": True,
            "is_query": True,
            "query_type": "LIKE",
            "html_type": "input"
        }
    ],

    # 元数据
    "author": "Your Name",
    "datetime": "2025-01-01 12:00:00",
    "package_name": "graphedu"
}
```

### 模板示例

#### ORM 模板 (orm.py.jinja2)

```jinja2
from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from graphedu.common.models.orm.base import Base


class {{ orm_class_name }}(Base):
    """{{ table_comment if table_comment else table_name }}"""

    __tablename__ = "{{ table_name }}"

    {% for column in columns %}
    {{ column.column_name }}: Mapped[{{ column.python_type }}] = mapped_column(
        {% if column.is_pk == '1' %}primary_key=True, {% endif %}
        {% if column.is_required %}nullable=False, {% endif %}
        comment="{{ column.column_comment }}",
    )
    {% endfor %}
```

#### API 模板 (api.py.jinja2)

```jinja2
from typing import List

from fastapi import APIRouter, Depends

from graphedu.common.models.dto.{{ domain }}.{{ module_name }} import (
    {{ class_name }}AddDTO,
    {{ class_name }}UpdateDTO,
    {{ class_name }}ListDTO,
)
from graphedu.common.models.vo.{{ domain }}.{{ module_name }} import {{ class_name }}VO
from graphedu.services.{{ domain }}.{{ module_name }} import {{ class_name }}Service
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit

router = APIRouter(prefix="/{{ module_name }}", tags=["{{ function_name }}"])


@router.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("{{ domain }}:{{ module_name }}:add"))],
    response_model={{ class_name }}VO,
)
async def create_{{ business_name }}(
    data: {{ class_name }}AddDTO,
    service: {{ class_name }}Service = Depends(),
):
    """新增{{ function_name }}"""
    return await service.create(data)
```

#### Vue 模板 (index.vue.jinja2)

```jinja2
<template>
  <div class="{{ module_name }}-container">
    <a-card :bordered="false">
      <!-- 查询表单 -->
      <a-form @finish="handleQuery">
        {% for column in columns if column.is_query %}
        <a-form-item label="{{ column.column_comment }}">
          <a-input v-model:value="queryParams.{{ column.column_name }}" />
        </a-form-item>
        {% endfor %}
      </a-form>

      <!-- 操作按钮 -->
      <a-button type="primary" @click="handleAdd">新增</a-button>

      <!-- 数据表格 -->
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
      />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { list{{ class_name }}, add{{ class_name }} } from '@/api/{{ domain }}/{{ module_name }}';

// 查询参数
const queryParams = ref<{{ class_name }}ListDTO>({
  {% for column in columns if column.is_query %}
  {{ column.column_name }}: undefined,
  {% endfor %}
});

// 数据源
const dataSource = ref<{{ class_name }}VO[]>([]);
</script>
```

## API 参考

### 函数签名

#### generate_model

```python
async def generate_model(
    table_name: str,
    schema: str = "public",
    module: str | None = None,
    output_root: str = "graphedu",
    db_url: str | None = None,
) -> None:
    """
    生成 ORM 实体模型

    Args:
        table_name: 数据库表名
        schema: 数据库 schema
        module: 模块名（可选）
        output_root: 输出根目录
        db_url: 数据库连接 URL（可选，默认从配置读取）
    """
```

#### generate_crud

```python
async def generate_crud(
    module: str,
    table_name: str | None = None,
    schema: str = "public",
    template: str = "crud",
    with_api: bool = True,
    with_frontend: bool = True,
    author: str | None = None,
    output_root: str = "graphedu",
    db_url: str | None = None,
) -> None:
    """
    生成完整 CRUD 代码

    Args:
        module: 模块名
        table_name: 表名（可选，默认为 {domain}_{module}）
        schema: 数据库 schema
        template: 模板类型 (crud/tree/sub)
        with_api: 是否生成 API 层
        with_frontend: 是否生成前端代码
        author: 作者名称
        output_root: 输出根目录
        db_url: 数据库连接 URL
    """
```

### 类参考

#### EnvGeneratorService

```python
class EnvGeneratorService:
    def __init__(
        self,
        config_path: str,
        template_path: str,
        config: dict | None = None,
    ):
        """
        环境变量生成服务

        Args:
            config_path: YAML 配置文件路径
            template_path: 模板文件路径
            config: 配置字典（可选）
        """

    def generate_env_file(
        self,
        output_path: str,
        mask_secrets: bool = True,
    ) -> None:
        """
        生成 .env 文件

        Args:
            output_path: 输出文件路径
            mask_secrets: 是否脱敏敏感字段
        """
```

## 最佳实践

### 1. 表设计规范

**命名规范：**
```sql
-- 好的命名
edu_student          -- 教育领域-学生表
edu_course_review    -- 教育领域-课程评价表
sys_user             -- 系统领域-用户表

-- 避免的命名
student              -- 缺少领域前缀
Student              -- 不要使用大写
eduStudentInfo       -- 不要使用驼峰
```

**字段规范：**
```sql
-- 必需字段
id              BIGINT       PRIMARY KEY,
created_time    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_time    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
created_by      BIGINT,
updated_by      BIGINT,

-- 状态字段
status          VARCHAR(20)  NOT NULL DEFAULT 'active',

-- 注释
COMMENT ON TABLE edu_student IS '学生表';
COMMENT ON COLUMN edu_student.student_name IS '学生姓名';
```

### 2. 模块组织

```
graphedu/
├── api/services/
│   ├── education/         # 教育模块
│   │   ├── course.py
│   │   ├── student.py
│   │   └── teacher.py
│   └── system/           # 系统模块
│       ├── user.py
│       └── role.py
├── services/
│   ├── education/
│   └── system/
└── mapper/
    ├── course.py
    ├── student.py
    └── user.py
```

### 3. 代码生成工作流

```bash
# 1. 设计数据库表
psql -f schema.sql

# 2. 生成 ORM 模型（先查看）
uv run -m graphedu generate code model edu_student

# 3. 手动合并 ORM 到对应文件
# 将生成的代码合并到 graphedu/common/models/orm/education.py

# 4. 生成完整 CRUD
uv run -m graphedu generate code crud student --table edu_student

# 5. 检查生成的代码
# - 确认字段映射正确
# - 确认查询字段设置合理
# - 确认 HTML 控件类型合适

# 6. 手动调整
# - 添加自定义业务逻辑
# - 添加复杂的查询条件
# - 调整前端布局
```

### 4. 自定义模板

如需自定义模板，可修改 `templates/` 目录下的文件：

```jinja2
# templates/python/custom_service.py.jinja2
from {{ package_name }}.services.{{ domain }}.{{ module_name }} import {{ class_name }}Service

class Custom{{ class_name }}Service({{ class_name }}Service):
    """自定义 {{ class_name }} 服务"""

    async def custom_method(self):
        # 自定义业务逻辑
        pass
```

## 常见问题

### Q1: 生成的 ORM 文件在哪里？

**A:** ORM 文件会生成到 `graphedu/common/models/orm/{domain}.py`。如果文件已存在，新生成的内容会追加到文件末尾。你需要手动检查并合并代码。

### Q2: 如何修改字段的查询类型？

**A:** 在生成的 Mapper 文件中修改 `query_fields` 列表：

```python
# mapper/student.py
query_fields = [
    {"field": "student_name", "op": "LIKE"},  # 模糊查询
    {"field": "status", "op": "EQ"},          # 精确查询
    {"field": "enrollment_date", "op": "GTE"}, # 大于等于
]
```

### Q3: 如何添加自定义查询条件？

**A:** 在生成的 Service 类中添加自定义方法：

```python
# services/education/student.py
class StudentService(BaseService[StudentVO, Student]):
    async def search_by_keyword(self, keyword: str) -> List[StudentVO]:
        """按关键字搜索学生"""
        return await self.mapper.list_by_options(
            whereclause=or_(
                Student.student_name.like(f"%{keyword}%"),
                Student.student_no.like(f"%{keyword}%")
            )
        )
```

### Q4: 树形结构表如何生成？

**A:** 使用 `--template tree` 参数：

```bash
uv run -m graphedu generate code crud dept --template tree
```

确保表包含以下字段：
- `id`: 主键
- `parent_id`: 父节点 ID
- `ancestors`: 祖级列表
- `order_num`: 显示顺序

### Q5: 如何修改生成的代码风格？

**A:** 有两种方式：

1. **修改模板**：编辑 `templates/` 目录下的 Jinja2 模板文件
2. **修改常量**：编辑 `core/gen_util.py` 中的类型映射和默认值

### Q6: 生成后需要手动做什么？

**A:** 通常需要：

1. **合并 ORM 文件**：将生成的实体类合并到领域 ORM 文件
2. **注册路由**：在 `api/__init__.py` 中注册新的 API 路由
3. **添加权限**：在数据库中添加菜单和权限记录
4. **前端路由**：在前端路由配置中添加新页面路由
5. **测试**：编写测试用例验证功能

### Q7: 如何重新生成已有模块？

**A:** 重新生成会覆盖现有文件。建议：

1. **备份现有代码**
2. **生成新代码**
3. **手动合并**保留自定义修改
4. **运行测试**确保功能正常

### Q8: 环境变量生成时如何处理敏感信息？

**A:** 使用脱敏功能：

```python
generator = EnvGeneratorService(config_path="prod.config.yaml")
generator.generate_env_file(output_path=".env.example", mask_secrets=True)
```

敏感字段（password、secret、token 等）会被替换为 `***`。

### Q9: 支持哪些数据库？

**A:** 目前主要支持 PostgreSQL。通过修改 `GenConstant` 中的类型映射，可以支持其他数据库（MySQL、SQLite 等）。

### Q10: 如何贡献新的模板？

**A:** 欢迎贡献！步骤：

1. 在 `templates/` 目录下创建新模板文件
2. 在 `TemplateUtils` 中注册模板
3. 添加模板类型常量到 `GenConstant`
4. 编写文档和使用示例
5. 提交 Pull Request

## 附录

### 命令速查

```bash
# 代码生成
uv run -m graphedu generate code model <table>        # 生成 ORM
uv run -m graphedu generate code crud <module>        # 生成 CRUD
uv run -m graphedu generate code list                 # 列出模板

# 环境变量
uv run -m graphedu generate env                       # 生成 .env
uv run -m graphedu generate env --mask                # 生成脱敏版本

# Schema
uv run -m graphedu generate schema                    # 生成 JSON Schema
```

### 相关文档

- [项目总体文档](../../CLAUDE.md)
- [前端文档](../../graphedu-ui/CLAUDE.md)
- [模型文档](../../common/models/README.md)
- [异常处理文档](../../common/exceptions/README.md)
- [配置说明](../../common/config/README.md)
