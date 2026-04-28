# Cloudflare Turnstile 认证组件

本目录包含 Cloudflare Turnstile 人机验证的 Vue 3 组件实现。

## 组件列表

### 1. TurnstileWidget.vue

基础 Turnstile Widget 组件，封装了 Cloudflare Turnstile 的基本功能。

**Props:**

- `siteKey` (string, required): Cloudflare Site Key
- `widgetId` (string, optional): 组件唯一标识，默认为 `'turnstile-widget'`
- `theme` ('auto' | 'light' | 'dark'): 主题，默认为 `'auto'`
- `language` (string, optional): 语言，默认为 `'auto'`
- `tabIndex` (number, optional): Tabindex，默认为 `0`

**Events:**

- `verify`: 验证成功时触发，返回 `token`
- `error`: 发生错误时触发
- `expire`: 验证过期时触发
- `fail`: 验证失败时触发
- `ready-for-interaction`: Widget 准备好接收焦点时触发
- `client-side-confirmation`: Widget 清除时触发

**暴露的方法:**

- `reset()`: 重置 Widget
- `getResponse()`: 获取响应 Token
- `remove()`: 移除 Widget

**使用示例:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import TurnstileWidget from '@/components/auth/TurnstileWidget.vue'

const turnstileRef = ref()
const token = ref('')

const handleVerify = (t: string) => {
  token.value = t
  console.log('验证成功:', t)
}

const handleSubmit = async () => {
  // 获取 token 并提交到后端
  const responseToken = turnstileRef.value.getResponse()
  // ... 调用后端 API 验证
}
</script>

<template>
  <TurnstileWidget ref="turnstileRef" site-key="your-site-key" @verify="handleVerify" />
  <a-button @click="handleSubmit">提交</a-button>
</template>
```

### 2. TurnstileInput.vue

封装了验证逻辑的高级组件，包含前端验证和后端验证。

**Props:**

- `siteKey` (string, required): Cloudflare Site Key
- `theme` ('auto' | 'light' | 'dark'): 主题，默认为 `'auto'`
- `autoValidate` (boolean): 是否在组件内自动验证（默认 false）

**Events:**

- `update:modelValue`: 验证成功时触发，返回 token
- `validate`: 验证完成时触发，返回 `(success: boolean, data?: any)`

**暴露的方法:**

- `validateToken()`: 调用后端验证 token，返回 `Promise<boolean>`
- `reset()`: 重置验证
- `checkValidated()`: 检查是否已验证，返回 `boolean`
- `getToken()`: 获取当前 token
- `getResponse()`: 获取响应 Token

**使用示例（手动验证）:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import TurnstileInput from '@/components/auth/TurnstileInput.vue'

const turnstileInputRef = ref()
const formData = ref({
  username: '',
  password: '',
  turnstileToken: '',
})

const handleLogin = async () => {
  // 先验证 Turnstile
  const isValid = await turnstileInputRef.value.validateToken()
  if (!isValid) {
    return
  }

  // 获取 token 并提交登录
  formData.value.turnstileToken = turnstileInputRef.value.getToken()
  // ... 调用登录 API
}
</script>

<template>
  <a-form :model="formData">
    <a-form-item label="用户名">
      <a-input v-model:value="formData.username" />
    </a-form-item>
    <a-form-item label="密码">
      <a-input-password v-model:value="formData.password" />
    </a-form-item>
    <a-form-item label="验证">
      <TurnstileInput ref="turnstileInputRef" v-model="formData.turnstileToken" site-key="your-site-key" />
    </a-form-item>
    <a-form-item>
      <a-button type="primary" @click="handleLogin">登录</a-button>
    </a-form-item>
  </a-form>
</template>
```

**使用示例（自动验证）:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import TurnstileInput from '@/components/auth/TurnstileInput.vue'

const turnstileInputRef = ref()
const formData = ref({
  username: '',
  password: '',
  turnstileToken: '',
})

const handleValidate = (success: boolean, data?: any) => {
  console.log('验证结果:', success, data)
}

