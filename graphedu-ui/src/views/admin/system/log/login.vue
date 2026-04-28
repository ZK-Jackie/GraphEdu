<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.log.login.ipaddr')">
            <a-input
              v-model:value="queryParams.ipaddr"
              :placeholder="t('system.log.login.ipaddrPlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.userName')">
            <a-input
              v-model:value="queryParams.userName"
              :placeholder="t('common.userNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('system.log.login.statusPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('system.log.login.loginTime')">
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
        <a-button type="primary" :disabled="single" @click="handleUnlock">
          <template #icon><UnlockOutlined /></template>
          {{ t('system.log.login.unlock') }}
        </a-button>
        <a-button type="default" @click="handleExport">
          <template #icon><DownloadOutlined /></template>
          {{ t('common.export') }}
        </a-button>
      </a-space>
    </template>

    <!-- 登录日志表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="loginLogList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="infoId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 用户名称列 -->
          <template v-if="column.key === 'userName'">
            <a-tooltip :title="record.userName">
              {{ record.userName }}
            </a-tooltip>
          </template>
          <!-- 地址列 -->
          <template v-else-if="column.key === 'ipaddr'">
            <a-tooltip :title="record.ipaddr">
              {{ record.ipaddr }}
            </a-tooltip>
          </template>
          <!-- 登录地点列 -->
          <template v-else-if="column.key === 'loginLocation'">
            <a-tooltip :title="record.loginLocation">
              {{ record.loginLocation }}
            </a-tooltip>
          </template>
          <!-- 操作系统列 -->
          <template v-else-if="column.key === 'os'">
            <a-tooltip :title="record.os">
              {{ record.os }}
            </a-tooltip>
          </template>
          <!-- 浏览器列 -->
          <template v-else-if="column.key === 'browser'">
            <a-tooltip :title="record.browser">
              {{ record.browser }}
            </a-tooltip>
          </template>
          <!-- 登录状态列 -->
          <template v-else-if="column.key === 'status'">
            <DictTag :options="sys_data_status" :value="record.status" />
          </template>
          <!-- 描述列 -->
          <template v-else-if="column.key === 'msg'">
            <a-tooltip :title="record.msg">
              {{ record.msg }}
            </a-tooltip>
          </template>
          <!-- 访问时间列 -->
          <template v-else-if="column.key === 'loginTime'">
            {{ formatTime(record.loginTime) }}
          </template>
        </template>
      </a-table>
    </template>

    <template #pagination>
      <!-- 分页 -->
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
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { SearchOutlined, ReloadOutlined, DeleteOutlined, DownloadOutlined, UnlockOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getLoginLogList, deleteLoginLog, clearLoginLog, unlockUser } from '@/api/system/log.ts'
import type { LoginLogQueryDTO, LoginLogListVO } from '@/types/api/system/log.ts'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import DictTag from '../../../../components/dict/DictTag.vue'
import DictSelect from '../../../../components/dict/DictSelect.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

const { t } = useI18n()

// 获取字典数据
const { sys_data_status } = useDict('sys_data_status')

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('system.log.login.infoId'), dataIndex: 'infoId', key: 'infoId', width: 100 },
  { title: t('common.userName'), dataIndex: 'userName', key: 'userName', width: 120, ellipsis: true },
  { title: t('system.log.login.ipaddr'), dataIndex: 'ipaddr', key: 'ipaddr', width: 140, ellipsis: true },
  {
    title: t('system.log.login.loginLocation'),
    dataIndex: 'loginLocation',
    key: 'loginLocation',
    width: 140,
    ellipsis: true,
  },
  { title: t('system.log.login.os'), dataIndex: 'os', key: 'os', width: 120, ellipsis: true },
  { title: t('system.log.login.browser'), dataIndex: 'browser', key: 'browser', width: 120, ellipsis: true },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('system.log.login.msg'), dataIndex: 'msg', key: 'msg', ellipsis: true },
  { title: t('system.log.login.loginTime'), dataIndex: 'loginTime', key: 'loginTime', width: 180 },
]

// 数据状态
const loading = ref(false)
const loginLogList = ref<LoginLogListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: LoginLogQueryDTO = {
  page: 1,
  size: 10,
  ipaddr: undefined,
  userName: undefined,
  status: undefined,
  beginTime: undefined,
  endTime: undefined,
}

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 临时存储查询参数（在 getList 中使用）
let queryParams: LoginLogQueryDTO = { ...defaultQueryParams }

// 获取登录日志列表
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
    const res = await getLoginLogList(queryParams)
    if (res.code === 200) {
      loginLogList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (_e) {
    message.error(t('system.log.login.getLoginLogListFailed'))
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
} = usePaginationQuery<LoginLogQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['ipaddr', 'userName', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<LoginLogListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys, rows) => {
    selectedRowKeys.value = keys as number[]
    selectedRows.value = rows as LoginLogListVO[]
  },
}))

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

// 删除
const handleDelete = () => {
  const infoIds = selectedRowKeys.value.join(',')

  Modal.confirm({
    title: t('common.systemTip'),
    content: t('system.log.login.deleteConfirm', { infoIds }),
    onOk: async () => {
      try {
        const res = await deleteLoginLog(infoIds)
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
    content: t('system.log.login.cleanConfirm'),
    onOk: async () => {
      try {
        const res = await clearLoginLog()
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

// 解锁
const handleUnlock = () => {
  const username = selectedRows.value[0]?.userName
  if (!username) {
    message.warning(t('system.log.login.selectUserToUnlock'))
    return
  }

  Modal.confirm({
    title: t('common.systemTip'),
    content: t('system.log.login.unlockConfirm', { username }),
    onOk: async () => {
      try {
        const res = await unlockUser(username)
        if (res.code === 200) {
          message.success(t('system.log.login.unlockSuccess', { username }))
        }
      } catch (_e) {
        message.error(t('system.log.login.unlockFailed'))
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
