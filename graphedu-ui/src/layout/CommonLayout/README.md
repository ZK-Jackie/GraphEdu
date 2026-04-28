# CommonLayout 使用说明

## 📋 概述

CommonLayout 是一个简洁的通用布局方案，适用于首页、关于页、文档页等不需要复杂侧边栏和面板管理的页面。

## 🏗️ 布局结构

```
┌─────────────────────────────────────────────┐
│  CommonHeader (固定顶部导航栏)                │
│  - 左侧: Logo + 导航项                        │
│  - 右侧: GitHub + 深色模式 + 用户头像          │
├─────────────────────────────────────────────┤
│                                             │
│  Main Content (路由页面内容)                 │
│  - 支持页面切换动画                           │
│  - 可滚动内容区域                             │
│                                             │
├─────────────────────────────────────────────┤
│  CommonFooter (底部信息栏)                    │
│  - 版权信息                                   │
│  - 底部链接                                   │
└─────────────────────────────────────────────┘
```

## 🎨 组件说明

### 1. CommonHeader (导航栏)

**左侧内容：**

- Logo + 文字：点击返回首页
- 导航项：可配置的路由链接，支持激活状态高亮

**右侧内容：**

- GitHub 图标按钮
- 深色模式切换按钮
- 用户头像

**配置导航项：**

```typescript
// 在 CommonHeader.vue 中修改
const navItems = ref([
  { label: '首页', path: '/' },
  { label: '关于', path: '/about' },
  { label: '文档', path: '/docs' },
  { label: '联系', path: '/contact' },
])
```

### 2. CommonFooter (底部信息栏)

**内容：**

- 版权信息：自动显示当前年份
- 底部链接：关于我们、隐私政策、使用条款、联系我们

**配置底部链接：**

```typescript
// 在 CommonFooter.vue 中修改
const footerLinks = ref([
  { label: '关于我们', path: '/about' },
  { label: '隐私政策', path: '/privacy' },
  { label: '使用条款', path: '/terms' },
  { label: '联系我们', path: '/contact' },
])
```

## 🚀 使用方式

### 在路由中使用

```typescript
// router/index.ts
import { CommonLayout } from '@/layout'

const routes = [
  {
    path: '/',
    component: CommonLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
      },
      {
        path: 'about',
        name: 'About',
        component: () => import('@/views/About.vue'),
      },
    ],
  },
]
```

### 在页面组件中使用

页面组件会自动渲染在 CommonLayout 的主内容区域：

```vue
<!-- views/Home.vue -->
<template>
  <div class="home-page">
    <h1>欢迎来到首页</h1>
    <p>这里是通过 CommonLayout 渲染的页面内容</p>
  </div>
</template>

<style scoped>
.home-page {
  @apply max-w-7xl mx-auto px-6 py-12;
}
</style>
```

## ✨ 特性

1. **响应式设计**：支持桌面和移动端
2. **暗色模式**：完整的暗色模式支持
3. **页面动画**：平滑的页面切换动画
4. **导航高亮**：当前页面导航项自动高亮
5. **固定导航栏**：顶部导航栏固定，内容区域可滚动

## 🎯 与 WorkbenchLayout 的区别

| 特性          | CommonLayout       | WorkbenchLayout  |
| ------------- | ------------------ | ---------------- |
| 侧边栏        | ❌ 无              | ✅ 有            |
| Golden Layout | ❌ 无              | ✅ 有            |
| 多标签页      | ❌ 无              | ✅ 有            |
| 固定导航栏    | ✅ 有              | ✅ 有            |
| Footer        | ✅ 有              | ❌ 无            |
| 适用场景      | 简单页面、营销页面 | 工作台、管理后台 |

## 📝 自定义建议

1. **修改导航项**：编辑 `CommonHeader.vue` 中的 `navItems`
2. **修改底部链接**：编辑 `CommonFooter.vue` 中的 `footerLinks`
3. **调整样式**：修改对应组件的 `<style>` 部分
4. **添加组件**：在 `CommonLayout/components/` 下添加新组件
