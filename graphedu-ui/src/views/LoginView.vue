<script setup lang="ts">
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, MobileOutlined, IdcardOutlined } from '@ant-design/icons-vue'
import CaptchaInput from '@/components/auth/CaptchaInput.vue'
import QRCodeLogin from '@/components/auth/QRCodeLogin.vue'
import useUserStore from '@/stores/modules/user'

const router = useRouter()
const userStore = useUserStore()

// 是否启用二维码登录
const qrCodeEnabled = computed(() => import.meta.env.VITE_LOGIN_QRCODE === 'true')

// 登录类型
type LoginType = 'username' | 'phone' | 'studentId' | 'employeeId'

const activeTab = ref<LoginType>('username')
const loading = ref(false)

// 表单数据
const formData = reactive({
  account: '',
  password: '',
  captcha: '',
  uuid: '', // 验证码会话ID
})

// Tab配置
const tabs = [
  {
    key: 'username' as LoginType,
    label: '用户名登录',
    placeholder: '请输入用户名',
    icon: UserOutlined,
  },
  {
    key: 'phone' as LoginType,
    label: '手机号登录',
    placeholder: '请输入手机号',
    icon: MobileOutlined,
  },
  {
    key: 'studentId' as LoginType,
    label: '学号登录',
    placeholder: '请输入学号',
    icon: IdcardOutlined,
  },
  {
    key: 'employeeId' as LoginType,
    label: '工号登录',
    placeholder: '请输入工号',
    icon: IdcardOutlined,
  },
]

// 当前tab配置
const currentTab = computed(() => tabs.find((t) => t.key === activeTab.value))

// 方法
const handleTabChange = (key: string | any) => {
  activeTab.value = key as LoginType
  formData.account = ''
  formData.password = ''
  formData.captcha = ''
}

const handleLogin = async () => {
  // 验证
  if (!formData.account) {
    message.warning(currentTab.value?.placeholder ?? '请输入账号')
    return
  }
  if (!formData.password) {
    message.warning('请输入密码')
    return
  }
  if (!formData.captcha) {
    message.warning('请输入验证码')
    return
  }

  loading.value = true

  try {
    // 根据登录类型构建不同的请求数据
    const loginType = activeTab.value
    const baseFields = {
      password: formData.password,
      code: formData.captcha,
      uuid: formData.uuid,
    }

    let loginData: Record<string, any>
    switch (loginType) {
      case 'phone':
        loginData = { phonenumber: formData.account, ...baseFields }
        break
      case 'studentId':
        loginData = { studentNo: formData.account, ...baseFields }
        break
      case 'employeeId':
        loginData = { teacherNo: formData.account, ...baseFields }
        break
      default:
        loginData = { username: formData.account, ...baseFields }
        break
    }

    // 调用登录API
    await userStore.login(loginType, loginData as any)

    message.success('登录成功')

    // 获取查询参数中的 redirect
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
  } catch (_error) {
    message.error('登录失败，请检查账号密码')
    // 登录失败后刷新验证码
    onCaptchaRefresh()
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}

const onCaptchaRefresh = (uuid?: string) => {
  if (uuid) {
    formData.uuid = uuid
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-content">
      <div class="login-box">
        <!-- 左侧：账号密码登录 -->
        <div class="login-form-section">
          <h2 class="login-title">欢迎登录</h2>

          <!-- @ts-ignore Tab切换 -->
          <a-tabs v-model:active-key="activeTab" class="login-tabs" @change="handleTabChange">
            <a-tab-pane v-for="tab in tabs" :key="tab.key" :tab="tab.label">
              <div class="form-wrapper">
                <!-- 账号输入 -->
                <a-input
                  v-model:value="formData.account"
                  size="large"
                  :placeholder="tab.placeholder"
                  class="form-input"
                >
                  <template #prefix>
                    <component :is="tab.icon" class="input-icon" />
                  </template>
                </a-input>

                <!-- 密码输入 -->
                <a-input-password
                  v-model:value="formData.password"
                  size="large"
                  placeholder="请输入密码"
                  class="form-input"
                >
                  <template #prefix>
                    <LockOutlined class="input-icon" />
                  </template>
                </a-input-password>

                <!-- 验证码 -->
                <CaptchaInput v-model:code="formData.captcha" class="form-input" @refresh="onCaptchaRefresh" />

                <!-- 登录按钮 -->
                <a-button
                  type="primary"
                  size="large"
                  block
                  :loading="loading"
                  class="login-button"
                  @click="handleLogin"
                >
                  登录
                </a-button>

                <!-- 底部提示 -->
                <div class="form-footer">
                  <span class="footer-text">还没有账号？</span>
                  <a class="footer-link" @click="goToRegister">立即注册</a>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>

        <!-- 分隔线 -->
        <a-divider v-if="qrCodeEnabled" type="vertical" class="login-divider" />

        <!-- 右侧：二维码登录 -->
        <div v-if="qrCodeEnabled" class="qrcode-section">
          <QRCodeLogin />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.login-page {
  @apply flex-1 flex items-center justify-center;
}

.login-content {
  @apply w-full p-4;
}

.login-box {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-xl mx-auto;
  @apply flex flex-col md:flex-row;
  @apply overflow-hidden;
  max-width: 440px;
}

.login-form-section {
  @apply p-8 md:p-12 w-full;
}

.login-title {
  @apply text-2xl md:text-3xl font-bold mb-8 text-center;
  @apply text-gray-800 dark:text-gray-200;
}

.login-tabs {
  @apply w-full;
}

.form-wrapper {
  @apply flex flex-col gap-4 mt-6;
}

.form-input {
  @apply w-full;
}

.input-icon {
  @apply text-gray-400;
}

.login-button {
  @apply mt-2 h-12 text-base font-medium;
}

.form-footer {
  @apply text-center mt-4;
}

.footer-text {
  @apply text-gray-600 dark:text-gray-400 text-sm;
}

.footer-link {
  @apply text-blue-600 dark:text-blue-400 text-sm ml-1;
  @apply hover:text-blue-700 dark:hover:text-blue-300;
  @apply cursor-pointer;
}

.login-divider {
  @apply h-auto my-8 md:my-0 bg-gray-200 dark:bg-gray-700;
}

.qrcode-section {
  @apply flex items-center justify-center p-8 md:p-12 will-change-auto;
  @apply bg-gray-50 dark:bg-gray-900;
  min-width: 300px;
  max-width: 350px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-box {
    @apply flex-col;
  }

  .login-form-section {
    @apply p-6;
  }

  .qrcode-section {
    @apply p-6 w-full;
    min-width: 100%;
    max-width: 100%;
  }

  .login-divider {
    @apply w-full h-px mx-0 my-0;
  }

  .login-title {
    @apply text-xl mb-6;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .login-content {
    @apply p-2;
  }

  .login-form-section {
    @apply p-4;
  }

  .qrcode-section {
    @apply p-4;
  }
}
</style>
