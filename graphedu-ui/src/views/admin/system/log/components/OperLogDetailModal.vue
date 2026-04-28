<template>
  <a-modal
    :open="visible"
    :title="t('system.log.operation.detailModal')"
    :footer="null"
    width="800px"
    @cancel="handleCancel"
  >
    <a-spin :spinning="loading">
      <a-descriptions bordered :column="2">
        <a-descriptions-item :label="t('system.log.operation.moduleName')" :span="2">
          {{ currentLog.title }} / {{ typeFormat(currentLog) }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.loginInfo')" :span="2">
          {{ currentLog.operName }} / {{ currentLog.operIp }} / {{ currentLog.operLocation }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.requestAddress')" :span="2">
          {{ currentLog.operUrl || '-' }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.requestMethod')" :span="2">
          {{ currentLog.requestMethod }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.operMethod')" :span="2">
          {{ currentLog.method }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.requestParam')" :span="2">
          <pre class="log-content">{{ currentLog.operParam || '-' }}</pre>
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.jsonResult')" :span="2">
          <pre class="log-content">{{ currentLog.jsonResult || '-' }}</pre>
        </a-descriptions-item>
        <a-descriptions-item :label="t('common.status')">
          <a-tag v-if="currentLog.status === 0" color="success">{{ t('common.normal') }}</a-tag>
          <a-tag v-else-if="currentLog.status === 1" color="error">{{ t('system.log.operation.detailFailed') }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.costTime')">
          {{ currentLog.costTime }}{{ t('system.log.operation.costTimeUnit') }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('system.log.operation.operateTime')" :span="2">
          {{ formatTime(currentLog.operTime) }}
        </a-descriptions-item>
        <a-descriptions-item v-if="currentLog.status === 1" :label="t('system.log.operation.exceptionInfo')" :span="2">
          <pre class="log-content error">{{ currentLog.errorMsg || '-' }}</pre>
        </a-descriptions-item>
      </a-descriptions>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getOperationLogDetail } from '@/api/system/log.ts'
import type { OperLogDetailVO } from '@/types/api/system/log.ts'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'

const { t } = useI18n()

interface Props {
  visible: boolean
  operId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 获取字典数据
const { sys_oper_log_oper_type } = useDict('sys_oper_log_oper_type')

const loading = ref(false)
const currentLog = ref<OperLogDetailVO>({} as OperLogDetailVO)

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 操作日志类型字典翻译
const typeFormat = (row: OperLogDetailVO) => {
  const dict = sys_oper_log_oper_type?.value?.find((d) => d.value === String(row.businessType))
  return dict?.label ?? ''
}

// 获取操作日志详情
const fetchDetail = async () => {
  if (!props.operId) return

  loading.value = true
  try {
    const res = await getOperationLogDetail(props.operId)
    if (res.code === 200) {
      currentLog.value = res.data
    }
  } catch (_e) {
    message.error(t('system.log.operation.getOperationLogDetailFailed'))
  } finally {
    loading.value = false
  }
}

// 监听 visible 变化
watch(
  () => props.visible,
  (val) => {
    if (val && props.operId) {
      fetchDetail()
    }
  }
)

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.log-content {
  margin: 0;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  font-family: 'Courier New', Courier, monospace;

  &.error {
    color: #ff4d4f;
  }
}
</style>
