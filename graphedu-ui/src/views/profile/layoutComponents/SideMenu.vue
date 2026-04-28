<template>
  <a-menu
    v-model:selected-keys="selectedKeys"
    mode="inline"
    :style="{ borderRight: 0 }"
    :items="menuItems"
    @click="handleMenuClick"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { MenuProps } from 'ant-design-vue'
import { getActiveMenuKeys } from '@/router/utils.ts'
import useFunctionStore from '@/stores/modules/function.ts'

const router = useRouter()
const route = useRoute()
const functionStore = useFunctionStore()

const selectedKeys = ref<string[]>([])

/**
 * 获取菜单项
 * 从 function store 获取 web 场景的顶部菜单配置
 */
const menuItems = computed(() => {
  return (functionStore.userInfoMenuItems[0] as any)?.children ?? []
})

// 点击菜单项进行路由跳转
const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
  router.push({ name: key as string })
}

/**
 * 根据当前路由更新选中的菜单项
 */
watch(
  () => route.matched,
  (matched) => {
    selectedKeys.value = getActiveMenuKeys(matched)
  },
  { immediate: true }
)
</script>
