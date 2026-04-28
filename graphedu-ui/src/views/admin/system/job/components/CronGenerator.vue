<template>
  <a-modal
    :open="visible"
    :title="t('system.job.cronGenerator')"
    :width="600"
    @ok="handleConfirm"
    @cancel="handleCancel"
  >
    <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
      <a-form-item :label="t('system.job.preset')">
        <a-space direction="vertical" style="width: 100%">
          <a-radio-group v-model:value="preset" button-style="solid" @change="handlePresetChange">
            <a-radio-button value="everyMinute">{{ t('system.job.everyMinute') }}</a-radio-button>
            <a-radio-button value="everyHour">{{ t('system.job.everyHour') }}</a-radio-button>
            <a-radio-button value="everyDay">{{ t('system.job.everyDay') }}</a-radio-button>
            <a-radio-button value="everyWeek">{{ t('system.job.everyWeek') }}</a-radio-button>
            <a-radio-button value="everyMonth">{{ t('system.job.everyMonth') }}</a-radio-button>
          </a-radio-group>
        </a-space>
      </a-form-item>

      <a-divider />

      <a-form-item :label="t('system.job.minute')">
        <a-select v-model:value="config.minute" style="width: 100%" @change="updateCron">
          <a-select-option value="*">{{ t('system.job.every') }}</a-select-option>
          <a-select-option value="0">{{ t('system.job.atMinute', { minute: 0 }) }}</a-select-option>
          <a-select-option value="5">{{ t('system.job.atMinute', { minute: 5 }) }}</a-select-option>
          <a-select-option value="15">{{ t('system.job.atMinute', { minute: 15 }) }}</a-select-option>
          <a-select-option value="30">{{ t('system.job.atMinute', { minute: 30 }) }}</a-select-option>
          <a-select-option value="custom">{{ t('system.job.custom') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('system.job.hour')">
        <a-select v-model:value="config.hour" style="width: 100%" @change="updateCron">
          <a-select-option value="*">{{ t('system.job.every') }}</a-select-option>
          <a-select-option value="0">{{ t('system.job.atHour', { hour: 0 }) }}</a-select-option>
          <a-select-option value="1">{{ t('system.job.atHour', { hour: 1 }) }}</a-select-option>
          <a-select-option value="6">{{ t('system.job.atHour', { hour: 6 }) }}</a-select-option>
          <a-select-option value="12">{{ t('system.job.atHour', { hour: 12 }) }}</a-select-option>
          <a-select-option value="custom">{{ t('system.job.custom') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('system.job.day')">
        <a-select v-model:value="config.day" style="width: 100%" @change="updateCron">
          <a-select-option value="*">{{ t('system.job.every') }}</a-select-option>
          <a-select-option value="1">{{ t('system.job.atDay', { day: 1 }) }}</a-select-option>
          <a-select-option value="15">{{ t('system.job.atDay', { day: 15 }) }}</a-select-option>
          <a-select-option value="?">{{ t('system.job.unspecified') }}</a-select-option>
          <a-select-option value="custom">{{ t('system.job.custom') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('system.job.month')">
        <a-select v-model:value="config.month" style="width: 100%" @change="updateCron">
          <a-select-option value="*">{{ t('system.job.every') }}</a-select-option>
          <a-select-option value="1">{{ t('system.job.atMonth', { month: 1 }) }}</a-select-option>
          <a-select-option value="4">{{ t('system.job.atMonth', { month: 4 }) }}</a-select-option>
          <a-select-option value="7">{{ t('system.job.atMonth', { month: 7 }) }}</a-select-option>
          <a-select-option value="10">{{ t('system.job.atMonth', { month: 10 }) }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('system.job.dayOfWeek')">
        <a-select v-model:value="config.dayOfWeek" style="width: 100%" @change="updateCron">
          <a-select-option value="*">{{ t('system.job.every') }}</a-select-option>
          <a-select-option value="?">{{ t('system.job.unspecified') }}</a-select-option>
          <a-select-option value="1">{{ t('system.job.monday') }}</a-select-option>
          <a-select-option value="2">{{ t('system.job.tuesday') }}</a-select-option>
          <a-select-option value="3">{{ t('system.job.wednesday') }}</a-select-option>
          <a-select-option value="4">{{ t('system.job.thursday') }}</a-select-option>
          <a-select-option value="5">{{ t('system.job.friday') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-divider />

      <a-form-item :label="t('system.job.expression')">
        <a-input v-model:value="cronExpression" readonly style="font-family: 'Courier New', monospace" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: [cron: string]
}>()

const { t } = useI18n()

const preset = ref('everyDay')
const cronExpression = ref('0 0 0 * * ?')

const config = reactive({
  minute: '0',
  hour: '0',
  day: '*',
  month: '*',
  dayOfWeek: '?',
})

// 预设选项变化
const handlePresetChange = () => {
  switch (preset.value) {
    case 'everyMinute':
      config.minute = '*'
      config.hour = '*'
      config.day = '*'
      config.month = '*'
      config.dayOfWeek = '?'
      break
    case 'everyHour':
      config.minute = '0'
      config.hour = '*'
      config.day = '*'
      config.month = '*'
      config.dayOfWeek = '?'
      break
    case 'everyDay':
      config.minute = '0'
      config.hour = '0'
      config.day = '*'
      config.month = '*'
      config.dayOfWeek = '?'
      break
    case 'everyWeek':
      config.minute = '0'
      config.hour = '0'
      config.day = '?'
      config.month = '*'
      config.dayOfWeek = '1'
      break
    case 'everyMonth':
      config.minute = '0'
      config.hour = '0'
      config.day = '1'
      config.month = '*'
      config.dayOfWeek = '?'
      break
  }
  updateCron()
}

// 更新 Cron 表达式
const updateCron = () => {
  const minute = config.minute === 'custom' ? '0' : config.minute
  const hour = config.hour === 'custom' ? '0' : config.hour
  const day = config.day === 'custom' ? '*' : config.day
  const month = config.month === 'custom' ? '*' : config.month
  const dayOfWeek = config.dayOfWeek === 'custom' ? '?' : config.dayOfWeek

  cronExpression.value = `${minute} ${hour} ${day} ${month} ${dayOfWeek} ?`
}

// 确认
const handleConfirm = () => {
  emit('confirm', cronExpression.value)
  handleCancel()
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
  // 重置为默认状态
  preset.value = 'everyDay'
  handlePresetChange()
}

// 监听弹窗显示状态
watch(
  () => props.visible,
  (val) => {
    if (val) {
      handlePresetChange()
    }
  }
)
</script>

<style scoped>
:deep(.ant-divider-horizontal) {
  margin: 12px 0;
}
</style>
