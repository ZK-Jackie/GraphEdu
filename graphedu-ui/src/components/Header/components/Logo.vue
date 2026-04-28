<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
  <router-link class="logo-container" to="/">
    <img src="../../../assets/logo/logo.svg" alt="Website Logo" class="logo-img" draggable="false" />
    <h1 class="logo-h1">
      {{ t('header.nav.title') }}
    </h1>
  </router-link>
</template>

<style scoped>
@reference "#main.css";

.logo-container {
  @apply flex items-center select-none focus:outline-none;
}

.logo-img {
  @apply h-15 w-auto;
}

.logo-h1 {
  @apply text-black dark:text-gray-200 text-3xl ml-2 h-15 flex items-center mb-0;
  font-family:
    Cascadia Code SemiBold,
    Source Han Serif SC Heavy,
    monospace,
    sans-serif;
}
</style>