const handleLogin = async () => {
  // 检查是否已验证
  if (!turnstileInputRef.value.checkValidated()) {
    return
  }

  // 提交登录
  formData.value.turnstileToken = turnstileInputRef.value.getToken()
  // ... 调用登录 API
}
</script>

<template>
  <a-form :model="formData">
    <a-form-item label="用户名">
      <a-input v-model:value="formData.username" />
    </a-form-item>
    <a-form-item label="密码">
      <a-input-password v-model:value="formData.password" />
    </a-form-item>
    <a-form-item label="验证">
      <TurnstileInput
        ref="turnstileInputRef"
        v-model="formData.turnstileToken"
        site-key="your-site-key"
        :auto-validate="true"
        @validate="handleValidate"
      />
    </a-form-item>
    <a-form-item>
      <a-button type="primary" @click="handleLogin">登录</a-button>
    </a-form-item>
  </a-form>
</template>
```

## API 说明

### validateTurnstile

验证 Cloudflare Turnstile token 的 API 函数。

**签名:**

```typescript
function validateTurnstile(data: TurnstileValidateDTO): Promise<ResponseType<TurnstileValidateVO>>
```

**参数:**

```typescript
interface TurnstileValidateDTO {
  token: string // Turnstile 验证 token
  remoteIp?: string // 用户 IP 地址（可选）
}
```

**返回:**

```typescript
interface TurnstileValidateVO {
  success: boolean // 验证是否成功
  challengeTs?: string // 验证时间戳
  hostname?: string // 验证时使用的主机名
  errorCodes?: string[] // 错误码列表
  action?: string // 验证操作类型
  cdata?: string // 客户数据
}
```

**使用示例:**

```typescript
import { validateTurnstile } from '@/api/system/auth'

const result = await validateTurnstile({
  token: '0x...',
})

if (result.data.success) {
  console.log('验证成功')
} else {
  console.error('验证失败:', result.data.errorCodes)
}
```

## 配置说明

### 1. 获取 Cloudflare Turnstile Site Key

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Turnstile** 页面
3. 创建新的 Site Key
4. 选择 **Managed Challenge** 模式（推荐）
5. 复制 **Site Key** 和 **Secret Key**

### 2. 配置后端

在后端配置文件中添加 Secret Key：

```yaml
service:
  turnstile:
    secret: 'your-turnstile-secret-key'
    verify_url: 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    timeout: 10.0
```

### 3. 配置前端

将 Site Key 传递给 Turnstile 组件：

```vue
<TurnstileInput site-key="your-site-key" />
```

或在环境变量中配置：

```bash
# .env.development
VITE_TURNSTILE_SITE_KEY=your-site-key
```

```vue
<script setup>
import TurnstileInput from '@/components/auth/TurnstileInput.vue'

const siteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY
</script>

<template>
  <TurnstileInput :site-key="siteKey" />
</template>
```

## 注意事项

1. **安全性**: Secret Key 必须保存在后端，不要暴露在前端代码中
2. **验证流程**: 前端获取 token → 提交到后端 → 后端调用 Cloudflare API 验证
3. **Token 过期**: Token 有效期通常为 5 分钟，过期后需要重新验证
4. **错误处理**: 建议在表单提交前检查验证状态
5. **主题适配**: 组件支持自动适配明暗主题

## 常见问题

### Q: 组件加载失败？

A: 检查网络是否能访问 `challenges.cloudflare.com`，某些地区可能需要特殊网络配置。

### Q: 验证总是失败？

A: 检查：

1. Site Key 和 Secret Key 是否匹配
2. 后端 API 是否正常工作
3. 浏览器控制台是否有错误信息

### Q: 如何在测试环境跳过验证？

A: 可以在开发环境下使用 Cloudflare 的测试密钥：

- Site Key: `1x00000000000000000000AA`
- Secret Key: `1x0000000000000000000000000000000AA`

测试密钥会始终返回验证成功。
