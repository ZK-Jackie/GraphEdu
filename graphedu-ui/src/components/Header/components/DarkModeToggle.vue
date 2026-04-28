<script setup lang="ts">
import useAppStore from '@/stores/modules/app.ts'

const appStore = useAppStore()
const { darkMode } = storeToRefs(appStore)

const toggleTheme = () => {
  appStore.toggleDarkMode()
}
</script>

<template>
  <button class="nav-darkmode-item" :aria-label="darkMode ? '切换到亮色模式' : '切换到暗色模式'" @click="toggleTheme">
    <span class="nav-darkmode-toggle">
      <a-tooltip placement="bottom" arrow-point-at-center>
        <template #title>
          <span>亮暗模式切换</span>
        </template>
        <span class="nav-darkmode-icon" :class="{ dark: darkMode }"></span>
      </a-tooltip>
    </span>
  </button>
</template>

<style scoped>
@reference "#main.css";

/* 主题切换按钮 */
.nav-darkmode-toggle {
  @apply relative rounded flex items-center justify-center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  outline: none;
  appearance: none;
}

.nav-darkmode-icon {
  @apply relative rounded-full;
  width: 24px;
  height: 24px;
  transition: all 0.45s ease;
  background-color: black;
}

.nav-darkmode-icon::before {
  content: '';
  @apply absolute rounded-full;
  right: -3px;
  top: -3px;
  height: 18px;
  width: 18px;
  transition:
    transform 0.5s ease-in,
    opacity 0.5s ease-in;
  opacity: 1;
  background-color: #fff;
  transform: translate(0, 0);
  box-shadow: 0 0 0 0 transparent;
}

.nav-darkmode-item:hover .nav-darkmode-icon::before {
  background-color: rgb(243 244 246); /* gray-100*/
}

.nav-darkmode-item:hover .nav-darkmode-icon {
  transform: scale(1.1);
}

.nav-darkmode-item:hover .nav-darkmode-icon.dark {
  transform: scale(0.6);
}

.nav-darkmode-icon::after {
  content: '';
  @apply absolute rounded-full;
  width: 8px;
  height: 8px;
  margin: -4px 0 0 -4px;
  top: 50%;
  left: 50%;
  transition: all 0.35s ease;
  transform: scale(0);
  box-shadow:
    0 -23px 0 rgb(55 65 81),
    0 23px 0 rgb(55 65 81),
    23px 0 0 rgb(55 65 81),
    -23px 0 0 rgb(55 65 81),
    15px 15px 0 rgb(55 65 81),
    -15px 15px 0 rgb(55 65 81),
    15px -15px 0 rgb(55 65 81),
    -15px -15px 0 rgb(55 65 81);
}

/* 暗色模式状态 - 修复白色圆圈显露问题 */
.nav-darkmode-icon.dark {
  border: 4px solid rgb(229 231 235);
  background-color: rgb(229 231 235);
  transform: scale(0.55);
  overflow: visible;
  box-shadow: none;
}

.nav-darkmode-icon.dark::before {
  transform: translate(14px, -14px);
  opacity: 0;
  background-color: rgb(55 65 81);
}

.nav-darkmode-icon.dark::after {
  transform: scale(1);
  box-shadow:
    0 -23px 0 rgb(229 231 235),
    0 23px 0 rgb(229 231 235),
    23px 0 0 rgb(229 231 235),
    -23px 0 0 rgb(229 231 235),
    15px 15px 0 rgb(229 231 235),
    -15px 15px 0 rgb(229 231 235),
    15px -15px 0 rgb(229 231 235),
    -15px -15px 0 rgb(229 231 235);
}

.nav-darkmode-item:hover .nav-darkmode-toggle {
  @apply cursor-pointer;
}
</style>
