<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.job.jobName')">
            <a-input
              v-model:value="queryParams.jobName"
              :placeholder="t('system.job.jobNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.job.jobGroup')">
            <DictSelect
              v-model:model-value="queryParams.jobGroup"
              dict-type="sys_job_group"
              :placeholder="t('system.job.jobGroupPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('system.job.jobExecutor')">
            <DictSelect
              v-model:model-value="queryParams.jobExecutor"
              dict-type="sys_job_executor"
              :placeholder="t('system.job.jobExecutorPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_job_status"
              :placeholder="t('system.job.statusPlaceholder')"
              allow-clear
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" @click="handleQuery">
                <template #icon><SearchOutlined /></template>
                {{ t('common.search') }}
              </a-button>
              <a-button @click="resetQuery">
                <template #icon><ReloadOutlined /></template>
                {{ t('common.reset') }}
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>
    </template>

    <!-- 操作按钮 -->
    <template #actions>
      <a-space>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          {{ t('common.add') }}
        </a-button>
        <a-button type="default" danger :disabled="multiple" @click="handleDelete">
          <template #icon><DeleteOutlined /></template>
          {{ t('common.delete') }}
        </a-button>
      </a-space>
    </template>

    <!-- 任务表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="jobList"
        :loading="loading"
        :row-selection="rowSelection as any"
        :pagination="false"
        row-key="jobId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 任务分组列 -->
          <template v-if="column.key === 'jobGroup'">
            <DictTag :value="record.jobGroup" dict-type="sys_job_group" />
          </template>
          <!-- 执行器类型列 -->
          <template v-else-if="column.key === 'jobExecutor'">
            <DictTag :value="record.jobExecutor" dict-type="sys_job_executor" />
          </template>
          <!-- Cron表达式列 -->
          <template v-else-if="column.key === 'cronExpression'">
            <a-tooltip :title="record.cronExpression">
              <span class="cron-text">{{ record.cronExpression }}</span>
            </a-tooltip>
          </template>
          <!-- 执行策略列 -->
          <template v-else-if="column.key === 'misfirePolicy'">
            <DictTag :value="record.misfirePolicy" dict-type="sys_job_misfire_policy" />
          </template>
          <!-- 并发列 -->
          <template v-else-if="column.key === 'concurrent'">
            <DictTag :value="record.concurrent" dict-type="sys_job_concurrent" />
          </template>
          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <a-switch
              :checked="record.status === '0'"
              :checked-children="t('common.normal')"
              :un-checked-children="t('common.paused')"
              @change="(checked: any) => handleStatusChange(record as JobListVO, checked)"
            />
          </template>
          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('system.job.copyWebhookUrl')">
                <a-button type="link" size="small" @click="handleCopyWebhookUrl(record as JobListVO)">
                  <template #icon><LinkOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" @click="handleUpdate(record as JobListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.job.executeOnce')">
                <a-button type="link" size="small" @click="handleExecute(record as JobListVO)">
                  <template #icon><PlayCircleOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.job.viewLogs')">
                <a-button type="link" size="small" @click="handleViewLogs(record as JobListVO)">
                  <template #icon><FileTextOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.delete')">
                <a-button type="link" size="small" danger @click="handleDelete(record as JobListVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </template>

    <!-- 分页 -->
    <template #pagination>
      <a-pagination
        v-model:current="queryParams.page"
        v-model:page-size="queryParams.size"
        :total="total"
        :show-size-changer="true"
        :show-total="(total) => `${t('common.total')} ${total} ${t('common.items')}`"
        @change="handlePageChange"
      />
    </template>
  </TablePageLayout>

  <!-- 任务表单弹窗 -->
  <JobForm v-model:visible="formVisible" :job-id="currentJobId" @success="handleFormSuccess" />

  <!-- 任务日志弹窗 -->
  <JobLog v-model:visible="logVisible" :job-id="currentJobId" :job-name="currentJobName" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  FileTextOutlined,
  LinkOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getJobList, deleteJob, changeJobStatus, executeJobOnce } from '@/api/system/job.ts'
import type { JobQueryDTO, JobListVO } from '@/types/api/tool/job.ts'
import JobForm from './components/JobForm.vue'
import JobLog from './components/JobLog.vue'
import { formatTime } from '@/utils/common.ts'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'
import TablePageLayout from '@/layout/TablePageLayout.vue'

const { t } = useI18n()

