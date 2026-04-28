# MinerU Vue 组件

基于 [MinerU](https://github.com/opendatalab/MinerU) 前端移植的 Vue 3 + TypeScript PDF 查看、标注和 Markdown 对比渲染组件套件。

---

## 目录

- [功能概览](#功能概览)
- [目录结构](#目录结构)
- [实现原理](#实现原理)
  - [PDF 渲染与标注层](#pdf-渲染与标注层)
  - [Markdown 渲染](#markdown-渲染)
  - [双向同步机制](#双向同步机制)
  - [状态管理](#状态管理)
- [架构设计](#架构设计)
- [依赖说明](#依赖说明)
- [快速上手](#快速上手)
- [完整 API](#完整-api)
- [数据格式与转换](#数据格式与转换)
- [标注颜色配置](#标注颜色配置)
- [常见问题](#常见问题)

---

## 功能概览

| 功能            | 说明                                                                     |
| --------------- | ------------------------------------------------------------------------ |
| PDF 显示        | 基于定制版 PDF.js，嵌入 iframe，支持缩放、翻页、搜索                     |
| 标注层渲染      | 在 PDF 页面叠加 Canvas 绘制识别框，区分标题/正文/表格/图片/公式等        |
| Markdown 渲染   | 支持 GFM、行内/块级数学公式（KaTeX）、代码高亮、表格、图片               |
| PDF-MD 对比视图 | 左右分栏联动，PDF 翻页自动滚动 MD，MD 滚动自动切换 PDF 页                |
| 预览/编辑模式   | MD 面板支持实时预览和原文编辑切换                                        |
| 全屏模式        | 可将 MD 面板展开为全屏                                                   |
| 双后端兼容      | 兼容 MinerU pipeline 和 VLM 两种后端的 `middle.json` / `model.json` 输出 |

---

## 目录结构

```
src/components/mineru/
├── index.ts                    # 统一导出入口
├── MinerUViewer.vue            # 主入口组件（推荐使用）
├── example.vue                 # 完整使用示例
├── README.md                   # 本文档
├── docs/                       # MinerU 官方输出格式文档
│   └── output_files.md
│
├── pdf-viewer/
│   └── PdfViewer.vue           # PDF 查看器（iframe + postMessage）
│
├── md-viewer/
│   ├── MdViewer.vue            # Markdown 查看器容器（滚动同步、模式切换）
│   └── UrlMarkdown.vue         # Markdown → HTML 渲染器（marked + KaTeX）
│
├── pdf-extraction/
│   └── PdfExtraction.vue       # PDF-MD 双栏对比视图（协调者）
│
├── stores/
│   └── mdStore.ts              # Pinia Store，管理 MD 内容与锚点
│
├── types/
│   └── index.ts                # 所有 TypeScript 类型 + 工具函数
│
└── constants/
    └── index.ts                # 颜色表、事件名、常量
```

---

## 实现原理

### PDF 渲染与标注层

**渲染架构**

PDF 通过 `<iframe>` 嵌入定制版 PDF.js Viewer（位于 `public/pdfjs-dist/web/`）运行。定制版在原版基础上修改了以下文件：

- **`viewer.mjs`**：新增 `window.parent.postMessage` 调用，将页码变化事件通知父页面
- **`layer.js`**：监听 `window.addEventListener('message', ...)` 接收父页面指令，实现标注层 Canvas 绘制

**主 → iframe 消息协议**（父页面发出）

| type                   | data                                    | 说明                           |
| ---------------------- | --------------------------------------- | ------------------------------ |
| `initExtractLayerData` | `Record<pageIdx, {bboxes: BboxItem[]}>` | 初始化所有页标注数据           |
| `pageChange`           | `number`（0-based 页码）                | 命令 layer.js 在指定页重绘标注 |
| `setPage`              | `number`（1-based 页码，裸数字）        | 命令 PDF.js 跳转到指定页       |
| `title`                | `string`                                | 设置查看器标题栏文字           |

**iframe → 主 消息协议**（PDF.js 发出）

| 字段               | 类型     | 说明                                                |
| ------------------ | -------- | --------------------------------------------------- |
| `status: 'loaded'` | —        | PDF 初始化完成，此后才可发送 `initExtractLayerData` |
| `pageNum`          | `number` | 页面变化（0-based），用于触发标注层切换             |
| `pageNumDetail`    | `number` | 页面变化（1-based，更精确），用于驱动 MD 同步       |
| `error`            | `string` | 浏览器版本过低等错误                                |

**标注层绘制**（`layer.js`）

```
收到 initExtractLayerData
  └─ 全局缓存 window.pdfExtractData
  └─ 调用 renderExtractLayer(data, 0, scale)

收到 pageChange(n)
  └─ 调用 renderExtractLayer(data, n, scale)
  └─ 在对应页面的 .annotationLayer 中动态创建 <canvas id="extractLayer">
  └─ 逐框绘制：边框动画（0→1 进度）→ 填充矩形
```

bbox 坐标为**绝对像素坐标 [x0, y0, x1, y1]**，layer.js 再乘以当前缩放比例 scale。

---

### Markdown 渲染

`UrlMarkdown.vue` 使用 **marked** 解析 Markdown，处理流程：

```
原始 Markdown 字符串
  └─ marked.parse()
       ├─ GFM 语法（表格、删除线、任务列表）
       └─ marked-katex-extension（$...$ 行内公式 / $$...$$ 块级公式 → KaTeX HTML）
  └─ DOMPurify.sanitize()
       └─ 白名单过滤（保留 KaTeX SVG/MathML 元素）
  └─ v-html 渲染到 DOM
```

**锚点机制**

`mdStore.allMdContentWithAnchor` 在每页内容前插入不可见锚点：

```html
<span id="md-anchor-0" style="display:none;"></span>

# 第一页内容...

<span id="md-anchor-1" style="display:none;"></span>

# 第二页内容...
```

锚点 id 格式为 `md-anchor-{pageIndex}`（0-based），用于精准定位。

---

### 双向同步机制

```
┌─────────────────────────────────────────────────────────┐
│                   PdfExtraction（协调者）                 │
│                                                          │
│  pdfState.page (reactive)                                │
│       │ watch                  CustomEvent               │
│       ▼                    MD_DRIVE_PDF {detail: idx}    │
│  PdfViewer.setPage(n)  ◄────────────────  MdViewer       │
│       │ emit pageChange                       ▲           │
│       ▼                                       │           │
│  pdfState.page = n                     scroll event      │
│       │ prop :curPage                 (isAutoScrolling   │
│       ▼                                 = false 时)       │
│  MdViewer.scrollToPage(n-1)  ──────────────────►         │
│       └─ 设置 isAutoScrolling=true（400ms）               │
└─────────────────────────────────────────────────────────┘
```

**防循环机制**  
PDF 驱动 MD 滚动时，`MdViewer` 设置 `isAutoScrolling = true`，在此期间 scroll 事件不会反向触发 `MD_DRIVE_PDF`，400ms 后自动重置，防止 PDF→MD→PDF 循环触发。

**事件常量**

| 常量           | 值             | 用途               |
| -------------- | -------------- | ------------------ |
| `MD_DRIVE_PDF` | `'mdDrivePdf'` | MD 滚动 → PDF 跳页 |

---

### 状态管理

`mdStore`（Pinia）集中管理 Markdown 内容，使两个独立组件解耦：

```
PdfExtraction
  └─ watch(markdownPages) → mdStore.setMdContent(pages)
  └─ watch(layerData)     → mdStore.setLayerData(data)

MdViewer
  └─ computed allMdContentWithAnchor ← mdStore
  └─ computed allMdContent           ← mdStore
  └─ computed displayType            ← mdStore
```

---

## 架构设计

```
MinerUViewer（主入口）
  └─ PdfExtraction（容器 / 协调者）
       ├─ [左] PdfViewer
       │         ├─ <iframe src="pdfjs-dist/web/viewer.html?file=...">
       │         │       └─ viewer.mjs + layer.js（定制 PDF.js）
       │         └─ postMessage 双向通信桥
       │
       └─ [右] MdViewer
                 ├─ 工具栏（预览/编辑切换、全屏）
                 ├─ [预览模式] UrlMarkdown
                 │       └─ marked + KaTeX + DOMPurify
                 └─ [编辑模式] <a-textarea>
```

**数据流向**

```
外部数据（pdfUrl / markdownContent / layerData）
  │
  ▼
MinerUViewer → TaskInfo → PdfExtraction
                              │
         ┌────────────────────┤
         │                    │
         ▼                    ▼
    PdfViewer            mdStore（Pinia）
    - iframe URL          - mdContent[]
    - layerData           - displayType
    - postMessage ──►     - allMdContentWithAnchor
         ▲          layer.js
         │
    pageNumDetail ──► emit('pageChange') ──► pdfState.page ──► MdViewer(:curPage)
```

---

## 依赖说明

| 包                       | 版本  | 用途                 |
| ------------------------ | ----- | -------------------- |
| `marked`                 | ^15   | Markdown 解析        |
| `marked-katex-extension` | ^5    | KaTeX 数学公式扩展   |
| `katex`                  | ^0.16 | 数学公式渲染引擎     |
| `dompurify`              | ^3    | HTML 净化，防 XSS    |
| `@types/katex`           | ^0.16 | KaTeX 类型定义       |
| `pinia`                  | ^3    | 状态管理（项目已有） |
| `ant-design-vue`         | ^4    | UI 组件（项目已有）  |

**安装**

```bash
pnpm add katex marked-katex-extension
pnpm add -D @types/katex
```

**静态资源**（`public/pdfjs-dist/`）

定制版 PDF.js，直接放置在 `public` 目录下由 Vite 原样输出：

```
public/pdfjs-dist/
├── build/
│   └── pdf.mjs          # PDF.js 核心库
└── web/
    ├── viewer.html       # 查看器页面（主入口）
    ├── viewer.mjs        # 查看器应用逻辑（定制，新增 postMessage）
    ├── layer.js          # 标注层逻辑（定制新增）
    ├── viewer.css
    ├── custom.css        # 自定义样式
    ├── custom.js         # 自定义脚本
    ├── cmaps/            # 字符映射表
    └── standard_fonts/   # 标准字体
```

---

## 快速上手

### 最简用法

```vue
<template>
  <!-- 容器必须有明确高度 -->
  <div style="height: 800px;">
    <MinerUViewer pdf-url="/path/to/file.pdf" :markdown-content="markdownPages" />
  </div>
</template>

<script setup lang="ts">
import MinerUViewer from '@/components/mineru'

// 每个元素对应 PDF 的一页（index 与 0-based 页码对应）
const markdownPages = [
  '# 第一页\n\n这是第一页的正文内容。',
  '## 第二页\n\n支持 $E=mc^2$ 行内公式和\n\n$$\\int_a^b f(x)dx$$\n\n块级公式。',
]
</script>
```

### 带标注数据

```vue
<template>
  <div style="height: 800px;">
    <MinerUViewer pdf-url="/path/to/file.pdf" :markdown-content="markdownPages" :layer-data="layerData" />
  </div>
</template>

<script setup lang="ts">
import MinerUViewer from '@/components/mineru'
import type { ExtractLayerData } from '@/components/mineru'

const markdownPages = ['# Page 1', '# Page 2']

// bbox 为绝对像素坐标 [x0, y0, x1, y1]
const layerData: ExtractLayerData = {
  0: {
    preproc_blocks: [
      { type: 'title', bbox: [52, 62, 294, 83] },
      { type: 'text', bbox: [52, 90, 294, 200] },
    ],
    discarded_blocks: [{ type: 'header', bbox: [52, 10, 560, 30] }],
  },
  1: {
    preproc_blocks: [{ type: 'table', bbox: [52, 100, 560, 300] }],
  },
}
</script>
```

### 从 MinerU 输出文件构建数据

#### Pipeline 后端（`_backend: "pipeline"`）

```typescript
import { pipelineMiddleToLayerData } from '@/components/mineru'

// 直接传入 middle.json 的 pdf_info 数组
const layerData = pipelineMiddleToLayerData(middleJson.pdf_info)
```

#### VLM 后端（`_backend: "vlm-transformers"` 等）

```typescript
import { vlmModelJsonToLayerData } from '@/components/mineru'

// VLM model.json bbox 为 0-1 相对坐标，需提供每页像素尺寸
const pageSizes: Array<[number, number]> = middleJson.pdf_info.map((p: any) => [p.page_size[0], p.page_size[1]])
const layerData = vlmModelJsonToLayerData(modelJson, pageSizes)
```

### 独立使用子组件

```vue
<template>
  <div class="h-full grid grid-cols-2">
    <PdfViewer ref="pdfRef" pdf-url="/file.pdf" :layer-data="layerData" @page-change="onPageChange" />
    <MdViewer :cur-page="currentPage" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { PdfViewer, MdViewer, useMdStore } from '@/components/mineru'
import type { PDFViewerState } from '@/components/mineru'

const pdfRef = ref<InstanceType<typeof PdfViewer>>()
const currentPage = ref(1)
const mdStore = useMdStore()

onMounted(() => {
  mdStore.setMdContent(['# 第一页内容', '# 第二页内容'])
})

function onPageChange(state: PDFViewerState) {
  currentPage.value = state.page
}

// 手动跳页
function jumpTo(page: number) {
  pdfRef.value?.setPage(page)
}
</script>
```

---

## 完整 API

### `MinerUViewer` Props

| 属性              | 类型               | 必填 | 默认值 | 说明                                            |
| ----------------- | ------------------ | ---- | ------ | ----------------------------------------------- |
| `pdfUrl`          | `string`           | ✅   | —      | PDF 文件 URL                                    |
| `markdownContent` | `string[]`         | ❌   | `[]`   | 每页 Markdown 内容（index 与 0-based 页码对应） |
| `layerData`       | `ExtractLayerData` | ❌   | `{}`   | 标注数据                                        |

---

### `PdfViewer` Props / Events / Methods

**Props**

| 属性        | 类型               | 默认值 | 说明                              |
| ----------- | ------------------ | ------ | --------------------------------- |
| `pdfUrl`    | `string`           | —      | PDF URL，变化时重新加载           |
| `curPage`   | `number`           | `1`    | 当前页码（1-based），变化时跳转   |
| `layerData` | `ExtractLayerData` | `{}`   | 标注数据，变化时重新发送给 iframe |

**Events**

| 事件         | 载荷                              | 说明                      |
| ------------ | --------------------------------- | ------------------------- |
| `pageChange` | `PDFViewerState { page: number }` | 用户翻页时触发（1-based） |
| `loaded`     | —                                 | PDF 加载完成              |

**Methods**（通过模板 ref 调用）

| 方法      | 签名                     | 说明                    |
| --------- | ------------------------ | ----------------------- |
| `setPage` | `(page: number) => void` | 跳转到指定页（1-based） |

---

### `MdViewer` Props

| 属性      | 类型     | 默认值 | 说明                                          |
| --------- | -------- | ------ | --------------------------------------------- |
| `curPage` | `number` | `1`    | 当前页码（1-based），变化时自动滚动到对应锚点 |

内容通过 `useMdStore().setMdContent()` 注入，不作为 prop 传入。

---

### `UrlMarkdown` Props

| 属性            | 类型     | 默认值 | 说明                                |
| --------------- | -------- | ------ | ----------------------------------- |
| `content`       | `string` | `''`   | 完整 Markdown 字符串（含锚点 HTML） |
| `markdownClass` | `string` | `''`   | 附加到渲染容器的 CSS 类名           |

---

### `useMdStore()` Store API

```typescript
import { useMdStore } from '@/components/mineru'
const mdStore = useMdStore()
```

**State**

| 属性          | 类型                  | 说明                   |
| ------------- | --------------------- | ---------------------- |
| `mdContent`   | `string[]`            | 各页 Markdown 原始内容 |
| `displayType` | `'preview' \| 'code'` | 当前显示模式           |

**Getters（computed）**

| 属性                     | 类型     | 说明                                                       |
| ------------------------ | -------- | ---------------------------------------------------------- |
| `allMdContentWithAnchor` | `string` | 所有页内容拼接，每页前插入锚点 `<span id="md-anchor-{i}">` |
| `allMdContent`           | `string` | 所有页内容拼接（无锚点，用于编辑模式）                     |

**Actions**

| 方法             | 签名                                  | 说明                   |
| ---------------- | ------------------------------------- | ---------------------- |
| `setMdContent`   | `(content: string[]) => void`         | 设置各页 Markdown 内容 |
| `setDisplayType` | `(type: 'preview' \| 'code') => void` | 切换预览/编辑模式      |
| `setLayerData`   | `(data: ExtractLayerData) => void`    | 存储标注数据（备用）   |
| `reset`          | `() => void`                          | 重置所有状态           |

---

## 数据格式与转换

### `ExtractLayerData`（组件直接使用的格式）

```typescript
type ExtractLayerData = Record<number, ExtractLayerItem>
// key 为 0-based 页码

interface ExtractLayerItem {
  preproc_blocks?: Bbox[] // 识别出的内容块
  discarded_blocks?: Bbox[] // 丢弃块（页眉/页脚/页码等）
}

interface Bbox {
  type: BboxType // 块类型（见下方类型表）
  bbox: [number, number, number, number] // 绝对像素坐标 [x0, y0, x1, y1]
  color?: BboxColor // 可选，缺省时自动从颜色表映射
}
```

> ⚠️ **坐标系说明**：`bbox` 必须是**绝对像素坐标**。
>
> - Pipeline `middle.json` 中的 bbox 已经是像素坐标，可直接使用。
> - VLM `model.json` 中的 bbox 是 0-1 相对坐标，必须通过 `vlmModelJsonToLayerData()` 转换。

---

### 工具函数

#### `pipelineMiddleToLayerData(pdfInfo)` — Pipeline 后端

```typescript
import { pipelineMiddleToLayerData } from '@/components/mineru'

const layerData = pipelineMiddleToLayerData(middleJson.pdf_info)
```

从 `_backend: "pipeline"` 的 `middle.json` 中提取每页的 `preproc_blocks` 和 `discarded_blocks`。

#### `vlmModelJsonToLayerData(modelJson, pageSizes)` — VLM 后端

```typescript
import { vlmModelJsonToLayerData } from '@/components/mineru'

const pageSizes: Array<[number, number]> = middleJson.pdf_info.map((p) => [p.page_size[0], p.page_size[1]])
const layerData = vlmModelJsonToLayerData(modelJson, pageSizes)
```

将 VLM `model.json` 中的 0-1 相对坐标 × pageSize 转换为绝对像素坐标。

---

### 支持的 BboxType 类型

| 类型                                                 | 来源         | 说明              | 标注颜色 |
| ---------------------------------------------------- | ------------ | ----------------- | -------- |
| `title`                                              | pipeline/VLM | 标题              | 蓝紫色   |
| `text` / `plain_text`                                | pipeline     | 正文文本          | 粉色     |
| `image` / `figure` / `image_body`                    | pipeline/VLM | 图片本体          | 绿色     |
| `image_caption` / `figure_caption`                   | pipeline/VLM | 图片描述          | 青色     |
| `image_footnote`                                     | pipeline/VLM | 图片脚注          | 紫罗兰   |
| `table` / `table_body`                               | pipeline/VLM | 表格本体          | 黄色     |
| `table_caption`                                      | pipeline/VLM | 表格描述          | 青色     |
| `table_footnote`                                     | pipeline/VLM | 表格脚注          | 紫罗兰   |
| `formula` / `isolate_formula` / `interline_equation` | pipeline     | 行间公式          | 橙色     |
| `embedding` / `isolated`                             | pipeline     | 行内/行间公式别名 | 橙色     |
| `formula_caption`                                    | pipeline     | 公式编号          | 深橙色   |
| `code` / `code_body`                                 | VLM          | 代码块本体        | 靛蓝色   |
| `code_caption`                                       | VLM          | 代码描述          | 浅蓝色   |
| `list` / `index`                                     | VLM/pipeline | 列表/目录         | 绿色     |
| `discarded` / `abandon`                              | pipeline     | 废弃内容          | 灰色     |
| `header`                                             | VLM          | 页眉              | 浅灰色   |
| `footer`                                             | VLM          | 页脚              | 浅灰色   |
| `page_number`                                        | VLM          | 页码              | 浅灰色   |
| `aside_text`                                         | VLM          | 装订线注          | 灰色     |
| `page_footnote`                                      | VLM          | 页面脚注          | 紫罗兰   |
| `ref_text`                                           | VLM          | 参考文献          | 灰色     |
| 其他                                                 | —            | 未知类型          | 默认灰色 |

---

## 标注颜色配置

颜色在 `constants/index.ts` 的 `PDF_COLOR_PICKER` 中定义：

```typescript
export const PDF_COLOR_PICKER: Record<string, BboxColor> = {
  title: {
    line: 'rgba(121, 124, 255, 1)', // 边框色（不透明）
    fill: 'rgba(121, 124, 255, 0.3)', // 填充色（半透明）
  },
  // ... 其他类型
}
```

**自定义颜色**：直接修改 `PDF_COLOR_PICKER` 中对应类型的值，无需改动组件代码。

**单个 Bbox 覆盖**：在 `Bbox` 对象中传入 `color` 字段，优先级高于全局配置：

```typescript
{
  type: 'title',
  bbox: [52, 62, 294, 83],
  color: { line: 'red', fill: 'rgba(255, 0, 0, 0.2)' }
}
```

---

## 常见问题

**Q：PDF 显示空白或加载失败**

1. 确认 `public/pdfjs-dist/` 目录存在，运行后可访问 `/pdfjs-dist/web/viewer.html`
2. 检查 `pdfUrl` 是否可被浏览器直接访问（同源或已配置 CORS）
3. 打开浏览器控制台，查看 `[PdfViewer]` 前缀的错误信息

**Q：标注框不显示**

1. 确认 `layerData` 有数据，且 key 为正确的 0-based 页码
2. 确认 bbox 是绝对像素坐标（VLM 输出需先调用 `vlmModelJsonToLayerData`）
3. 点击 PDF Viewer 工具栏中的 **"显示识别结果"** 按钮，标注层默认可能为隐藏状态

**Q：数学公式显示为原始 LaTeX 文本**

确认 `katex/dist/katex.min.css` 已被加载（`UrlMarkdown.vue` 中 `import 'katex/dist/katex.min.css'`）。

**Q：Markdown 与 PDF 页码不对应**

`markdownContent` 数组的 index 必须严格对应 PDF 页码（0-based）。若某页没有内容，用空字符串占位：

```typescript
const markdownContent = [
  '', // 第 0 页（封面，无内容）
  '# 第1章', // 第 1 页
  '# 第2章', // 第 2 页
]
```

**Q：组件高度为 0**

组件内部全部使用 `h-full`，**父容器必须有明确高度**：

```vue
<!-- ✅ 正确 -->
<div style="height: 800px;"><MinerUViewer ... /></div>
<div class="h-screen"><MinerUViewer ... /></div>

<!-- ❌ 错误：div 默认高度为 0 -->
<div><MinerUViewer ... /></div>
```

**Q：切换 PDF 文件后标注层未更新**

`PdfViewer` 在收到新的 `status: 'loaded'` 消息后会重新发送 `initExtractLayerData`，需同步更新 `layerData` prop 才会刷新标注。

---

## 技术栈对照（React 原版 → Vue 移植）

| 方面          | MinerU 原版（React）                        | 本组件（Vue）                           |
| ------------- | ------------------------------------------- | --------------------------------------- |
| 框架          | React 18                                    | Vue 3.5                                 |
| 状态管理      | Zustand                                     | Pinia                                   |
| Markdown 解析 | react-markdown + remark-math + rehype-katex | marked + marked-katex-extension         |
| HTML 净化     | 内置（rehype-raw）                          | DOMPurify                               |
| 代码高亮      | react-syntax-highlighter（Prism）           | 原生 `<pre><code>`                      |
| 编辑器        | CodeMirror                                  | ant-design-vue Textarea                 |
| 异步滚动保护  | useHover（ahooks）                          | isAutoScrolling ref + 400ms 定时器      |
| MD 内容加载   | 自定义并发队列（axios，URL 数组）           | 直接接收内容字符串数组（不做 URL 加载） |
