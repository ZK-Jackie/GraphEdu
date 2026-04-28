# CLAUDE.md

> 本文件为 Claude Code 在本仓库工作时提供指导。

---

## 快速参考

| 场景           | 命令                           |
| -------------- | ------------------------------ |
| 安装依赖       | `pnpm install`                 |
| 启动开发服务   | `pnpm dev`（端口 8001）        |
| 类型检查       | `pnpm type-check`              |
| 构建生产版本   | `pnpm build`                   |
| 代码检查并修复 | `pnpm lint:fix && pnpm format` |

---

## 必须遵从

### 环境要求

- **包管理器**：必须使用 `pnpm`
- **Node.js**：`^20.19.0 || ^22.12.0 || ^24.9.0`

### Vue 组件规范

- 使用 `<script setup>` + Composition API
- Props 必须定义类型：`defineProps<T>()`
- Emits 必须定义类型：`defineEmits<T>()`
- 组件文件名使用 PascalCase

### TypeScript 规范

- 类型导入使用 `import type { ... }`
- 优先避免 `any`，优先使用 `unknown` 或具体类型（某些情况下可用）
- 复杂函数必须显式声明返回值类型

### 样式规范

- 优先使用 Tailwind CSS 原子类
- 组件样式使用 `<style scoped>`
- 可使用 `@apply` 运用 Tailwind CSS 样式，使用前需要引入 `@reference "#main.css"`

```vue
<style scoped>
@reference "#main.css"

  .card-wrapper {
  @apply rounded-lg shadow-md p-4 bg-white;
}
</style>
```

### 开发流程

**编写完成后，务必运行 lint 检查并修正问题**：

```bash
pnpm lint:fix && pnpm format
```

---

## 项目概览

**GraphEdu 前端**：基于知识图谱的教育平台界面。

- **框架**：Vue 3.5 + TypeScript 5.9 + Vite 7
- **UI**：Ant Design Vue 4.2 + Tailwind CSS 4.1
- **状态**：Pinia 3
- **路由**：Vue Router 4.6（部分静态路由 + 后端传入的动态路由）
- **国际化**：vue-i18n 11.3（中/英双语）

后端文档见 `../CLAUDE.md`

---

## 核心架构

### 动态路由系统

**多场景架构**：

| 场景       | 用途               |
| ---------- | ------------------ |
| `web`      | 学生学习、课程浏览 |
| `admin`    | 后台管理           |
| `userInfo` | 个人中心           |
| `mobile`   | 移动端（预留）     |

**路由流程**：

```
登录 → Token 存储
  ↓
GET /info → 获取用户权限
  ↓
GET /menus?scene=xxx → 按场景获取菜单
  ↓
functionStore.loadMenuDataByScene(scene)
  ↓
router.addRoute() 动态注册
```

**路由守卫**：`router/guard.ts`
**动态路由加载**：`stores/modules/function.ts`

### 国际化（i18n）

项目使用 `vue-i18n` 实现 Composition API 模式的国际化，配置文件位于 `plugins/i18n.ts`。

**语言文件组织**：

```
src/locales/
├── zh/                    # 中文翻译
│   ├── common.json       # 通用文本（操作按钮、状态提示、表单标签）
│   ├── header.json       # 头部导航
│   ├── settings.json     # 设置页面（语言、时区、时间格式）
│   ├── system.json       # 系统管理（用户、角色、部门、字典、功能、日志、任务）
│   ├── education.json    # 教育模块（门户、学生、教师、课程、章节、书籍）
│   └── learning.json     # 学习模块（课程标签、学习状态、相对时间）
└── en/                    # 英文翻译（结构同上）
```

**命名空间规则**：每个 JSON 文件名自动成为顶级命名空间，例如 `common.json` → `common.*`，`system.json` → `system.*`。

**翻译 key 层级约定**：

```jsonc
// system.json — 按功能模块二级分组
{
  "user": { "title": "用户管理", "nickName": "用户昵称" },
  "role": { "title": "角色管理", "roleName": "角色名称" },
  "dict": { "title": "字典管理", "dictName": "字典名称" },
}
// 使用：$t('system.user.title')、$t('system.role.title')
```

