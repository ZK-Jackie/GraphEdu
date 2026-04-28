# GraphEdu

> 基于知识图谱的教育平台 —— 智能化学习管理与内容生成系统

GraphEdu 是一个融合了知识图谱技术、AI 内容生成和现代化前端交互的教育平台。系统采用前后端分离架构，提供学生学习、课程管理、知识图谱可视化等核心功能。

## 项目简介

GraphEdu 旨在通过知识图谱技术提升学习体验，主要特色包括：

- **知识图谱驱动**：基于 Neo4j 构建课程知识图谱，可视化知识关联
- **AI 内容生成**：集成 LangChain/LangGraph，支持智能问答和内容生成
- **现代化交互**：Vue 3 + Ant Design Vue 构建响应式前端界面
- **PDF 智能解析**：基于 pdfjs-dist 的 PDF 阅读器，支持文本选中和标注
- **多角色权限**：学生/教师双角色视图，动态路由与菜单系统
- **实时通信**：WebSocket 支持的实时聊天和协作功能

## 技术栈

### 后端
- **框架**：FastAPI + SQLAlchemy 2.0（异步）
- **数据库**：PostgreSQL + pgvector + Redis
- **AI 引擎**：LangChain / LangGraph
- **任务队列**：Celery + Redis
- **对象存储**：MinIO / 阿里云 OSS
- **开发工具**：uv（包管理）+ Ruff（代码检查）+ pytest（测试）

### 前端
- **框架**：Vue 3.5 + TypeScript 5.9 + Vite 7
- **UI 组件**：Ant Design Vue 4.2 + Tailwind CSS 4.1
- **状态管理**：Pinia 3
- **路由**：Vue Router 4.6（动态路由系统）
- **PDF 渲染**：pdfjs-dist 5.6
- **图可视化**：Cytoscape.js + Neo4j
- **测试**：Vitest + Playwright

## 关键模块

### 后端架构（graphedu/）

```
graphedu/
├── api/              # API 接口层（Controller）
│   ├── services/     # 业务服务（系统/教育/AI代理）
│   └── middleware/   # 中间件（CORS/日志/认证）
├── services/         # 核心业务逻辑层（Service）
├── mapper/           # 数据访问层（Mapper）
├── common/           # 公共模块
│   ├── models/       # ORM/DTO/VO 定义
│   ├── config/       # 配置管理
│   ├── exceptions/   # 异常体系
│   └── resource/     # DB/Redis 客户端
├── security/         # 安全模块（认证/权限）
├── workers/          # Celery 后台任务
├── mcp/              # MCP (Model Context Protocol) 集成
└── cli/              # 命令行工具
```

### 前端架构（graphedu-ui/）

```
src/
├── api/              # API 请求封装
├── components/       # 公共组件
│   ├── mineru/       # PDF/Markdown 查看器
│   ├── dict/         # 字典组件
│   └── VueGoldenLayout/ # Golden Layout 集成
├── stores/           # Pinia 状态管理
├── router/           # 路由配置（动态路由系统）
├── views/            # 页面组件
│   ├── course/       # 课程学习
│   ├── admin/        # 后台管理
│   └── profile/      # 个人中心
└── utils/            # 工具函数
```

### 核心工作流程

#### 1. 动态路由与权限系统

```
登录 → JWT Token
  ↓
GET /system/user/getInfo → 获取用户权限
  ↓
GET /system/function/router?scene=xxx → 按场景获取菜单
  ↓
前端动态注册路由 → 加载对应组件
```

支持多场景路由：
- `web`：学生学习视图
- `admin`：后台管理
- `userInfo`：个人中心
- `mobile`：移动端（预留）

#### 2. 知识图谱构建与可视化

```
课程数据 → Pipeline 预处理
  ↓
提取实体/关系 → 存入 Neo4j
  ↓
前端 Cytoscape.js 可视化渲染
  ↓
交互式图谱探索与查询
```

#### 3. AI 问答与内容生成

