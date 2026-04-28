<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { QrcodeOutlined, ReloadOutlined } from '@ant-design/icons-vue'

// State
const qrCodeUrl = ref('')
const loading = ref(false)
const expired = ref(false)
const scanned = ref(false)
let pollingTimer: number | null = null

// Methods
const generateQRCode = async () => {
  loading.value = true
  expired.value = false
  scanned.value = false

  // TODO: 调用后端API生成二维码
  // 这里先用占位图片
  setTimeout(() => {
    qrCodeUrl.value = `https://api.2dcode.biz/v1/create-qr-code?data=%20Example`
    loading.value = false
    startPolling()
  }, 300)
}

const startPolling = () => {
  // 模拟轮询检查二维码状态
  // TODO: 实际应该调用后端API检查状态
  pollingTimer = window.setInterval(() => {
    // 模拟30秒后过期
    const random = Math.random()
    if (random > 0.95) {
      expired.value = true
      stopPolling()
    } else if (random > 0.9) {
      scanned.value = true
    }
  }, 300)
}

const stopPolling = () => {
  if (pollingTimer !== null) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const refresh = () => {
  stopPolling()
  generateQRCode()
}

// Lifecycle
onMounted(() => {
  generateQRCode()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="qrcode-login-container">
    <div class="qrcode-title">
      <QrcodeOutlined class="title-icon" />
      <span>扫码登录</span>
    </div>

    <div class="qrcode-wrapper">
      <a-spin :spinning="loading" size="large">
        <div class="qrcode-content">
          <img
            v-if="qrCodeUrl && !expired"
            :src="qrCodeUrl"
            alt="二维码"
            class="qrcode-image"
            :class="{ 'qrcode-scanned': scanned }"
          />

          <!-- 过期遮罩 -->
          <div v-if="expired" class="qrcode-overlay">
            <div class="overlay-content">
              <p class="overlay-text">二维码已过期</p>
              <a-button type="primary" @click="refresh">
                <template #icon>
                  <ReloadOutlined />
                </template>
                刷新
              </a-button>
            </div>
          </div>

          <!-- 已扫描提示 -->
          <div v-if="scanned && !expired" class="scanned-tip">
            <p>已扫描</p>
            <p class="tip-sub">请在手机上确认登录</p>
          </div>
        </div>
      </a-spin>
    </div>

    <div class="qrcode-tips">
      <p class="tip-item">使用手机扫描二维码</p>
      <p class="tip-item">快速安全登录</p>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.qrcode-login-container {
  @apply flex flex-col items-center justify-center p-6;
}

.qrcode-title {
  @apply flex items-center gap-2 mb-6 text-lg font-medium;
  @apply text-gray-700 dark:text-gray-200;
}

.title-icon {
  @apply text-xl;
}

.qrcode-wrapper {
  @apply mb-4;
}

.qrcode-content {
  @apply relative w-52 h-52 flex items-center justify-center;
  @apply bg-white dark:bg-gray-800 rounded-lg border-2 border-gray-200 dark:border-gray-700;
}

.qrcode-image {
  @apply w-48 h-48 rounded;
  transition: opacity 0.3s;
}

.qrcode-scanned {
  @apply opacity-50;
}

.qrcode-overlay {
  @apply absolute inset-0 flex items-center justify-center;
  @apply bg-gray-900 rounded-lg;
}

.overlay-content {
  @apply flex flex-col items-center gap-3;
}

.overlay-text {
  @apply text-gray-200 text-base font-medium mb-0;
}

.scanned-tip {
  @apply absolute inset-0 flex flex-col items-center justify-center;
  @apply bg-green-400 opacity-80 rounded-lg text-gray-50;
}

.tip-sub {
  @apply text-sm mt-1 mb-0;
}

.qrcode-tips {
  @apply text-center;
}

.tip-item {
  @apply text-sm text-gray-500 dark:text-gray-400 mb-1;
}

.tip-item:last-child {
  @apply mb-0;
}
</style>
