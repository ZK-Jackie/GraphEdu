# SvgIcon 组件

基于 SVG Sprite 技术的图标组件，配合项目自制的 `vite-plugin-svg-icons-plus` 插件使用。

## 图标来源

本项目使用 **Ant Design Icons** 作为图标库，位于 `node_modules/@ant-design/icons-svg/inline-namespaced-svg`（需要安装依赖 `@ant-design/icons-svg`）。

## 命名规则

### Ant Design 原始命名

Ant Design 图标采用 **风格 + 图标名** 的组合命名方式：

```typescript
UserOutlined // Outlined 风格 + User（用户）
UpCircleOutlined // Outlined 风格 + UpCircle（向上圆圈）
AccountBookFilled // Filled 风格 + AccountBook（账本）
CheckCircleTwotone // Twotone 风格 + CheckCircle（勾选圆圈）
```

### SvgIcon 组件命名

本项目将 Ant Design 的 **驼峰命名** 转换为 **连字符命名**：

| Ant Design 命名      | SvgIcon 命名           | 说明              |
| -------------------- | ---------------------- | ----------------- |
| `UserOutlined`       | `outlined-user`        | 风格在前，小写    |
| `UpCircleOutlined`   | `outlined-up-circle`   | 多单词用 `-` 分隔 |
| `AccountBookFilled`  | `filled-account-book`  | 风格在后时同理    |
| `CheckCircleTwotone` | `twotone-check-circle` | Twotone 风格      |

**转换规则**：

1. **风格部分**（Outlined/Filled/Twotone）→ 小写 + 连字符前缀
2. **图标名称**（PascalCase）→ 小写 + 连字符分隔

### 风格对照表

| Ant Design 后缀 | SvgIcon 前缀 | 示例                                          |
| --------------- | ------------ | --------------------------------------------- |
| `Outlined`      | `outlined-`  | `UserOutlined` → `outlined-user`              |
| `Filled`        | `filled-`    | `AccountBookFilled` → `filled-account-book`   |
| `Twotone`       | `twotone-`   | `CheckCircleTwotone` → `twotone-check-circle` |

## 基本用法

### 引入组件

```vue
<script setup lang="ts">
import SvgIcon from '@/components/SvgIcon/index.vue'
</script>
```

### 使用图标

```vue
<template>
  <!-- 用户图标 (UserOutlined) -->
  <SvgIcon icon="outlined-user" />

  <!-- 向上圆圈图标 (UpCircleOutlined) -->
  <SvgIcon icon="outlined-up-circle" />

  <!-- 账本图标 (AccountBookFilled) -->
  <SvgIcon icon="filled-account-book" />

  <!-- 勾选圆圈图标 (CheckCircleTwotone) -->
  <SvgIcon icon="twotone-check-circle" />
</template>
```

## Props

| 参数  | 说明                          | 类型     | 默认值 | 必填 |
| ----- | ----------------------------- | -------- | ------ | ---- |
| icon  | 图标名称（不含 `icon-` 前缀） | `string` | -      | 是   |
| color | 图标颜色                      | `string` | `''`   | 否   |

## 颜色定制

### 使用 color 属性

```vue
<template>
  <!-- 红色用户图标 -->
  <SvgIcon icon="outlined-user" color="#ff0000" />

  <!-- 使用 CSS 变量 -->
  <SvgIcon icon="outlined-up-circle" color="var(--primary-color)" />
</template>
```

### 通过 CSS 控制

组件默认使用 `currentColor`，会继承父元素的 `color`：

```vue
<template>
  <div class="text-blue-500">
    <!-- 图标会显示为蓝色 -->
    <SvgIcon icon="outlined-user" />
  </div>
</template>
```

或使用 Tailwind CSS 类：

```vue
<template>
  <SvgIcon icon="outlined-user" class="text-red-500" />
</template>
```

## 尺寸控制

组件默认尺寸为 `1em`，会随字体大小缩放：