```
用户提问 → LangGraph Agent
  ↓
检索增强生成（RAG）
  ├─ 图谱检索（Apache AGE）
  ├─ 文档检索（pgvector）
  └─ 联网搜索（可选）
  ↓
流式响应 → WebSocket 推送
```

#### 4. PDF 智能阅读

```
PDF 文件 → pdfjs 渲染
  ├─ Canvas 层：HiDPI 渲染
  ├─ TextLayer：文本选中与复制
  ├─ AnnotationLayer：bbox 标注显示
  └─ 虚拟滚动：IntersectionObserver 优化
```

## 快速开始

### 环境要求

- Python 3.13+
- Node.js 20.19+ / 22.12+ / 24.9+
- PostgreSQL 18+
- Redis 8+

### 后端启动

```bash
# 安装依赖
uv sync --extra service --extra test --extra dev

# 配置文件
cp example.config.yaml dev.config.yaml
# 编辑 dev.config.yaml 配置数据库连接等

# 启动开发服务
uv run -m graphedu service dev

# 运行测试
uv run -m graphedu test run

# 代码检查
uv run ruff check
uv run ruff format
```

### 前端启动

```bash
cd graphedu-ui

# 安装依赖
pnpm install

# 启动开发服务
pnpm dev

# 构建生产版本
pnpm build

# 代码检查
pnpm lint:fix && pnpm format
```

## 部署指南

### Docker 部署（推荐）

```bash
# 配置环境变量
cp example.config.yaml dev.config.yaml
# 编辑配置文件

# 生成 docker/.env
uv run -m graphedu generate env --output docker/.env

# 启动所有服务
cd docker
docker compose -f prod.docker-compose.yaml up -d --build
```

### 手动部署

1. **数据库初始化**：执行 SQL 脚本初始化 PostgreSQL
2. **后端部署**：
   ```bash
   uv sync --extra service
   uv run -m graphedu service prod
   ```
3. **前端部署**：
   ```bash
   cd graphedu-ui
   pnpm build
   # 将 dist/ 目录部署到 Web 服务器
   ```

详细部署文档见 [`docker/README.md`](docker/README.md)

## 测试

```bash
# 后端单元测试
pytest tests/unit

# 后端集成测试
pytest tests/integration

# 前端单元测试
cd graphedu-ui && pnpm test:unit

# 前端 E2E 测试
cd graphedu-ui && pnpm test:e2e
```

详细测试文档见 [`tests/README.md`](tests/README.md)

## 开发文档

- **后端开发指南**：[`CLAUDE.md`](CLAUDE.md)
- **前端开发指南**：[`graphedu-ui/CLAUDE.md`](graphedu-ui/CLAUDE.md)
- **配置系统**：[`graphedu/common/config/README.md`](graphedu/common/config/README.md)
- **异常处理**：[`graphedu/common/exceptions/README.md`](graphedu/common/exceptions/README.md)
- **数据模型**：[`graphedu/common/models/README.md`](graphedu/common/models/README.md)

## 项目特色

### 分层架构

严格的三层分离架构，确保代码可维护性：

```
Controller (API) → Service (业务逻辑) → Mapper (数据访问)
```

### 异步优先

所有 IO 操作使用 async/await，充分利用异步性能优势。

### 权限控制

- **接口权限**：基于注解的接口级权限控制
- **数据权限**：支持 5 种数据范围（全部/自定义/本部门/本部门及子部门/仅本人）
- **动态路由**：根据用户权限动态加载菜单和路由

### 代码生成

内置 CRUD 代码生成器，一键生成完整的前后端代码：

```bash
uv run -m graphedu generate crud <table_name>
```

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

GraphEdu 的开发离不开以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL 工具包和 ORM
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Ant Design Vue](https://antdv.com/) - Vue 3 UI 组件库
- [pdfjs](https://mozilla.github.io/pdf.js/) - Mozilla PDF 渲染引擎
- [LangChain](https://langchain.com/) - AI 应用开发框架
- [Golden Layout](https://golden-layout.com/) - 布局管理器

---

**Built with ❤️ for education**