```jsonc
// common.json — 扁平结构，存放跨模块复用的通用文本
{
  "search": "搜索",
  "reset": "重置",
  "addSuccess": "新增成功",
}
// 使用：$t('common.search')、$t('common.addSuccess')
```

**使用方式**：

```vue
<!-- 模板中使用 $t() -->
<span>{{ $t('common.search') }}</span>

<!-- 脚本中使用 useI18n() -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const title = t('system.user.title')
</script>
```

**语言切换**：通过 `stores/modules/app.ts` 的 `updateLocale()` 方法，自动同步到 localStorage、i18n 实例和请求头 `Accept-Language`。

**添加翻译的规范**：

1. 在 `zh/` 和 `en/` 对应文件中同时添加，保持双语同步
2. 通用文本放 `common.json`，按功能模块分组放对应文件
3. key 使用 camelCase 命名，避免使用点号等特殊字符
4. 新增功能模块时，在 `zh/` 和 `en/` 下新建对应 JSON 文件即可，无需修改初始化代码

### 布局系统

| 布局                  | 用途           | 位置                          |
| --------------------- | -------------- | ----------------------------- |
| `CommonLayout`        | 首页、公开页面 | `layout/CommonLayout/`        |
| `WorkbenchLayout`     | 工作台（管理） | `layout/WorkbenchLayout/`     |
| `StudentCourseLayout` | 学生课程学习   | `layout/StudentCourseLayout/` |
| `TeacherCourseLayout` | 教师课程管理   | `layout/TeacherCourseLayout/` |
| `TablePageLayout`     | 通用表格列表页 | `layout/TablePageLayout.vue`  |
| `CommonPageLayout`    | 通用页面容器   | `layout/CommonPageLayout.vue` |

---

## 项目结构

```
src/
├── api/                  # API 请求（按模块：system/、education/）
├── components/           # 公共组件
│   ├── association/     # 关联选择器
│   ├── auth/            # 认证组件（验证码、Turnstile、扫码登录）
│   ├── dict/            # 字典组件（DictSelect、DictTag、DictLabel、DictRadio、DictSwitch）
│   ├── education/       # 教育组件（学生/教师选择器、学习日历、统计卡片）
│   ├── Header/          # 头部导航组件（Logo、用户头像、暗色模式、角色切换）
│   ├── mineru/          # 文档查看器（PDF、Markdown、MinerU）
│   ├── nvl/             # 知识图谱可视化（Neo4j NVL）
│   ├── tag/             # 标签输入（InputTag）
│   └── VueGoldenLayout/ # Golden Layout 多面板布局
├── composables/          # 可组合函数
│   ├── useAdaptiveTable.ts      # 自适应表格高度（ResizeObserver）
│   ├── useAsyncTaskPolling.ts    # 异步任务进度轮询
│   ├── useBreakpoints.ts        # 响应式断点（mobile/tablet/desktop）
│   ├── usePaginationQuery.ts    # 分页参数与 URL 同步
│   ├── useResourceProgress.ts   # 资料阅读进度上报
│   └── useTime.ts               # UTC 时间转换与相对时间
├── constants/            # 常量定义
│   └── process.ts       # 异步任务状态（PENDING/RUNNING/COMPLETED/ERROR）
├── layout/               # 布局组件（见上方布局系统）
├── locales/              # 国际化翻译文件（见上方 i18n 章节）
├── plugins/              # 插件（i18n、error）
├── router/               # 路由配置
│   ├── index.ts         # 静态路由
│   └── guard.ts         # 路由守卫
├── stores/modules/       # Pinia 状态模块
│   ├── app.ts           # 应用状态（侧边栏、暗色模式、语言、时区）
│   ├── chat.ts          # AI 聊天（会话、流式消息）
│   ├── dict.ts          # 字典缓存
│   ├── function.ts      # 功能菜单与动态路由
│   ├── learning.ts      # 学习状态（我的课程、进度）
│   ├── quote.ts         # 文本引用管理
│   ├── tab.ts           # 标签页状态
│   ├── teaching.ts      # 教学状态（当前课程、章节树、知识图谱）
│   └── user.ts          # 用户状态（Token、角色、多角色切换）
├── types/                # TypeScript 类型
│   ├── api/             # API 请求/响应类型
│   ├── stores/          # Store 状态类型
│   ├── components/      # 组件 Props/Emits 类型
│   └── composables/     # Composable 返回值类型
├── utils/                # 工具函数
│   ├── request/         # Axios 封装（Token、语言、防重复提交）
│   ├── errors.ts        # 错误码映射与消息提取
│   ├── message.ts       # 统一消息提示
│   ├── storage.ts       # localStorage 封装
│   ├── string.ts        # 字符串工具
│   └── token.ts         # Token 管理
└── views/                # 页面组件
    ├── admin/           # 后台管理页面
    ├── course/          # 课程相关页面
    ├── error/           # 错误页面（404）
    ├── profile/         # 个人中心
    └── LoginView.vue / RegisterView.vue  # 登录/注册
```

