<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.log.operation.operIp')">
            <a-input
              v-model:value="queryParams.operIp"
              :placeholder="t('system.log.operation.operIpPlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.log.operation.moduleName')">
            <a-input
              v-model:value="queryParams.title"
              :placeholder="t('system.log.operation.moduleNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.log.operation.userName')">
            <a-input
              v-model:value="queryParams.operName"
              :placeholder="t('system.log.operation.userNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.log.operation.businessType')">
            <DictSelect
              v-model:model-value="queryParams.businessType"
              dict-type="sys_oper_log_oper_type"
              :placeholder="t('system.log.operation.operateTypePlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('system.log.operation.statusPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('system.log.operation.operateTime')">
            <a-range-picker
              v-model:value="dateRange as any"
              :placeholder="[t('common.startDate'), t('common.endDate')]"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 380px"
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

    <!-- 操作按钮和表格 -->
    <!-- 操作按钮 -->
    <template #actions>
      <a-space>
        <a-button type="default" danger :disabled="multiple" @click="handleDelete">
          <template #icon><DeleteOutlined /></template>
          {{ t('common.delete') }}
        </a-button>
        <a-button type="default" danger @click="handleClean">
          <template #icon><DeleteOutlined /></template>
          {{ t('common.clean') }}
        </a-button>
        <a-button type="default" @click="handleExport">
          <template #icon><DownloadOutlined /></template>
          {{ t('common.export') }}
        </a-button>
      </a-space>
    </template>

    <!-- 操作日志表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="operLogList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="operId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 操作类型列 -->
          <template v-if="column.key === 'businessType'">
            <DictTag :options="sys_oper_log_oper_type" :value="record.businessType" />
          </template>
          <!-- 操作人员列 -->
          <template v-else-if="column.key === 'operName'">
            <a-tooltip :title="record.operName">
              {{ record.operName }}
            </a-tooltip>
          </template>
          <!-- 操作地址列 -->
          <template v-else-if="column.key === 'operIp'">
            <a-tooltip :title="record.operIp">
              {{ record.operIp }}
            </a-tooltip>
          </template>
          <!-- 系统模块列 -->
          <template v-else-if="column.key === 'title'">
            <a-tooltip :title="record.title">
              {{ record.title }}
            </a-tooltip>
          </template>
          <!-- 操作状态列 -->
          <template v-else-if="column.key === 'status'">
            <DictTag :options="sys_data_status" :value="record.status" />
          </template>
          <!-- 操作日期列 -->
          <template v-else-if="column.key === 'operTime'">
            {{ formatTime(record.operTime) }}
          </template>
          <!-- 消耗时间列 -->
          <template v-else-if="column.key === 'costTime'">
            <a-tooltip :title="`${record.costTime}${t('system.log.operation.costTimeUnit')}`">
              {{ record.costTime }}{{ t('system.log.operation.costTimeUnit') }}
            </a-tooltip>
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleView(record as OperLogListVO)">
                <template #icon><EyeOutlined /></template>
                {{ t('common.detail') }}
              </a-button>
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
        :show-total="showTotal"
        @change="handlePageChange"
      />
    </template>
  </TablePageLayout>

  <!-- 操作日志详情弹窗组件 -->
  <OperLogDetailModal v-model:visible="detailVisible" :oper-id="currentOperId" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { SearchOutlined, ReloadOutlined, DeleteOutlined, DownloadOutlined, EyeOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getOperationLogList, deleteOperationLog, clearOperationLog } from '@/api/system/log.ts'
import type { OperLogQueryDTO, OperLogListVO } from '@/types/api/system/log.ts'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import DictTag from '../../../../components/dict/DictTag.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import OperLogDetailModal from './components/OperLogDetailModal.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

const { t } = useI18n()

// 获取字典数据
const { sys_oper_log_oper_type, sys_data_status } = useDict('sys_oper_log_oper_type', 'sys_data_status')

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('system.log.operation.operId'), dataIndex: 'operId', key: 'operId', width: 100 },
  { title: t('system.log.operation.moduleName'), dataIndex: 'title', key: 'title', width: 150, ellipsis: true },
  { title: t('system.log.operation.operateType'), dataIndex: 'businessType', key: 'businessType', width: 120 },
  { title: t('system.log.operation.userName'), dataIndex: 'operName', key: 'operName', width: 120, ellipsis: true },
  { title: t('system.log.operation.operIp'), dataIndex: 'operIp', key: 'operIp', width: 140, ellipsis: true },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('system.log.operation.operateTime'), dataIndex: 'operTime', key: 'operTime', width: 180 },
  { title: t('system.log.operation.costTime'), dataIndex: 'costTime', key: 'costTime', width: 120, ellipsis: true },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 100 },
]

// 数据状态
const loading = ref(false)
const operLogList = ref<OperLogListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: OperLogQueryDTO = {
  page: 1,
  size: 10,
  operIp: undefined,
  title: undefined,
  operName: undefined,
  businessType: undefined,
  status: undefined,
  beginTime: undefined,
  endTime: undefined,
}

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 临时存储查询参数（在 getList 中使用）
let queryParams: OperLogQueryDTO = { ...defaultQueryParams }

// 获取操作日志列表
const getList = async () => {
  loading.value = true
  // 处理日期范围
  if (dateRange.value?.length === 2) {
    queryParams.beginTime = dateRange.value[0]
    queryParams.endTime = dateRange.value[1]
  } else {
    queryParams.beginTime = undefined
    queryParams.endTime = undefined
  }

  try {
    const res = await getOperationLogList(queryParams)
    if (res.code === 200) {
      operLogList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (_e) {
    message.error(t('system.log.operation.getOperationLogListFailed'))
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
} = usePaginationQuery<OperLogQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['operIp', 'title', 'operName', 'businessType', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<OperLogListVO[]>([])
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys, rows) => {
    selectedRowKeys.value = keys as number[]
    selectedRows.value = rows as OperLogListVO[]
  },
}))

// 详情弹窗
const detailVisible = ref(false)
const currentOperId = ref<number>()

// 搜索
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  dateRange.value = null
  resetAll()
  fetch()
}

// 分页变化
const handlePageChange = () => {
  getList()
}

// 查看详情
const handleView = (record: OperLogListVO) => {
  currentOperId.value = record.operId
  detailVisible.value = true
}

// 删除
const handleDelete = () => {
  const operIds = selectedRowKeys.value.join(',')

  Modal.confirm({
    title: t('common.systemTip'),
    content: t('system.log.operation.deleteConfirm', { operIds }),
    onOk: async () => {
      try {
        const res = await deleteOperationLog(operIds)
        if (res.code === 200) {
          message.success(t('common.deleteSuccess'))
          await getList()
        }
      } catch (_e) {
        message.error(t('common.deleteFailed'))
      }
    },
  })
}

// 清空
const handleClean = () => {
  Modal.confirm({
    title: t('common.systemTip'),
    content: t('system.log.operation.cleanConfirm'),
    onOk: async () => {
      try {
        const res = await clearOperationLog()
        if (res.code === 200) {
          message.success(t('common.cleanSuccess'))
          await getList()
        }
      } catch (_e) {
        message.error(t('common.cleanFailed'))
      }
    },
  })
}

// 导出
const handleExport = () => {
  message.info(t('common.exportFeatureInDevelopment'))
}

// 分页组件的 show-total 回调
const showTotal = (total: number) => `${t('common.total')} ${total} ${t('common.items')}`

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 初始化
onMounted(() => {
  getList()
})
</script>
