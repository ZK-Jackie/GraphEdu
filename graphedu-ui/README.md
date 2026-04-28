# graphedu-ui

GraphEdu 前端 — 基于 Vue 3.5 + TypeScript 5.9 + Vite 8 构建的知识图谱教育平台界面。

## 项目架构

```
src/
├── api/                  # API 请求（按模块：system/、education/）
├── components/           # 公共组件
│   ├── association/     # 关联选择器
│   ├── auth/            # 认证（验证码、Turnstile、扫码登录）
│   ├── dict/            # 字典（DictSelect、DictTag、DictLabel）
│   ├── education/       # 教育组件（学生/教师选择器、学习日历、统计卡片）
│   ├── Header/          # 头部导航（Logo、用户头像、暗色模式、角色切换）
│   ├── mineru/          # 文档查看器（PDF、Markdown）
│   ├── nvl/             # 知识图谱可视化（Neo4j NVL）
│   ├── tag/             # 标签输入（InputTag）
│   └── VueGoldenLayout/ # Golden Layout 多面板布局
├── composables/          # 可组合函数
├── constants/            # 常量定义
├── layout/               # 布局组件
├── locales/              # 国际化翻译（zh/、en/）
├── plugins/              # 插件（i18n、error）
├── router/               # 路由（静态路由 + 动态路由守卫）
├── stores/modules/       # Pinia 状态管理
├── types/                # TypeScript 类型定义
├── utils/                # 工具函数（请求封装、Token、错误处理）
└── views/                # 页面组件
    ├── admin/           # 后台管理
    ├── course/          # 课程相关
    ├── profile/         # 个人中心
    └── error/           # 错误页面
```

### 核心机制

**动态路由**：后端按场景（web / admin / userInfo / mobile）下发菜单，前端通过 `router.addRoute()` 动态注册路由和组件，无需前端硬编码路由表。

**自动导入**：Vue API（`ref`、`computed` 等）和 Ant Design Vue 组件（`<a-table />` 等）无需手动 import。

**国际化**：vue-i18n 11.3，中/英双语，翻译文件按功能模块组织在 `locales/` 下。

## 命令

| 命令 | 说明 |
|:---|:---|
| `pnpm install` | 安装依赖 |
| `pnpm dev` | 启动开发服务（端口 8001） |
| `pnpm build` | 类型检查 + 构建生产版本 |
| `pnpm build-only` | 仅构建，跳过类型检查 |
| `pnpm preview` | 预览生产构建 |
| `pnpm type-check` | 运行 vue-tsc 类型检查 |
| `pnpm lint` | 代码检查（oxlint） |
| `pnpm lint:fix` | 代码检查并自动修复 |
| `pnpm format` | 代码格式化（oxfmt） |
| `pnpm format:check` | 检查格式是否符合规范 |
| `pnpm test:unit` | 运行单元测试（Vitest） |
| `pnpm test:e2e` | 运行 E2E 测试（Playwright） |

## 配置项

环境变量通过 `.env.development`（开发）和 `.env.production`（生产）配置。

### 应用

| 变量 | 说明 | 开发默认值 | 生产默认值 |
|:---|:---|:---|:---|
| `VITE_APP_BASE_URL` | 应用部署路径 | `/` | `/` |
| `VITE_APP_TITLE` | 页面标题 | `GraphEdu-Dev` | `GraphEdu` |

### API

| 变量 | 说明 | 开发默认值 | 生产默认值 |
|:---|:---|:---|:---|
| `VITE_API_BASE_URL` | API 基础路径 | `/dev-api`（代理到 `localhost:8000`） | `/api` |
| `VITE_API_TIMEOUT` | 请求超时（ms） | `300000`（5 分钟） | `30000`（30 秒） |
| `VITE_API_REQUEST_INTERVAL` | 防重复提交间隔（ms） | `1000` | `1000` |
| `VITE_API_REQUEST_INTERVAL_DATA_THRESHOLD` | 防重复提交数据量阈值（字节） | `5242880`（5 MB） | `5242880` |

### 构建

| 变量 | 说明 | 可选值 |
|:---|:---|:---|
| `VITE_BUILD_COMPRESS` | 构建压缩方式 | `gzip`、`brotli`、`brotli,gzip` |

### 功能开关

| 变量 | 说明 | 开发默认值 | 生产默认值 |
|:---|:---|:---|:---|
| `VITE_LOGIN_QRCODE` | 启用扫码登录 | `false` | `true` |
| `VITE_MOCK_ENABLED` | 启用 Mock 数据 | `false` | — |

### 备案信息

| 变量 | 说明 |
|:---|:---|
| `VITE_ICP_LICENSE` | ICP 备案号 |
| `VITE_PSA_LICENSE` | 公安备案号 |

### 开发代理

开发环境下 `VITE_API_BASE_URL=/dev-api` 由 Vite 代理到后端 `http://localhost:8000`，配置在 `vite.config.ts` 的 `server.proxy` 中。