```vue
<template>
  <!-- 小尺寸 -->
  <SvgIcon icon="outlined-user" class="text-sm" />

  <!-- 正常尺寸 -->
  <SvgIcon icon="outlined-user" class="text-base" />

  <!-- 大尺寸 -->
  <SvgIcon icon="outlined-user" class="text-2xl" />

  <!-- 自定义尺寸 -->
  <SvgIcon icon="outlined-user" style="font-size: 32px" />
</template>
```

## 完整示例

```vue
<template>
  <div class="icon-demo">
    <!-- 基本用法 -->
    <SvgIcon icon="outlined-user" />

    <!-- 带颜色 -->
    <SvgIcon icon="outlined-up-circle" color="#1890ff" />

    <!-- 使用 Tailwind 类控制颜色和尺寸 -->
    <SvgIcon icon="filled-account-book" class="text-green-500 text-xl" />

    <!-- 按钮中嵌入图标 -->
    <a-button>
      <SvgIcon icon="outlined-edit" class="mr-1" />
      编辑
    </a-button>
  </div>
</template>

<script setup lang="ts">
import SvgIcon from '@/components/SvgIcon/index.vue'
</script>
```

## 常用图标速查

### 用户相关

| Ant Design           | SvgIcon                | 说明     |
| -------------------- | ---------------------- | -------- |
| `UserOutlined`       | `outlined-user`        | 用户     |
| `UserAddOutlined`    | `outlined-user-add`    | 添加用户 |
| `UserDeleteOutlined` | `outlined-user-delete` | 删除用户 |
| `TeamOutlined`       | `outlined-team`        | 团队     |

### 操作相关

| Ant Design       | SvgIcon           | 说明 |
| ---------------- | ----------------- | ---- |
| `EditOutlined`   | `outlined-edit`   | 编辑 |
| `DeleteOutlined` | `outlined-delete` | 删除 |
| `PlusOutlined`   | `outlined-plus`   | 添加 |
| `CloseOutlined`  | `outlined-close`  | 关闭 |
| `CheckOutlined`  | `outlined-check`  | 勾选 |

### 方向相关

| Ant Design           | SvgIcon                | 说明     |
| -------------------- | ---------------------- | -------- |
| `UpOutlined`         | `outlined-up`          | 向上     |
| `DownOutlined`       | `outlined-down`        | 向下     |
| `LeftOutlined`       | `outlined-left`        | 向左     |
| `RightOutlined`      | `outlined-right`       | 向右     |
| `UpCircleOutlined`   | `outlined-up-circle`   | 向上圆圈 |
| `DownCircleOutlined` | `outlined-down-circle` | 向下圆圈 |

### 文件相关

| Ant Design         | SvgIcon              | 说明     |
| ------------------ | -------------------- | -------- |
| `FileOutlined`     | `outlined-file`      | 文件     |
| `FolderOutlined`   | `outlined-folder`    | 文件夹   |
| `FileTextOutlined` | `outlined-file-text` | 文本文件 |
| `FilePdfOutlined`  | `outlined-file-pdf`  | PDF 文件 |

## 图标查找

完整图标列表请访问 [Ant Design Icons 官方文档](https://ant.design/components/icon-cn)。

**命名转换步骤**：

1. 在官网找到想要的图标，例如 `UserOutlined`
2. 提取风格后缀：`Outlined` → `outlined-`
3. 提取图标名：`User` → `user`
4. 组合：`outlined-` + `user` = `outlined-user`

## 技术实现

组件内部会自动添加 `icon-` 前缀：

```vue
<!-- 用户传入 -->
<SvgIcon icon="outlined-user" />

<!-- 实际渲染 -->
<svg class="svg-icon" aria-hidden="true">
  <use xlink:href="#icon-outlined-user" />
</svg>
```

## 插件配置

相关插件配置位于 `vite/plugins/svg-icon.ts`：

```typescript
createSvgIconsPlugin({
  iconDirs: ['node_modules/@ant-design/icons-svg/inline-namespaced-svg'],
  symbolId: 'icon-[dir]-[name]',
  optimize: true,
  domId: '__svg_icons_dom__',
  inject: 'body-last',
})
```

更多插件细节请参考 [vite-plugin-svg-icons-plus 文档](../../../vite/plugins/vite-plugin-svg-icons-plus/README.md)。
