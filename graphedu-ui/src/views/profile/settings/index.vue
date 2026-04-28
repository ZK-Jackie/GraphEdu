<template>
  <a-card :bordered="true">
    <template #title>
      <span>{{ t('settings.title') }}</span>
    </template>

    <div class="settings-content">
      <a-form :label-col="formLayout.labelCol" :wrapper-col="formLayout.wrapperCol">
        <!-- 界面语言 -->
        <a-form-item :label="t('settings.language.label')">
          <a-radio-group v-model:value="language" button-style="solid">
            <a-radio-button value="zh">{{ t('settings.language.zh') }}</a-radio-button>
            <a-radio-button value="en">{{ t('settings.language.en') }}</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <!-- 时区设置 -->
        <a-form-item :label="t('settings.timezone.label')">
          <a-select v-model:value="timeConfig.timezone" class="settings-select" :options="timezoneOptions" />
        </a-form-item>

        <!-- 时间格式 -->
        <a-form-item :label="t('settings.timeFormat.label')">
          <a-select v-model:value="timeConfig.format" class="settings-select" :options="formatOptions" />
          <div class="format-preview">
            <span class="preview-label">{{ t('settings.timeFormat.preview') }}：</span>
            <span class="preview-value">{{ formatPreview }}</span>
          </div>
        </a-form-item>

        <!-- 相对时间 -->
        <a-form-item :label="t('settings.relativeTime.label')">
          <a-switch v-model:checked="timeConfig.relativeTime" />
          <div class="help-text">{{ t('settings.relativeTime.help') }}</div>
          <div class="format-preview">
            <span class="preview-label">{{ t('settings.timeFormat.preview') }}：</span>
            <span class="preview-value">{{ relativePreview }}</span>
          </div>
        </a-form-item>

        <!-- 操作按钮 -->
        <a-form-item v-bind="submitLayout">
          <a-space>
            <a-button type="primary" @click="handleSave">{{ t('settings.save') }}</a-button>
            <a-button @click="handleReset">{{ t('common.reset') }}</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import useAppStore from '@/stores/modules/app'
import { useTime } from '@/composables/useTime'
import { useBreakpoints } from '@/composables/useBreakpoints'
import type { TimeConfig } from '@/types/stores/app'
import { SystemMessage } from '@/utils/message'

const { isMobile } = useBreakpoints()

const formLayout = computed(() =>
  isMobile.value
    ? { labelCol: { span: 24 }, wrapperCol: { span: 24 } }
    : { labelCol: { span: 6 }, wrapperCol: { span: 14 } }
)

const submitLayout = computed(() =>
  isMobile.value ? { wrapperCol: { span: 24 } } : { wrapperCol: { span: 14, offset: 6 } }
)

const { t } = useI18n()
const appStore = useAppStore()
const { formatUtcTime, previewFormat } = useTime()

// 语言设置
const language = ref(appStore.locale)

// 时间配置
const timeConfig = reactive<TimeConfig>({ ...appStore.timeConfig })

// 时区选项
const timezoneOptions = [
  { label: '自动', value: 'auto' },
  { label: 'UTC', value: 'UTC' },
  { label: 'Asia/Shanghai (中国标准时间)', value: 'Asia/Shanghai' },
  { label: 'America/New_York (美东时间)', value: 'America/New_York' },
  { label: 'America/Los_Angeles (美西时间)', value: 'America/Los_Angeles' },
  { label: 'Europe/London (格林威治时间)', value: 'Europe/London' },
  { label: 'Asia/Tokyo (日本时间)', value: 'Asia/Tokyo' },
]

// 时间格式选项
const formatOptions = [
  { label: 'YYYY-MM-DD HH:mm:ss', value: 'YYYY-MM-DD HH:mm:ss' },
  { label: 'YYYY-MM-DD HH:mm', value: 'YYYY-MM-DD HH:mm' },
  { label: 'YYYY年MM月DD日 HH:mm:ss', value: 'YYYY年MM月DD日 HH:mm:ss' },
  { label: 'MM/DD/YYYY HH:mm:ss', value: 'MM/DD/YYYY HH:mm:ss' },
  { label: 'DD/MM/YYYY HH:mm:ss', value: 'DD/MM/YYYY HH:mm:ss' },
]

// 格式预览
const formatPreview = computed(() => {
  return previewFormat(timeConfig.format)
})

// 相对时间预览
const relativePreview = computed(() => {
  const now = new Date()
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000).toISOString()
  return formatUtcTime(oneHourAgo)
})

// 保存设置
const handleSave = () => {
  appStore.updateLocale(language.value)
  appStore.updateTimeConfig(timeConfig)
  SystemMessage({ theme: 'success', content: t('settings.saveSuccess') })
}

// 重置设置
const handleReset = () => {
  language.value = 'zh'
  timeConfig.format = 'YYYY-MM-DD HH:mm:ss'
  timeConfig.relativeTime = false
  timeConfig.timezone = 'auto'
  SystemMessage({ theme: 'info', content: t('settings.resetSuccess') })
}
</script>

<style scoped>
@reference "#main.css";

.settings-content {
  max-width: 800px;
}

.settings-select {
  @apply w-full;
  max-width: 300px;
}

@media (max-width: 767px) {
  .settings-select {
    max-width: 100%;
  }
}

.format-preview {
  margin-top: 8px;
  font-size: 14px;
  color: var(--ge-text-secondary);
}

.preview-label {
  margin-right: 8px;
}

.preview-value {
  font-family: 'Courier New', monospace;
  color: var(--ge-primary);
}

.help-text {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ge-text-tertiary);
}
</style>
