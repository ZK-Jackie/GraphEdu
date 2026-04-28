<script setup lang="ts">
import { LoginOutlined, UserAddOutlined } from '@ant-design/icons-vue'

interface LoginRegisterProps {
  status: 'login' | 'register'
  redirect?: string | boolean
}

const props = withDefaults(defineProps<LoginRegisterProps>(), {
  redirect: false,
})

const router = useRouter()

// 默认配置
const defaultConfig = computed(() => {
  return props.status === 'login'
    ? {
        text: '登录',
        icon: LoginOutlined,
        path: '/login',
        tooltip: '登录到您的账户',
      }
    : {
        text: '注册',
        icon: UserAddOutlined,
        path: '/register',
        tooltip: '创建新账户',
      }
})

// 计算跳转路径
const targetPath = computed(() => {
  if (props.redirect === false) {
    return defaultConfig.value.path
  }
  if (typeof props.redirect === 'string') {
    return props.redirect
  }
  // redirect 为 true 时，添加当前路径作为回调
  return defaultConfig.value.path
})

// 点击处理
const handleClick = () => {
  if (props.redirect === true) {
    const currentPath = router.currentRoute.value.fullPath
    router.push({
      path: defaultConfig.value.path,
      query: { redirect: currentPath },
    })
  } else {
    router.push(targetPath.value)
  }
}
</script>

<template>
  <a-tooltip placement="bottom" arrow-point-at-center>
    <template #title>
      <span>{{ defaultConfig.tooltip }}</span>
    </template>
    <button class="login-register-btn" draggable="false" @click="handleClick">
      <component :is="defaultConfig.icon" class="btn-icon" />
      <span class="btn-text" draggable="false">{{ defaultConfig.text }}</span>
    </button>
  </a-tooltip>
</template>

<style scoped>
@reference "#main.css";

.login-register-btn {
  @apply w-auto h-10 rounded-md px-3 py-2
    hover:bg-gray-100 dark:hover:bg-gray-700
    cursor-pointer
    flex items-center justify-center gap-2
    border-none bg-transparent
    select-none focus:outline-none
    transition-all duration-200 ease-out;
}

.btn-icon {
  @apply text-lg text-gray-700 dark:text-gray-300 leading-none;
  transition: transform 0.2s ease-out;
}

.login-register-btn:hover .btn-icon {
  transform: scale(1.1);
}

.login-register-btn:hover .btn-text {
  @apply text-gray-800 dark:text-gray-200;
}

.btn-text {
  @apply text-sm text-gray-700 dark:text-gray-300
    font-medium
    whitespace-nowrap;
}
</style>