// 表格列定义
const columns = [
  { title: t('system.job.jobId'), dataIndex: 'jobId', key: 'jobId', width: 80, fixed: 'left' as const },
  { title: t('system.job.jobName'), dataIndex: 'jobName', key: 'jobName', width: 150 },
  { title: t('system.job.jobGroup'), dataIndex: 'jobGroup', key: 'jobGroup', width: 100 },
  { title: t('system.job.jobExecutor'), dataIndex: 'jobExecutor', key: 'jobExecutor', width: 100 },
  { title: t('system.job.invokeTarget'), dataIndex: 'invokeTarget', key: 'invokeTarget', width: 200, ellipsis: true },
  { title: t('system.job.cronExpression'), dataIndex: 'cronExpression', key: 'cronExpression', width: 120 },
  { title: t('system.job.misfirePolicy'), dataIndex: 'misfirePolicy', key: 'misfirePolicy', width: 100 },
  { title: t('system.job.concurrent'), dataIndex: 'concurrent', key: 'concurrent', width: 80 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 200 },
]

// 数据状态
const loading = ref(false)
const jobList = ref<JobListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: JobQueryDTO = {
  page: 1,
  size: 10,
  jobName: undefined,
  jobGroup: undefined,
  jobExecutor: undefined,
  status: undefined,
}

// 临时存储查询参数（在 fetchJobList 中使用）
let queryParams: JobQueryDTO = { ...defaultQueryParams }

// 获取任务列表
const fetchJobList = async () => {
  loading.value = true
  try {
    const { data } = await getJobList(queryParams)
    jobList.value = data.rows || []
    total.value = data.total || 0
  } catch {
    jobList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 使用 usePaginationQuery Hook 管理查询参数
const {
  queryParams: syncedQueryParams,
  resetPage,
  resetAll,
  fetch,
} = usePaginationQuery<JobQueryDTO>(defaultQueryParams, fetchJobList, {
  syncSearchParams: true,
  searchParamKeys: ['jobName', 'jobGroup', 'jobExecutor', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<JobListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[], rows: JobListVO[]) => {
    selectedRowKeys.value = keys
    selectedRows.value = rows
  },
}))

// 弹窗状态
const formVisible = ref(false)
const logVisible = ref(false)
const currentJobId = ref<number | undefined>(undefined)
const currentJobName = ref<string>('')

// 查询
const handleQuery = () => {
  queryParams.page = 1
  fetchJobList()
}

// 重置查询
const resetQuery = () => {
  resetAll()
  fetch()
}

// 分页变化
const handlePageChange = () => {
  fetchJobList()
}

// 新增
const handleAdd = () => {
  currentJobId.value = undefined
  formVisible.value = true
}

// 修改
const handleUpdate = (record: JobListVO) => {
  currentJobId.value = record.jobId
  formVisible.value = true
}

// 删除
const handleDelete = async (record?: any) => {
  const jobIds = record ? [record.jobId] : selectedRowKeys.value
  if (jobIds.length === 0) {
    return
  }

  Modal.confirm({
    title: t('common.confirm'),
    content: t('system.job.deleteConfirm'),
    onOk: async () => {
      try {
        await deleteJob(jobIds.join(','))
        message.success(t('common.deleteSuccess'))
        fetchJobList()
      } catch {
        message.error(t('common.deleteFailed'))
      }
    },
  })
}

// 状态变更
const handleStatusChange = async (record: JobListVO, checked: boolean) => {
  const newStatus = checked ? '0' : '1'
  try {
    await changeJobStatus({ jobId: record.jobId, status: newStatus })
    message.success(t('common.operationSuccess'))
    fetchJobList()
  } catch {
    message.error(t('common.operationFailed'))
  }
}

// 立即执行
const handleExecute = async (record: JobListVO) => {
  Modal.confirm({
    title: t('system.job.executeConfirm'),
    content: t('system.job.executeConfirmMessage', { name: record.jobName }),
    onOk: async () => {
      try {
        await executeJobOnce({ jobId: record.jobId })
        message.success(t('system.job.executeSuccess'))
      } catch {
        message.error(t('system.job.executeFailed'))
      }
    },
  })
}

// 查看日志
const handleViewLogs = (record: JobListVO) => {
  currentJobId.value = record.jobId
  currentJobName.value = record.jobName
  logVisible.value = true
}

// 表单成功回调
const handleFormSuccess = () => {
  fetchJobList()
}

// 复制 Webhook URL
const handleCopyWebhookUrl = async (record: JobListVO) => {
  // 获取当前基础 URL
  const baseUrl = window.location.origin
  const webhookUrl = `${baseUrl}/webhook/job/${record.jobId}`

  try {
    await navigator.clipboard.writeText(webhookUrl)
    message.success(t('system.job.webhookUrlCopied'))
  } catch {
    // 如果 clipboard API 不可用，使用传统方法
    const textarea = document.createElement('textarea')
    textarea.value = webhookUrl
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      message.success(t('system.job.webhookUrlCopied'))
    } catch {
      message.error(t('system.job.webhookUrlCopyFailed'))
    } finally {
      document.body.removeChild(textarea)
    }
  }
}

// 初始化
onMounted(() => {
  fetchJobList()
})
</script>

<style scoped>
.cron-text {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>
