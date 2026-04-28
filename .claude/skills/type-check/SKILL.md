---
name: type-check
description: >-
  前端 TypeScript 类型检查和修复工具。运行 vue-tsc 检查 graphedu-ui 前端类型错误，分析并自动修复。触发场景：(1) 用户要求运行 type-check、检查类型、修复类型错误；(2) 用户提到 TypeScript 错误或前端类型问题；(3) 前端构建失败需要修复类型问题；(4) 后端模型变更后需要验证前端类型。对数据模型不匹配的错误，读取后端 VO/DTO 源文件确定正确类型后修复前端。支持安全自动修复，对有歧义的修改会先询问用户。
---

# 前端 TypeScript 类型检查和修复

## 快速开始

```bash
cd graphedu-ui && pnpm type-check
```

## 工作流程

### Step 1: 运行类型检查

执行 `cd graphedu-ui && pnpm type-check`，捕获完整输出。

- **无错误**: 报告成功并结束。
- **有错误**: 继续步骤 2。

### Step 2: 错误分类

解析每个错误，按以下类别归类：

| 类别 | 识别方式 | 修复策略 |
|------|---------|---------|
| **A. 数据模型不匹配** | 错误涉及 `types/api/` 中的 VO/DTO 接口字段（缺失/类型错误） | 读后端 VO/DTO，修正前端类型 |
| **B. 导入错误** | TS2307/TS2305: "cannot find module" / "has no exported member" | 修正导入路径或补充导出 |
| **C. Vue 组件** | 错误在 `.vue` 文件中，涉及 `defineProps`/`defineEmits` | 调整组件类型定义 |
| **D. API 响应类型** | 错误在 `api/` 文件中，涉及 `Promise<ResponseType<...>>` | 对齐 API 函数签名 |
| **E. 通用 TS** | 缺失属性、可空访问、类型断言等 | 按上下文修复 |

详细错误模式匹配见 [references/error-patterns.md](references/error-patterns.md)。

### Step 3: 按类别修复

#### A. 数据模型不匹配

1. 从错误信息识别前端接口名（如 `UserDetailVO`）和问题字段。
2. 映射到后端文件：
   - `types/api/system/*.ts` → `graphedu/common/models/vo/systemv2/*.py`（VO）或 `dto/systemv2/*.py`（DTO）
   - `types/api/education/*.ts` → `vo/educationv2/*.py` 或 `dto/educationv2/*.py`
3. 读取后端 Python 文件，应用类型映射修正前端接口。

**类型映射（Python → TypeScript）**:

| Python | TypeScript |
|--------|-----------|
| `str` | `string` |
| `int` | `number` |
| `float` | `number` |
| `bool` | `boolean` |
| `datetime` | `string` |
| `list[T]` | `T[]` |
| `dict` | `Record<string, unknown>` |
| `T \| None` | 字段添加 `?` 可选标记 |

字段名转换: Python `snake_case` → TypeScript `camelCase`。

#### B-D. 其他类别

- 导入错误: 修正路径（前端使用 `@/` 别名映射到 `src/`），补充缺失的 `export`，使用 `import type` 语法。
- Vue 组件: 更新 `defineProps<T>()` 或 `defineEmits<T>()` 类型定义。
- API 响应: 对齐 `Promise<ResponseType<PageResponse<XxxVO>>>` 或 `Promise<ResponseType<XxxVO>>` 包装。

### Step 4: 歧义判断 — 何时询问用户

**以下情况必须询问用户后再操作**:

1. **多种有效修复方案**: 如字段添加 `?:`（可选）还是 `:`（必选），后端 `default=None` 但字段语义重要。
2. **破坏性变更风险**: 修改一个类型会影响多个文件（如 `string` → `number`）。
3. **后端本身不明确**: 后端 VO/DTO 有歧义（如 `list` 无泛型参数），需用户确认意图。
4. **大量错误**: 单次超过 10 个错误时，先展示汇总再让用户决定优先处理顺序。

### Step 5: 验证

修复后重新运行 `cd graphedu-ui && pnpm type-check`，确认零错误。

若修复引入新错误，回到步骤 2 迭代处理。

## 关键约定

- 使用 `import type { ... }` 进行纯类型导入
- 前端字段使用 camelCase，后端使用 snake_case（Pydantic alias_generator 自动转换）
- VO/DTO 接口名前后端一致（如 `UserDetailVO`）
- `ResponseType<T>` 和 `PageResponse<T>` 定义在 `@/types/api/common.ts`
- 自动导入的 Vue API（ref, computed, watch）和 Ant Design Vue 组件无需手动导入
