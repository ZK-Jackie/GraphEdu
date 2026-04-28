<template>
  <a-modal
    :open="visible"
    :title="`${t('system.job.executionLogs')} - ${jobName}`"
    :width="900"
    :footer="null"
    @cancel="handleCancel"
  >
    <!-- 搜索表单 -->
    <a-form layout="inline" :model="queryParams" class="mb-4">
      <a-form-item :label="t('common.status')">
        <DictSelect
          v-model:model-value="queryParams.status"
          dict-type="sys_job_status"
          :placeholder="t('system.job.statusPlaceholder')"
          allow-clear
          style="width: 120px"
          @change="handleQuery"
        />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="handleQuery">
          <template #icon><SearchOutlined /></template>
          {{ t('common.search') }}
        </a-button>
        <a-button @click="resetQuery" class="ml-2">
          <template #icon><ReloadOutlined /></template>
          {{ t('common.reset') }}
        </a-button>
      </a-form-item>
      <a-form-item style="float: right">
        <a-space>
          <a-button danger :disabled="!hasLogs" @click="handleClear">
            <template #icon><ClearOutlined /></template>
            {{ t('system.job.clearLogs') }}
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <!-- 日志表格 -->
    <a-table
      :columns="columns"
      :data-source="logList"
      :loading="loading"
      :pagination="pagination"
      :scroll="{ y: 400 }"
      row-key="jobLogId"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <!-- 状态列 -->
        <template v-if="column.key === 'status'">
          <a-tag v-if="record.status === '0'" color="success">{{ t('system.job.success') }}</a-tag>
          <a-tag v-else color="error">{{ t('system.job.failed') }}</a-tag>
        </template>
        <!-- 执行信息列 -->
        <template v-else-if="column.key === 'jobMessage'">
          <a-tooltip :title="record.jobMessage">
            <span class="log-message">{{ record.jobMessage || '-' }}</span>
          </a-tooltip>
        </template>
        <!-- 异常信息列 -->
        <template v-else-if="column.key === 'exceptionInfo'">
          <a-button v-if="record.exceptionInfo" type="link" size="small" @click="showException(record as JobLogListVO)">
            {{ t('system.job.viewException') }}
          </a-button>
          <span v-else>-</span>
        </template>
        <!-- 创建时间列 -->
        <template v-else-if="column.key === 'createTime'">
          {{ parseTime(record.createTime) }}
        </template>
        <!-- 操作列 -->
        <template v-else-if="column.key === 'action'">
          <a-popconfirm
            :title="t('common.confirmDelete')"
            :ok-text="t('common.ok')"
            :cancel-text="t('common.cancel')"
            @confirm="handleDeleteLog(record.jobLogId)"
          >
            <a-button type="link" size="small" danger>
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <!-- 异常信息弹窗 -->
    <a-modal v-model:open="exceptionVisible" :title="t('system.job.exceptionInfo')" :width="700" :footer="null">
      <pre class="exception-content">{{ currentException }}</pre>
    </a-modal>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { SearchOutlined, ReloadOutlined, ClearOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { getJobLogList, deleteJobLog, clearJobLog } from '@/api/system/job.ts'
import type { JobLogQueryDTO, JobLogListVO } from '@/types/api/tool/job.ts'
import { parseTime } from '@/utils/common.ts'

const props = defineProps<{
  visible: boolean
  jobId?: number
  jobName?: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const { t } = useI18n()

// 表格列定义
const columns = [
  { title: t('system.job.logId'), dataIndex: 'jobLogId', key: 'jobLogId', width: 60 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('system.job.jobMessage'), dataIndex: 'jobMessage', key: 'jobMessage', ellipsis: true },
  { title: t('system.job.exceptionInfo'), dataIndex: 'exceptionInfo', key: 'exceptionInfo', width: 100 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: t('common.operation'), key: 'action', width: 60, fixed: 'right' as const },
]

// 数据状态
const loading = ref(false)
const logList = ref<JobLogListVO[]>([])
const total = ref(0)
const exceptionVisible = ref(false)
const currentException = ref('')

// 查询参数
const queryParams = reactive<JobLogQueryDTO>({
  page: 1,
  size: 10,
  jobId: props.jobId,
  status: undefined,
})

// 分页配置
const pagination = computed(() => ({
  current: queryParams.page,
  pageSize: queryParams.size,
  total: total.value,
  showSizeChanger: true,
  showTotal: (total: number) => `${t('common.total')} ${total} ${t('common.items')}`,
  onChange: (page: number, pageSize: number) => {
    queryParams.page = page
    queryParams.size = pageSize
    fetchLogList()
  },
}))

const hasLogs = computed(() => logList.value.length > 0)

// 获取日志列表
const fetchLogList = async () => {
  if (!props.jobId) return

  loading.value = true
  try {
    const { data } = await getJobLogList(queryParams)
    logList.value = data.rows || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

// 查询
const handleQuery = () => {
  queryParams.page = 1
  fetchLogList()
}

// 重置查询
const resetQuery = () => {
  queryParams.status = undefined
  queryParams.page = 1
  fetchLogList()
}

// 删除日志
const handleDeleteLog = async (jobLogId: number) => {
  try {
    await deleteJobLog(jobLogId.toString())
    message.success(t('common.deleteSuccess'))
    fetchLogList()
  } catch {
    message.error(t('common.deleteFailed'))
  }
}

// 清空日志
const handleClear = () => {
  Modal.confirm({
    title: t('common.confirm'),
    content: t('system.job.clearLogsConfirm'),
    onOk: async () => {
      try {
        await clearJobLog()
        message.success(t('common.clearSuccess'))
        fetchLogList()
      } catch {
        message.error(t('common.clearFailed'))
      }
    },
  })
}

// 显示异常信息
const showException = (record: JobLogListVO) => {
  currentException.value = record.exceptionInfo || ''
  exceptionVisible.value = true
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 监听弹窗显示状态
watch(
  () => props.visible,
  (val) => {
    if (val) {
      queryParams.jobId = props.jobId
      fetchLogList()
    } else {
      logList.value = []
      total.value = 0
    }
  }
)
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.log-message {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exception-content {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}
</style>
