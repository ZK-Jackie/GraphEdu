# graphrag-pgvector

PostgreSQL + pgvector 后端适配，为 [microsoft/graphrag](https://github.com/microsoft/graphrag) 提供完整的存储（Storage）和向量检索（VectorStore）支持。

---

## 目录

- [概述](#概述)
- [架构](#架构)
- [安装](#安装)
- [快速开始](#快速开始)
- [PostgresStorage（KV 存储）](#postgresstorage)
  - [表结构](#storage-表结构)
  - [任务隔离](#任务隔离)
  - [子命名空间](#子命名空间)
  - [API 参考](#storage-api)
- [PostgresVectorStore（向量存储）](#postgresvectorstore)
  - [表结构](#vectorstore-表结构)
  - [任务隔离](#vectorstore-任务隔离)
  - [过滤器](#过滤器)
  - [API 参考](#vectorstore-api)
- [多任务隔离设计](#多任务隔离设计)
- [连接池配置](#连接池配置)
- [与 graphrag pipeline 的集成](#与-graphrag-pipeline-的集成)
- [设计决策说明](#设计决策说明)
- [已知限制](#已知限制)

---

## 概述

graphrag 的管道（pipeline）产出两类数据：

| 数据类型 | 内容 | 对应组件 |
|---|---|---|
| **Parquet 文件**（二进制） | `entities.parquet`、`relationships.parquet`、`community_reports.parquet` 等 | `PostgresStorage` |
| **向量嵌入** | 实体/社区/文本块的语义向量 + 结构化元数据 | `PostgresVectorStore` |

两者共享同一个 PostgreSQL 实例，但存储于不同的表中，通过 **namespace** 实现多任务（多项目）数据隔离。

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                  graphrag Pipeline                      │
│                                                         │
│  indexing 阶段                                          │
│    → entities.parquet, relationships.parquet, ...       │
│                         │  bytes                        │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │  PostgresStorage    │  graphrag_storage  │
│              │  namespace / key    │  表（BYTEA）        │
│              └─────────────────────┘                    │
│                                                         │
│  embedding 阶段                                         │
│    → entity vectors, community vectors, ...             │
│                         │  VectorStoreDocument          │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │ PostgresVectorStore │  graphrag_vectors  │
│              │  index_name / id    │  表（vector + JSONB）│
│              └─────────────────────┘                    │
└─────────────────────────────────────────────────────────┘

query 阶段（Local / Global Search）
  ① VectorStore.similarity_search() → 找相关实体/社区 ID
  ② Storage.get("entities.parquet") → bytes → pd.read_parquet()
  ③ 组装上下文 → LLM 生成答案
```

---

## 安装

```bash
# 在 GraphEdu 项目中作为本地依赖使用
uv add --editable ./libs/graphrag-pgvector

# 或直接安装
pip install ./libs/graphrag-pgvector
```

**前置要求**：PostgreSQL 14+ 并安装 pgvector 扩展：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 快速开始

### 注册插件

在启动时调用注册函数，将两个后端注入 graphrag 的插件注册表：

```python
from graphrag_pgvector import register_graphrag_pgvector, register_graphrag_pgvector_storage

# 注册 Storage 后端（settings.yml 中 storage.type: pgvector 生效）
register_graphrag_pgvector_storage()

# 注册 VectorStore 后端（settings.yml 中 vector_store.type: pgvector 生效）
register_graphrag_pgvector()
```

### settings.yml 配置

```yaml
storage:
  type: pgvector
  connection_string: "postgresql://user:pass@localhost:5432/graphedu"
  table_name: graphrag_storage    # 可选，默认 graphrag_storage
  namespace: "project_42"         # ⚠️ 多任务部署必填，见"任务隔离"

vector_store:
  type: pgvector
  connection_string: "postgresql://user:pass@localhost:5432/graphedu"
  namespace: "project_42"         # ⚠️ 必须与 storage 的 namespace 保持一致
  vector_size: 1536               # 可选，默认 1536（OpenAI text-embedding-3-small）
  index_name: entities            # 由 graphrag 自动按集合命名，通常无需手动设置
```

---

## PostgresStorage

### Storage 表结构

所有 Storage 实例共享**同一张物理表**，通过 `namespace` 列实现逻辑隔离：

```sql
CREATE TABLE graphrag_storage (
    namespace   TEXT        NOT NULL DEFAULT '',
    key         TEXT        NOT NULL,
    value       BYTEA,                              -- parquet bytes 或 JSON 编码后的字节
    encoding    TEXT,                               -- 非 bytes 值的编码，如 'utf-8'
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (namespace, key)
);

CREATE INDEX graphrag_storage_namespace_idx ON graphrag_storage (namespace);
```

`key` 的命名规律与 graphrag 的文件系统路径一致，例如：

| key | 内容 |
|---|---|
| `entities.parquet` | 所有抽取出的实体（id、title、description、type 等） |
| `relationships.parquet` | 实体间关系（source、target、description、weight 等） |
| `community_reports.parquet` | 社区摘要报告 |
| `text_units.parquet` | 文本切分块 |
| `nodes.parquet` | 图节点（用于布局计算） |
| `communities.parquet` | 社区信息 |

### 任务隔离

`namespace` 是任务隔离的唯一手段。**不同的 pipeline 任务必须使用不同的 namespace**，否则后写入的数据会覆盖前一任务的结果。

```python
from graphrag_pgvector import PostgresStorage

# ✅ 正确：每个项目使用独立的 namespace
storage_project_a = PostgresStorage(
    connection_string="postgresql://user:pass@host/db",
    namespace="project_a",
)
storage_project_b = PostgresStorage(
    connection_string="postgresql://user:pass@host/db",
    namespace="project_b",
)

# ❌ 错误：两个项目共用默认 namespace=""，数据会相互覆盖
storage_a = PostgresStorage(connection_string="postgresql://...")
storage_b = PostgresStorage(connection_string="postgresql://...")
```

**查询逻辑**：所有 SQL 操作都带 `WHERE namespace = %s` 过滤，不同 namespace 的数据完全隔离：

```sql
-- project_a 只能看到自己的数据
SELECT value FROM graphrag_storage WHERE namespace = 'project_a' AND key = 'entities.parquet';
-- project_b 只能看到自己的数据
SELECT value FROM graphrag_storage WHERE namespace = 'project_b' AND key = 'entities.parquet';
```

### 子命名空间

graphrag pipeline 会通过 `child()` 创建子级存储，映射到文件系统的子目录：

```python
# graphrag 内部调用模式（无需手动操作）
root = PostgresStorage(connection_string="...", namespace="project_42")
output = root.child("output")     # namespace = "project_42/output"
cache  = root.child("cache")      # namespace = "project_42/cache"
```

子实例与父实例共享同步连接池（在父池已初始化的前提下），不会重复创建数据库连接。

### Storage API

| 方法 | 类型 | 说明 |
|---|---|---|
| `get(key, as_bytes, encoding)` | `async` | 读取值；`as_bytes=True` 时直接返回原始 bytes |
| `set(key, value, encoding)` | `async` | 写入；bytes 直存，str 编码为 bytes，其他对象 JSON 序列化 |
| `has(key)` | `async` | 判断 key 是否存在 |
| `delete(key)` | `async` | 删除单条 |
| `clear()` | `async` | 清空当前 namespace 的所有数据 |
| `get_creation_date(key)` | `async` | 返回写入时间 ISO-8601 字符串 |
| `find(file_pattern, prefix, suffix)` | `sync` | 正则匹配 key；通过 PostgreSQL `~` 操作符下推，无全表扫描 |
| `keys()` | `sync` | 返回当前 namespace 所有 key |
| `child(name)` | `sync` | 返回子命名空间实例 |

---

## PostgresVectorStore

### VectorStore 表结构

所有 VectorStore 实例共享**同一张物理表**，通过 `index_name` 列实现逻辑隔离：

```sql
CREATE TABLE graphrag_vectors (
    index_name  TEXT    NOT NULL,              -- "{namespace}__{collection}"，如 "project_42__entities"
    id          TEXT    NOT NULL,
    vector      vector(1536),                  -- 向量嵌入（维度由 vector_size 配置）
    data        JSONB   DEFAULT '{}',          -- 文档结构化字段（title、description 等）
    create_date TEXT,
    update_date TEXT,
    PRIMARY KEY (index_name, id)
);

-- 每个 index_name 对应一个 partial HNSW 索引，用于近似最近邻加速
CREATE INDEX graphrag_vectors_{safe_idx}_hnsw_idx
ON graphrag_vectors USING hnsw (vector vector_cosine_ops)
WHERE index_name = '{effective_index_name}';
```

### VectorStore 任务隔离

`_index_key`（存入 `index_name` 列的值）由 `namespace` 和基础 `index_name` 拼合：

```
namespace="project_42", index_name="entities"  →  index_name = "project_42__entities"
namespace="project_42", index_name="communities" →  index_name = "project_42__communities"
namespace="",           index_name="entities"  →  index_name = "entities"  ← 任务间碰撞！
```

graphrag 为每类集合（entities、community_reports、text_units 等）创建独立的 VectorStore 实例，`namespace` 保证它们在多任务场景下不互相干扰。

### data JSONB 字段

`data` 列存储文档的结构化元数据，不同集合的字段不同：

| 集合（index_name 后缀） | data 中的典型字段 |
|---|---|
| `entities` | `title`、`description`、`type`、`human_readable_id` |
| `community_reports` | `title`、`summary`、`full_content`、`rank`、`community_id` |
| `text_units` | `text`、`document_ids`、`entity_ids`、`relationship_ids` |

查询时可用 `select` 参数限制返回的字段：

```python
results = store.similarity_search_by_vector(
    query_embedding=[...],
    k=10,
    select=["title", "description"],  # 只返回这两个字段，减少传输量
)
```

### 过滤器

支持对 `data` JSONB 字段的条件过滤，使用 graphrag 的 `FilterExpr` AST：

```python
from graphrag_vectors import Condition, Operator, AndExpr

# 只返回 type 为 "PERSON" 且 rank >= 5 的实体
filters = AndExpr(and_=[
    Condition(field="type", operator=Operator.eq, value="PERSON"),
    Condition(field="rank", operator=Operator.gte, value=5),
])

results = store.similarity_search_by_vector(
    query_embedding=[...],
    k=10,
    filters=filters,
)
```

支持的操作符：

| 操作符 | SQL 对应 | 备注 |
|---|---|---|
| `eq` / `ne` | `= / <>` | 字符串比较 |
| `gt` / `gte` / `lt` / `lte` | `::numeric > / >= / < / <=` | 自动 cast 为数值，避免 JSONB 文本比较语义错误 |
| `contains` / `startswith` / `endswith` | `LIKE` | 模糊匹配 |
| `in_` / `not_in` | `IN / NOT IN` | 多值匹配 |
| `exists` | `data ? field` | 判断字段是否存在 |
| `AndExpr` / `OrExpr` / `NotExpr` | `AND / OR / NOT` | 嵌套逻辑 |

### VectorStore API

| 方法 | 说明 |
|---|---|
| `connect()` | 创建连接池，`register_vector` 通过 `configure` 回调自动注册 |
| `create_index()` | 建表 + 建 partial HNSW 索引（幂等，可重复调用） |
| `insert(doc)` | 插入单条；ID 重复时抛 `ValueError` |
| `update(doc)` | 更新单条（UPSERT） |
| `load_documents(docs, overwrite)` | 批量写入（`executemany`）；`overwrite=True` 时先清空 |
| `similarity_search_by_vector(embedding, k, select, filters, include_vectors)` | 余弦相似度向量检索，返回 top-k 结果 |
| `similarity_search_by_text(text, text_embedder, k, ...)` | 先调用 embedder 生成向量再检索 |
| `search_by_id(id, select, include_vectors)` | 按 ID 精确查询；不存在时返回 `vector=None, data={}` |
| `count()` | 返回当前 index_name 下的文档总数 |
| `remove(ids)` | 批量删除 |

---

## 多任务隔离设计

两个模块的隔离键：

```
PostgresStorage：
  物理键 → (namespace, key)
  示例   → ('project_42', 'entities.parquet')

PostgresVectorStore：
  物理键 → (index_name, id)
  示例   → ('project_42__entities', 'entity-uuid-001')
```

**推荐的 namespace 命名规范**（与 GraphEdu 项目对齐）：

```
# 使用项目 ID（对应 GraphEdu 的 project 表主键）
namespace = f"project_{project_id}"          # project_42
namespace = f"project_{project_id}_v{ver}"  # project_42_v2（版本化索引）
```

**数据生命周期管理**：

```python
# 删除某个项目的全部 Storage 数据
await storage.clear()  # 只删 namespace='project_42' 的行，不影响其他项目

# 删除某个项目的向量数据
store.remove(ids=[...])       # 按 ID 删除
# 或重建时使用 overwrite=True
store.load_documents(docs, overwrite=True)
```

---

## 连接池配置

### PostgresStorage（异步路径）

异步路径使用单一 `psycopg.AsyncConnection`，适用于 graphrag pipeline 的串行写入场景。如需在异步并发场景中使用，可传入外部 `async_conn` 或升级为 `AsyncConnectionPool`（目前未内置，按需扩展）。

### PostgresStorage（同步路径）

`find()` / `keys()` 使用懒加载的 `psycopg_pool.ConnectionPool`，默认参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `min_size` | 1 | 最小保持连接数 |
| `max_size` | 3 | 最大并发连接数 |

### PostgresVectorStore

使用 `psycopg_pool.ConnectionPool`，在 `connect()` 时创建，默认参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `min_size` | 1 | 最小保持连接数 |
| `max_size` | `pool_size`（默认 5） | 最大并发连接数，对应 FastAPI 并发请求上限 |

根据实际并发量调整 `pool_size`：

```python
store = PostgresVectorStore(
    connection_string="postgresql://...",
    namespace="project_42",
    pool_size=10,   # 高并发场景适当增大
)
```

---

## 与 graphrag pipeline 的集成

### GraphEdu 项目中的典型调用模式

```python
from graphrag_pgvector import register_graphrag_pgvector, register_graphrag_pgvector_storage

# 应用启动时注册（在 graphedu/__init__.py 或 lifespan 中调用一次）
register_graphrag_pgvector_storage()
register_graphrag_pgvector()
```

```yaml
# dev.config.yaml（GraphEdu 项目配置）
graphrag:
  storage:
    type: pgvector
    connection_string: "${DATABASE_URL}"
    namespace: "${project_id}"   # 由业务层在运行时注入
  vector_store:
    type: pgvector
    connection_string: "${DATABASE_URL}"
    namespace: "${project_id}"
    vector_size: 1536
```

### query 阶段的数据流

```python
import pandas as pd
from io import BytesIO

# Local Search 典型流程
async def local_search(project_id: str, query: str):
    storage = PostgresStorage(connection_string=..., namespace=f"project_{project_id}")
    vector_store = PostgresVectorStore(connection_string=..., namespace=f"project_{project_id}")
    vector_store.connect()

    # 1. 向量检索：找最相关的实体
    results = vector_store.similarity_search_by_text(
        text=query,
        text_embedder=embedder,
        k=10,
        select=["title", "description"],
    )
    entity_ids = [r.document.id for r in results]

    # 2. 从 Storage 读取完整的关系数据
    relationships_bytes = await storage.get("relationships.parquet", as_bytes=True)
    relationships_df = pd.read_parquet(BytesIO(relationships_bytes))

    # 3. 过滤与顶层实体关联的关系，组装上下文...
```

---

## 设计决策说明

### 为什么 Storage 用 BYTEA 而非行拆分（参照 CosmosDB）？

CosmosDB 实现将 parquet 文件按行拆分存储（`pd.read_parquet → 每行一个 item`），这是 CosmosDB **不支持二进制存储**的妥协方案。

PostgreSQL 的 BYTEA 可直接存储 parquet 原始字节，优点：

- **单次 I/O**：`get()` 返回完整 bytes，调用方直接 `pd.read_parquet(BytesIO(bytes))`
- **语义一致**：与本地文件系统存储行为完全相同，便于切换
- **事务性**：写入是原子操作，无部分失败风险

对于 1~5MB 的 parquet 文件，PostgreSQL 的 TOAST 机制会自动处理分块存储，读取时透明重组，无需应用层介入。

### 为什么不引入 SQLAlchemy ORM？

向量操作依赖 pgvector 扩展的 `<=>` 操作符，SQLAlchemy 标准方言不原生支持，仍需大量 `text()` 降级。同时 `JSONB data` 列的动态结构不适合 ORM 映射。引入 SQLAlchemy Core 仅能简化部分查询构建，但会增加依赖复杂度，净收益低。

### 为什么 VectorStore 用 Partial HNSW 而非分表？

单表 + `index_name` 列 + Partial HNSW 索引，等效于 CosmosDB 的多容器隔离：

- **运维简单**：仅一张表，`CREATE INDEX IF NOT EXISTS` 幂等
- **查询效率**：Partial Index 限制 HNSW 只在目标 `index_name` 的行上构建，索引大小与分表方案相当
- **扩展灵活**：新增项目/索引无需 DDL，只需 `CREATE INDEX`

### 为什么用 CTE 重构 similarity_search？

原始实现将 `query_vec` 传参两次（SELECT 中计算分数，ORDER BY 中再次计算距离），PostgreSQL 执行两次向量运算。CTE 方案：

```sql
WITH scored AS (
    SELECT *, 1 - (vector <=> %s::vector) AS score  -- 只计算一次
    FROM graphrag_vectors WHERE index_name = %s ...
)
SELECT * FROM scored ORDER BY score DESC LIMIT %s   -- 复用计算结果
```

---

## 已知限制

| 项目 | 说明 | 建议 |
|---|---|---|
| **大文件性能** | parquet > 1MB 时触发 TOAST 分块，高并发读取有 I/O 放大 | 中期考虑引入 MinIO 混合存储 |
| **异步连接并发** | Storage 异步路径使用单连接，pipeline 并行化后存在瓶颈 | 按需升级为 `AsyncConnectionPool` |
| **namespace 规范** | 框架不强制 namespace 非空，调用方需自律传入任务 ID | 业务层封装时建议强制校验 |
| **向量维度固定** | `vector_size` 在建表后不可更改（pgvector 限制） | 更换 embedding 模型时需重建表 |
