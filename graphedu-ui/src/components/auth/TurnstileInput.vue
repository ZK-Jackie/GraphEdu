<script setup lang="ts">
import { message } from 'ant-design-vue'
import TurnstileWidget from './TurnstileWidget.vue'
import { validateTurnstile } from '@/api/system/auth'

// Props
interface Props {
  /** Cloudflare Site Key */
  siteKey: string
  /** 主题：light 或 dark */
  theme?: 'auto' | 'light' | 'dark'
  /** 是否在组件内自动验证（默认 false） */
  autoValidate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'auto',
  autoValidate: false,
})

// Emits
interface Emits {
  /** 验证成功时触发，返回服务端验证结果 */
  'update:modelValue': [token: string]
  /** 验证完成（包括成功和失败） */
  validate: [success: boolean, data?: any]
}

const emit = defineEmits<Emits>()

// State
const turnstileRef = ref<InstanceType<typeof TurnstileWidget> | null>(null)
const currentToken = ref('')
const isValidating = ref(false)
const isValidated = ref(false)
const serverValidated = ref(false)

/**
 * 处理 Turnstile 验证成功回调（前端验证）
 */
const handleVerify = (token: string) => {
  currentToken.value = token
  isValidated.value = true
  emit('update:modelValue', token)

  // 如果启用了自动验证，立即调用后端验证
  if (props.autoValidate) {
    validateToken()
  }
}

/**
 * 调用后端验证 token
 */
const validateToken = async (): Promise<boolean> => {
  if (!currentToken.value) {
    message.warning('请先完成人机验证')
    return false
  }

  if (!isValidated.value) {
    message.warning('验证未完成')
    return false
  }

  isValidating.value = true

  try {
    const response = await validateTurnstile({
      token: currentToken.value,
    })

    const success = response.data.success
    serverValidated.value = success

    if (success) {
      emit('validate', true, response.data)
    } else {
      message.error('验证失败，请重试')
      emit('validate', false, response.data)
      reset()
    }

    return success
  } catch (error: any) {
    console.error('Turnstile validation failed:', error)
    message.error(error.msg || '验证失败，请稍后重试')
    emit('validate', false, error)
    reset()
    return false
  } finally {
    isValidating.value = false
  }
}

/**
 * 重置验证
 */
const reset = () => {
  if (turnstileRef.value) {
    turnstileRef.value.reset()
  }
  currentToken.value = ''
  isValidated.value = false
  serverValidated.value = false
}

/**
 * 检查是否已验证
 */
const checkValidated = (): boolean => {
  return isValidated.value && !!currentToken.value
}

/**
 * 获取当前 token
 */
const getToken = (): string => {
  return currentToken.value
}

/**
 * 获取响应 Token（从 Widget）
 */
const getResponse = (): string | null => {
  if (turnstileRef.value) {
    return turnstileRef.value.getResponse()
  }
  return null
}

// 暴露方法给父组件
defineExpose({
  validateToken,
  reset,
  checkValidated,
  getToken,
  getResponse,
})
</script>

<template>
  <div class="turnstile-input-container">
    <TurnstileWidget
      ref="turnstileRef"
      :site-key="siteKey"
      :theme="theme"
      @verify="handleVerify"
      @error="emit('validate', false, $event)"
      @expire="reset"
    />

    <!-- 验证状态提示 -->
    <div v-if="isValidating" class="validation-status">
      <a-spin size="small" />
      <span class="ml-2">正在验证...</span>
    </div>
    <div v-else-if="serverValidated && isValidated" class="validation-status success">✓ 验证通过</div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.turnstile-input-container {
  @apply w-full;
}

.validation-status {
  @apply mt-2 text-sm text-gray-600 dark:text-gray-400 flex items-center;
}

.validation-status.success {
  @apply text-green-600 dark:text-green-400 font-medium;
}

/* 黑夜模式适配 */
html.dark .validation-status {
  @apply text-gray-400;
}

html.dark .validation-status.success {
  @apply text-green-400;
}
</style>
