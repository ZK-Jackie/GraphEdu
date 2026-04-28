<script setup lang="ts">
import { LoadingOutlined, ExclamationCircleOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getCaptchaImage } from '@/api/system/auth'

// Props
interface CaptchaInputProps {
  code?: string | number
}

const props = withDefaults(defineProps<CaptchaInputProps>(), {
  code: '',
})

// Emits
const emit = defineEmits<{
  'update:code': [value: string]
  refresh: [uuid: string]
}>()
const inputCode = computed({
  get: () => props.code,
  set: (value: string) => emit('update:code', value),
})

// State
const captchaImage = ref('')
const captchaUuid = ref('')
const loading = ref(false)
const imageLoaded = ref(false)
const imageLoadError = ref(false)

// Methods
const handleImageLoad = () => {
  imageLoaded.value = true
  imageLoadError.value = false
}

const handleImageError = () => {
  imageLoaded.value = false
  imageLoadError.value = true
}

const refreshCaptcha = async () => {
  loading.value = true
  imageLoadError.value = false
  imageLoaded.value = false

  try {
    const response = await getCaptchaImage()
    const { data } = response

    // 验证响应数据有效性
    if (!data || !data.img || !data.uuid) {
      throw new Error('验证码数据无效')
    }

    inputCode.value = String(data.code ?? '')
    captchaImage.value = `data:image/png;base64,${data.img}`
    captchaUuid.value = data.uuid

    // 通知父组件刷新成功，传递 uuid
    emit('refresh', data.uuid)
  } catch (error) {
    console.error('获取验证码失败:', error)
    message.error('获取验证码失败，请稍后重试')
    // 清空图片并设置错误状态
    captchaImage.value = ''
    imageLoadError.value = true
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  refreshCaptcha()
})
</script>

<template>
  <div class="captcha-container">
    <a-input v-model:value="inputCode" class="captcha-input" :maxlength="4" size="small" placeholder="请输入验证码">
      <template #suffix>
        <div class="captcha-image-wrapper">
          <a-spin :spinning="loading" size="small">
            <img
              v-if="captchaImage"
              :src="captchaImage"
              alt="验证码"
              class="captcha-image"
              @load="handleImageLoad"
              @error="handleImageError"
              @click="refreshCaptcha"
            />
            <div v-else class="captcha-placeholder" @click="refreshCaptcha">
              <LoadingOutlined v-if="loading" />
              <span v-else>
                <ExclamationCircleOutlined class="error-icon" />
                加载失败
              </span>
            </div>
          </a-spin>
        </div>
      </template>
    </a-input>
  </div>
</template>

<style scoped>
@reference "#main.css";

.captcha-container {
  @apply w-full;
}

.captcha-input {
  @apply w-full h-11 ps-4;
}

.captcha-image-wrapper {
  @apply flex items-center justify-center ml-2;
}

.captcha-image {
  @apply h-10 cursor-pointer rounded border border-gray-300 dark:border-gray-600;
  @apply hover:opacity-80 transition-opacity;
  width: 120px;
  object-fit: cover;
}

.captcha-placeholder {
  @apply flex items-center justify-center cursor-pointer;
  @apply h-10 w-30 rounded border border-dashed border-gray-300 dark:border-gray-600;
  @apply text-gray-400 dark:text-gray-500;
}

.error-icon {
  @apply text-red-500;
}

.refresh-btn {
  @apply ml-1;
}

/* 黑夜模式输入框样式 */
html.dark :deep(.ant-input),
html.dark :deep(.ant-input-affix-wrapper) {
  background-color: rgb(17 24 39) !important; /* gray-900 */
  border-color: rgb(75 85 99) !important; /* gray-600 */
  color: rgb(229 231 235) !important; /* gray-200 */
}

html.dark :deep(.ant-input)::placeholder {
  color: rgb(107 114 128) !important; /* gray-500 */
}

html.dark :deep(.ant-input-affix-wrapper):hover,
html.dark :deep(.ant-input-affix-wrapper):focus,
html.dark :deep(.ant-input-affix-wrapper-focused) {
  border-color: rgb(96 165 250) !important; /* blue-400 */
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
}
</style>
