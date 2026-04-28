<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import CaptchaInput from '@/components/auth/CaptchaInput.vue'

const router = useRouter()

const loading = ref(false)

// 表单数据
const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  captcha: '',
})

// 密码强度
const passwordStrength = computed(() => {
  const pwd = formData.password
  if (!pwd) return { level: 0, text: '', color: '' }

  let strength = 0
  if (pwd.length >= 8) strength++
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++
  if (/\d/.test(pwd)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength++

  if (strength <= 1) return { level: 1, text: '弱', color: '#ff4d4f' }
  if (strength === 2) return { level: 2, text: '中', color: '#faad14' }
  if (strength === 3) return { level: 3, text: '强', color: '#52c41a' }
  return { level: 4, text: '很强', color: '#52c41a' }
})

// 密码匹配
const passwordMatch = computed(() => {
  if (!formData.confirmPassword) return null
  return formData.password === formData.confirmPassword
})

// 方法
const validateForm = () => {
  if (!formData.username) {
    message.warning('请输入用户名')
    return false
  }
  if (formData.username.length < 3 || formData.username.length > 20) {
    message.warning('用户名长度应在3-20个字符之间')
    return false
  }
  if (!formData.password) {
    message.warning('请输入密码')
    return false
  }
  if (formData.password.length < 6) {
    message.warning('密码长度不能少于6个字符')
    return false
  }
  if (!formData.confirmPassword) {
    message.warning('请确认密码')
    return false
  }
  if (formData.password !== formData.confirmPassword) {
    message.warning('两次输入的密码不一致')
    return false
  }
  if (!formData.captcha) {
    message.warning('请输入验证码')
    return false
  }
  return true
}

const handleRegister = async () => {
  if (!validateForm()) return

  loading.value = true

  try {
    // TODO: 调用注册API
    await new Promise((resolve) => setTimeout(resolve, 1000))
    message.success('注册成功，即将跳转到登录页')
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (_error) {
    message.error('注册失败，请重试')
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

const onCaptchaRefresh = () => {
  // TODO: 刷新验证码的逻辑
  console.log('刷新验证码')
}
</script>

<template>
  <div class="register-page">
    <div class="register-content">
      <div class="register-container">
        <div class="register-box">
          <h2 class="register-title">创建账号</h2>
          <p class="register-subtitle">开启你的学习之旅</p>

          <div class="form-wrapper">
            <!-- 用户名输入 -->
            <div class="form-item">
              <label class="form-label">用户名</label>
              <a-input
                v-model:value="formData.username"
                size="large"
                placeholder="请输入用户名（3-20个字符）"
                class="form-input"
                :maxlength="20"
              >
                <template #prefix>
                  <UserOutlined class="input-icon" />
                </template>
              </a-input>
            </div>

            <!-- 密码输入 -->
            <div class="form-item">
              <label class="form-label">密码</label>
              <a-input-password
                v-model:value="formData.password"
                size="large"
                placeholder="请输入密码（至少6个字符）"
                class="form-input"
              >
                <template #prefix>
                  <LockOutlined class="input-icon" />
                </template>
              </a-input-password>
              <!-- 密码强度提示 -->
              <div v-if="formData.password" class="password-strength">
                <div class="strength-bar">
                  <div
                    v-for="i in 4"
                    :key="i"
                    class="strength-item"
                    :class="{ active: i <= passwordStrength.level }"
                    :style="{ backgroundColor: i <= passwordStrength.level ? passwordStrength.color : '' }"
                  ></div>
                </div>
                <span class="strength-text" :style="{ color: passwordStrength.color }">
                  {{ passwordStrength.text }}
                </span>
              </div>
            </div>

            <!-- 确认密码输入 -->
            <div class="form-item">
              <label class="form-label">确认密码</label>
              <a-input-password
                v-model:value="formData.confirmPassword"
                size="large"
                placeholder="请再次输入密码"
                class="form-input"
                :status="passwordMatch === false ? 'error' : ''"
              >
                <template #prefix>
                  <LockOutlined class="input-icon" />
                </template>
              </a-input-password>
              <div v-if="passwordMatch === false" class="error-tip">两次输入的密码不一致</div>
              <div v-if="passwordMatch === true" class="success-tip">密码匹配</div>
            </div>

            <!-- 验证码 -->
            <div class="form-item">
              <label class="form-label">验证码</label>
              <CaptchaInput v-model="formData.captcha" class="form-input" @refresh="onCaptchaRefresh" />
            </div>

            <!-- 注册按钮 -->
            <a-button
              type="primary"
              size="large"
              block
              :loading="loading"
              class="register-button"
              @click="handleRegister"
            >
              注册
            </a-button>

            <!-- 底部提示 -->
            <div class="form-footer">
              <span class="footer-text">已有账号？</span>
              <a class="footer-link" @click="goToLogin">立即登录</a>
            </div>

            <!-- 用户协议提示 -->
            <div class="agreement-tip">
              注册即表示同意
              <a class="agreement-link">用户协议</a>
              和
              <a class="agreement-link">隐私政策</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.register-page {
  @apply flex-1 flex items-center justify-center p-4;
}

.register-content {
  @apply w-full;
}

.register-container {
  @apply w-full max-w-md mx-auto;
}

.register-box {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-xl;
  @apply p-8 md:p-12;
}

.register-title {
  @apply text-2xl md:text-3xl font-bold mb-2 text-center;
  @apply text-gray-800 dark:text-gray-200;
}

.register-subtitle {
  @apply text-gray-500 dark:text-gray-400 text-center mb-8;
}

.form-wrapper {
  @apply flex flex-col gap-5;
}

.form-item {
  @apply w-full;
}

.form-label {
  @apply block text-sm font-medium mb-2;
  @apply text-gray-700 dark:text-gray-300;
}

.form-input {
  @apply w-full;
}

.input-icon {
  @apply text-gray-400;
}

.password-strength {
  @apply flex items-center gap-2 mt-2;
}

.strength-bar {
  @apply flex gap-1 flex-1;
}

.strength-item {
  @apply h-1 flex-1 rounded;
  @apply bg-gray-200 dark:bg-gray-700;
  transition: background-color 0.3s;
}

.strength-item.active {
  @apply opacity-100;
}

.strength-text {
  @apply text-xs font-medium;
}

.error-tip {
  @apply text-red-500 text-xs mt-1;
}

.success-tip {
  @apply text-green-500 text-xs mt-1;
}

.register-button {
  @apply mt-2 h-12 text-base font-medium;
}

.form-footer {
  @apply text-center;
}

.footer-text {
  @apply text-gray-600 dark:text-gray-400 text-sm;
}

.footer-link {
  @apply text-blue-600 dark:text-blue-400 text-sm ml-1;
  @apply hover:text-blue-700 dark:hover:text-blue-300;
  @apply cursor-pointer;
}

.agreement-tip {
  @apply text-center text-xs text-gray-500 dark:text-gray-400;
}

.agreement-link {
  @apply text-blue-600 dark:text-blue-400;
  @apply hover:text-blue-700 dark:hover:text-blue-300;
  @apply cursor-pointer;
}

/* 黑夜模式输入框样式调整 */
html.dark :deep(.ant-input),
html.dark :deep(.ant-input-password),
html.dark :deep(.ant-input-affix-wrapper) {
  background-color: rgb(17 24 39) !important; /* gray-900 */
  border-color: rgb(75 85 99) !important; /* gray-600 */
  color: rgb(229 231 235) !important; /* gray-200 */
}

html.dark :deep(.ant-input)::placeholder,
html.dark :deep(.ant-input-password input)::placeholder {
  color: rgb(107 114 128) !important; /* gray-500 */
}

html.dark :deep(.ant-input-affix-wrapper):hover,
html.dark :deep(.ant-input-affix-wrapper):focus,
html.dark :deep(.ant-input-affix-wrapper-focused) {
  border-color: rgb(96 165 250) !important; /* blue-400 */
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .register-box {
    @apply p-6;
  }

  .register-title {
    @apply text-xl mb-2;
  }

  .register-subtitle {
    @apply text-sm mb-6;
  }

  .form-wrapper {
    @apply gap-4;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .register-content {
    @apply p-2;
  }

  .register-box {
    @apply p-4;
  }
}
</style>
