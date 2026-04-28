import { createI18n } from 'vue-i18n'
import zhMessages from '@/locales/zh'
import enMessages from '@/locales/en'

/**
 * i18n plugin for Vue 3 applications.
 *
 * Translations are loaded from modular JSON files under `locales/zh/` and `locales/en/`.
 * Each file's name becomes a top-level namespace (e.g. `common.json` → `common.*`).
 *
 * @example
 * <script setup>
 * import { useI18n } from 'vue-i18n'
 * const { t } = useI18n()
 * </script>
 *
 * <template>
 *   <h1>{{ t("common.search") }}</h1>
 * </template>
 * @see https://vue-i18n.intlify.dev/guide/essentials/syntax.html#composition-api
 */
export const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  fallbackLocale: 'en',
  messages: {
    zh: zhMessages,
    en: enMessages,
  },
  warnHtmlMessage: false, // 禁用 HTML 消息警告（用于显示特殊字符如 < > 等）
})
