<template>
  <div class="profile-layout">
    <!-- 移动端：顶部 Tabs 导航 -->
    <template v-if="isMobile">
      <a-tabs v-model:activeKey="activeTab" class="profile-tabs" @change="handleTabChange">
        <a-tab-pane v-for="item in tabItems" :key="item.key" :tab="item.label" />
      </a-tabs>
      <div class="content-wrapper">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </div>
    </template>

    <!-- 桌面端：左侧导航 + 右侧内容 -->
    <template v-else>
      <a-row :gutter="16">
        <a-col :span="6" :xs="24" :lg="6">
          <a-card :bordered="true" class="nav-card">
            <template #title>
              <span class="nav-title">个人中心</span>
            </template>
            <SideMenu />
          </a-card>
        </a-col>

        <a-col :span="18" :xs="24" :lg="18">
          <div class="content-wrapper">
            <router-view v-slot="{ Component, route }">
              <transition name="fade-slide" mode="out-in">
                <component :is="Component" :key="route.path" />
              </transition>
            </router-view>
          </div>
        </a-col>
      </a-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SideMenu from './SideMenu.vue'
import { useBreakpoints } from '@/composables/useBreakpoints'
import useFunctionStore from '@/stores/modules/function.ts'

const router = useRouter()
const route = useRoute()
const functionStore = useFunctionStore()
const { isMobile } = useBreakpoints()

const tabItems = computed(() => {
  return (functionStore.userInfoMenuItems[0] as any)?.children ?? []
})

const activeTab = ref<string>('')

const handleTabChange = (key: string | number) => {
  router.push({ name: key as any })
}

watch(
  () => route.name,
  (name) => {
    if (name) {
      activeTab.value = name as string
    }
  },
  { immediate: true }
)
</script>

<style scoped>
@reference "#main.css";

.profile-layout {
  padding: 16px;

  .nav-card {
    min-height: 400px;

    :deep(.ant-card-head) {
      border-bottom: 1px solid var(--ge-border-color);
    }

    .nav-title {
      font-size: 16px;
      font-weight: 600;
    }

    :deep(.ant-menu-inline) {
      border-right: none;
    }

    :deep(.ant-menu-item) {
      margin: 4px 0;
      height: 44px;
      line-height: 44px;
      border-radius: 6px;

      &:hover {
        background-color: var(--ge-bg-elevated);
      }

      &.ant-menu-item-selected {
        background-color: var(--ge-primary-light);
        color: var(--ge-primary);
      }
    }
  }

  .content-wrapper {
    min-height: 400px;
  }

  .profile-tabs {
    background: var(--ge-bg-container);
    border-radius: 8px;
    padding: 0 12px;
    margin-bottom: 16px;

    :deep(.ant-tabs-nav) {
      margin-bottom: 0;

      &::before {
        border-bottom: none;
      }
    }

    :deep(.ant-tabs-tab) {
      padding: 12px 8px;
      font-size: 14px;
    }
  }
}

/* 页面切换动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(16px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

@media (max-width: 768px) {
  .profile-layout {
    padding: 8px;
  }
}
</style>
