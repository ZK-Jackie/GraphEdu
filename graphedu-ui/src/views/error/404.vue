<script setup lang="ts">
import { useRouter } from 'vue-router'
import { SearchOutlined, HomeOutlined, ArrowLeftOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}

const searchKeyword = ref('')

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    console.log('搜索:', searchKeyword.value)
    // TODO: 实现搜索功能
  }
}
</script>

<template>
  <div class="error-page">
    <div class="error-container">
      <!-- 404 图标 -->
      <div class="error-icon">
        <div class="error-number">404</div>
        <div class="error-decoration">
          <span class="decoration-item">🔍</span>
          <span class="decoration-item">📄</span>
          <span class="decoration-item">❓</span>
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="error-content">
        <h1 class="error-title">页面不存在</h1>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被移除。
          <br />
          请检查网址是否正确，或返回首页继续浏览。
        </p>

        <!-- 搜索框 -->
        <div class="search-box">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索页面或内容..."
            size="large"
            @search="handleSearch"
          >
            <template #enterButton>
              <a-button type="primary">
                <template #icon>
                  <SearchOutlined />
                </template>
                搜索
              </a-button>
            </template>
          </a-input-search>
        </div>

        <!-- 操作按钮 -->
        <div class="error-actions">
          <a-space :size="16">
            <a-button type="primary" size="large" @click="goHome">
              <template #icon>
                <HomeOutlined />
              </template>
              返回首页
            </a-button>
            <a-button size="large" @click="goBack">
              <template #icon>
                <ArrowLeftOutlined />
              </template>
              返回上一页
            </a-button>
          </a-space>
        </div>

        <!-- 常用链接 -->
        <div class="quick-links">
          <h3>您可能需要：</h3>
          <a-space :size="[16, 16]" wrap>
            <a-button type="link" @click="router.push('/')">首页</a-button>
            <a-button type="link" @click="router.push('/workbench')">工作台</a-button>
            <a-button type="link" @click="router.push('/about')">关于我们</a-button>
            <a-button type="link" @click="router.push('/help')">帮助中心</a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="decoration-circle circle-1"></div>
      <div class="decoration-circle circle-2"></div>
      <div class="decoration-circle circle-3"></div>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  padding: 24px;
}

.error-container {
  position: relative;
  z-index: 1;
  max-width: 600px;
  width: 100%;
  background: white;
  border-radius: 16px;
  padding: 48px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

/* 404 图标 */
.error-icon {
  position: relative;
  margin-bottom: 32px;
}

.error-number {
  font-size: 120px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
  margin-bottom: 16px;
  animation: float 3s ease-in-out infinite;
}

.error-decoration {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.decoration-item {
  font-size: 32px;
  animation: bounce 2s ease-in-out infinite;
}

.decoration-item:nth-child(2) {
  animation-delay: 0.2s;
}

.decoration-item:nth-child(3) {
  animation-delay: 0.4s;
}

/* 错误内容 */
.error-content {
  margin-top: 24px;
}

.error-title {
  font-size: 32px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.error-description {
  font-size: 16px;
  color: #666;
  line-height: 1.6;
  margin: 0 0 32px 0;
}

/* 搜索框 */
.search-box {
  margin-bottom: 32px;
}

/* 操作按钮 */
.error-actions {
  margin-bottom: 32px;
}

/* 快捷链接 */
.quick-links {
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.quick-links h3 {
  font-size: 14px;
  color: #999;
  margin: 0 0 16px 0;
  font-weight: normal;
}

/* 背景装饰 */
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -100px;
  animation: float 6s ease-in-out infinite;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
  animation: float 8s ease-in-out infinite reverse;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: 10%;
  animation: float 7s ease-in-out infinite;
}

/* 动画 */
@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .error-container {
    padding: 32px 24px;
  }

  .error-number {
    font-size: 80px;
  }

  .error-title {
    font-size: 24px;
  }

  .error-description {
    font-size: 14px;
  }

  .decoration-item {
    font-size: 24px;
  }

  .error-actions {
    margin-bottom: 24px;
  }

  .error-actions :deep(.ant-space) {
    flex-direction: column;
    width: 100%;
  }

  .error-actions :deep(.ant-btn) {
    width: 100%;
  }
}
</style>