---

## 关键约定

### 自动导入

无需手动 import：

- **Vue API**：`ref`、`computed`、`watch` 等
- **Ant Design Vue 组件**：`<a-table />`、`<a-form />` 等

类型定义在 `types/generated/`（无需手动修改）。

### 图标系统

```vue
<!-- Ant Design 图标，需要在 script 中引入组件 -->
<SearchOutlined />

<!-- 自定义 SVG 图标 -->
<SvgIcon icon="custom-icon" />
```

自定义 SVG 图标详见 `components/SvgIcon/README.md`。

### 字典组件

自动从后端加载字典数据：

```vue
<DictSelect v-model="form.status" dict-type="sys_normal_disable" />
<DictTag :value="row.status" dict-type="sys_normal_disable" />
```

### 请求封装

使用 `utils/request/`，自动处理：

- Bearer Token
- Accept-Language
- 防重复提交
- 统一错误处理

```typescript
import request from '@/utils/request'

export function getUserList(params: UserQuery) {
  return request<Response>({
    url: '/system/user/list',
    method: 'get',
    params,
  })
}
```

跳过 Token：`headers: { skipToken: true }`

### 常量

| 常量                  | 位置                   | 用途              |
| --------------------- | ---------------------- | ----------------- |
| `ProcessStatus`       | `constants/process.ts` | 异步任务状态枚举  |
| `LocalDarkModeKey` 等 | `constants.ts`         | localStorage 键名 |

### Composables 使用示例

```typescript
// 分页查询与 URL 同步
const { queryParams, resetPage, resetAll, fetch } = usePaginationQuery(
  { page: 1, size: 10, userName: undefined },
  getList
)

// 自适应表格高度
const tableScrollY = ref(200)
const { tableScrollY: scrollY } = useAdaptiveTable({
  containerRef: containerEl,
  subtractRefs: [searchFormEl, paginationEl],
  minHeight: 200,
})

// 时间格式化（自动响应语言和时区变化）
const { formatUtcTime, fromNow } = useTime()
```

---

## 开发指南

### 添加新页面

1. 在 `views/` 创建组件
2. 路由由后端菜单权限动态加载，无需手动配置
3. 如需权限控制，在后端配置菜单权限

### 添加新 API

1. 在 `types/api/` 定义类型
2. 在 `api/` 对应模块创建函数

### 添加新状态

在 `stores/modules/` 使用 Composition API 风格：

```typescript
export const useMyStore = defineStore('my', () => {
  const data = ref<string>('')
  const getData = computed(() => data.value)

  function setData(val: string) {
    data.value = val
  }

  return { data, getData, setData }
})
```

### 添加新翻译

1. 在 `src/locales/zh/` 和 `src/locales/en/` 对应文件中添加翻译条目
2. 如是新功能模块，新建同名 JSON 文件（无需修改初始化代码）
3. 保持中英文条目一一对应

---

## 配置与工具

### 环境变量

见 `.env.development` / `.env.production`

- 开发环境 API 代理：`/dev-api` → `http://localhost:8000`
- 开发服务器端口：`8001`

### 代码格式化

配置见 `.oxfmtrc.json`
