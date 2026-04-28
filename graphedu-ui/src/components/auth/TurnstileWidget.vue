<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { message } from 'ant-design-vue'

// Props
interface Props {
  /** Cloudflare Site Key */
  siteKey: string
  /** 组件唯一标识（用于重置等操作） */
  widgetId?: string
  /** 主题：light 或 dark */
  theme?: 'auto' | 'light' | 'dark'
  /** 语言 */
  language?: string
  /** Tabindex */
  tabIndex?: number
}

const props = withDefaults(defineProps<Props>(), {
  widgetId: 'turnstile-widget',
  theme: 'auto',
  language: 'auto',
  tabIndex: 0,
})

// Emits
interface Emits {
  /** 验证成功时触发，返回 token */
  verify: [token: string]
  /** 验证失败时触发 */
  error: [error: any]
  /** 组件过期时触发 */
  expire: []
  /** 发生错误时触发 */
  fail: [error: any]
  /** Widget 已准备好接收焦点时触发 */
  'ready-for-interaction': []
  /** Widget 已清除时触发 */
  'client-side-confirmation': []
}

const emit = defineEmits<Emits>()

// State
const containerRef = ref<HTMLElement | null>(null)
const turnstileId = ref<string | null>(null)
const isLoading = ref(true)
const isVerified = ref(false)
const scriptLoaded = ref(false)

// Cloudflare Turnstile 全局对象
declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: any) => string
      reset: (widgetId?: string) => void
      remove: (widgetId?: string) => void
      getResponse: (widgetId?: string) => string
    }
  }
}

/**
 * 加载 Cloudflare Turnstile 脚本
 */
const loadTurnstileScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.turnstile) {
      scriptLoaded.value = true
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
    script.async = true
    script.defer = true

    script.onload = () => {
      scriptLoaded.value = true
      resolve()
    }

    script.onerror = () => {
      reject(new Error('Failed to load Cloudflare Turnstile script'))
    }

    document.head.appendChild(script)
  })
}

/**
 * 渲染 Turnstile Widget
 */
const renderWidget = () => {
  if (!window.turnstile || !containerRef.value) {
    return
  }

  // 如果已存在，先移除
  if (turnstileId.value) {
    window.turnstile.remove(turnstileId.value)
  }

  try {
    turnstileId.value = window.turnstile.render(containerRef.value, {
      sitekey: props.siteKey,
      theme: props.theme,
      language: props.language,
      tabindex: props.tabIndex,
      callback: (token: string) => {
        isVerified.value = true
        isLoading.value = false
        emit('verify', token)
      },
      'error-callback': (error: any) => {
        isLoading.value = false
        emit('error', error)
      },
      'expired-callback': () => {
        isVerified.value = false
        emit('expire')
      },
      'fail-callback': (error: any) => {
        isLoading.value = false
        emit('fail', error)
      },
      'ready-callback': () => {
        emit('ready-for-interaction')
      },
    })

    isLoading.value = false
  } catch (error) {
    isLoading.value = false
    console.error('Failed to render Turnstile widget:', error)
    message.error('加载验证组件失败')
  }
}

/**
 * 重置 Widget
 */
const reset = () => {
  if (window.turnstile && turnstileId.value) {
    window.turnstile.reset(turnstileId.value)
    isVerified.value = false
  }
}

/**
 * 获取响应 Token
 */
const getResponse = (): string | null => {
  if (window.turnstile && turnstileId.value) {
    return window.turnstile.getResponse(turnstileId.value)
  }
  return null
}

/**
 * 移除 Widget
 */
const remove = () => {
  if (window.turnstile && turnstileId.value) {
    window.turnstile.remove(turnstileId.value)
    turnstileId.value = null
    isVerified.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  reset,
  getResponse,
  remove,
})

// Lifecycle
onMounted(async () => {
  try {
    await loadTurnstileScript()
    renderWidget()
  } catch (error) {
    console.error('Failed to initialize Turnstile:', error)
    message.error('初始化验证组件失败')
    isLoading.value = false
  }
})

onUnmounted(() => {
  remove()
})

// Watch siteKey 变化重新渲染
watch(
  () => props.siteKey,
  () => {
    if (scriptLoaded.value) {
      renderWidget()
    }
  }
)
</script>

<template>
  <div class="turnstile-widget-container">
    <a-spin :spinning="isLoading" size="small">
      <div :id="widgetId" ref="containerRef" class="turnstile-widget"></div>
    </a-spin>
  </div>
</template>

<style scoped>
@reference "#main.css";

.turnstile-widget-container {
  @apply flex items-center justify-center;
  min-height: 65px;
}

.turnstile-widget {
  @apply w-full;
}

/* 黑夜模式适配 */
html.dark :deep(.turnstile-widget) {
  /* Turnstile 会自动适配主题，但可以在这里添加自定义样式 */
}
</style>
