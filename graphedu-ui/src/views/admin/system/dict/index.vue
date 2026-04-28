<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.dict.dictType')">
            <a-input
              v-model:value="queryParams.dictName"
              :placeholder="t('system.dict.dictTypePlaceholder')"
              allow-clear
              style="width: 150px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.dict.dictTypeValue')">
            <a-input
              v-model:value="queryParams.dictType"
              :placeholder="t('system.dict.dictTypeValuePlaceholder')"
              allow-clear
              style="width: 150px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('system.dict.statusPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('common.createTime')">
            <a-range-picker
              v-model:value="dateRange as any"
              :placeholder="[t('common.startDate'), t('common.endDate')]"
              style="width: 220px"
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
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          {{ t('common.add') }}
        </a-button>
        <a-button type="default" :disabled="single" @click="() => handleUpdate()">
          <template #icon><EditOutlined /></template>
          {{ t('common.edit') }}
        </a-button>
        <a-button type="default" danger :disabled="multiple" @click="() => handleDelete()">
          <template #icon><DeleteOutlined /></template>
          {{ t('common.delete') }}
        </a-button>
        <a-button type="default" @click="handleExport">
          <template #icon><DownloadOutlined /></template>
          {{ t('common.export') }}
        </a-button>
        <a-button type="default" @click="handleRefreshCache">
          <template #icon><ReloadOutlined /></template>
          {{ t('system.dict.refreshCache') }}
        </a-button>
      </a-space>
    </template>

    <!-- 字典类型表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="typeList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        :scroll="{ x: 'max-content', y: scrollY }"
        row-key="dictId"
      >
        <template #bodyCell="{ column, record }">
          <!-- 字典类型列 - 点击打开抽屉 -->
          <template v-if="column.key === 'dictType'">
            <a style="cursor: pointer" @click="openDictDataDrawer(record as DictTypeListVO)">
              {{ record.dictType }}
            </a>
          </template>
          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <DictTag :options="sys_data_status" :value="record.status" />
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" @click="handleUpdate(record as DictTypeListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.delete')">
                <a-button type="link" size="small" danger @click="handleDelete(record as DictTypeListVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
          <!-- 时间列 -->
          <template v-else-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
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

  <!-- 字典类型表单弹窗 -->
  <DictTypeForm v-model:visible="formVisible" :dict-id="currentDictId" @success="handleFormSuccess" />
  <!-- 字典数据抽屉 -->
  <DictDataDrawer v-model:visible="drawerVisible" :dict-id="currentDict?.dictId || 0" :dict-type="currentDictType" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getDictTypeList, deleteDictType, refreshDictCache } from '@/api/system/dict.ts'
import type { DictTypeQueryDTO, DictTypeListVO } from '@/types/api/system/dict.ts'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import useDictStore from '@/stores/modules/dict.ts'
import DictTag from '../../../../components/dict/DictTag.vue'
import DictTypeForm from './components/DictTypeForm.vue'
import DictDataDrawer from './components/DictDataDrawer.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

// 获取字典数据
const { sys_data_status } = useDict('sys_data_status')

// URL 状态管理工具函数
// 更新 URL 中的 openDictId 参数
const updateOpenDictIdToUrl = (dictId: number) => {
  const currentQuery = { ...route.query }
  currentQuery.openDictId = String(dictId)
  router.replace({ query: currentQuery }).catch(() => {})
}

// 从 URL 中移除 openDictId 参数
const removeOpenDictIdFromUrl = () => {
  const currentQuery = { ...route.query }
  delete currentQuery.openDictId
  router.replace({ query: currentQuery }).catch(() => {})
}

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('system.dict.dictId'), dataIndex: 'dictId', key: 'dictId', width: 90 },
  { title: t('system.dict.dictType'), dataIndex: 'dictName', key: 'dictName', width: 150 },
  { title: t('system.dict.dictTypeValue'), dataIndex: 'dictType', key: 'dictType', width: 150 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('common.remark'), dataIndex: 'remark', key: 'remark', ellipsis: true },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 120 },
]

// 数据状态
const loading = ref(false)
const typeList = ref<DictTypeListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: DictTypeQueryDTO = {
  page: 1,
  size: 10,
  dictName: undefined,
  dictType: undefined,
  status: undefined,
  beginTime: undefined,
  endTime: undefined,
}

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 临时存储查询参数（在 getList 中使用）
let queryParams: DictTypeQueryDTO = { ...defaultQueryParams }

// 获取字典类型列表
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
    const res = await getDictTypeList(queryParams)
    if (res.code === 200) {
      typeList.value = res.data.rows || []
      total.value = res.data.total || 0

      // 数据加载完成后，检查是否需要打开抽屉
      checkAndOpenDrawerFromUrl()
    }
  } catch (_e) {
    message.error(t('system.dict.getDictTypeListFailed'))
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
} = usePaginationQuery<DictTypeQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['dictName', 'dictType', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 检查 URL 并打开抽屉
const checkAndOpenDrawerFromUrl = () => {
  const openDictId = route.query.openDictId
  if (!openDictId) return

  const targetDict = typeList.value.find((item) => item.dictId === Number(openDictId))
  if (targetDict) {
    // 找到了，打开抽屉
    currentDict.value = targetDict
    currentDictType.value = targetDict.dictType
    drawerVisible.value = true
  } else {
    // 没找到，清除参数
    removeOpenDictIdFromUrl()
  }
}

// 选中的行
const selectedRowKeys = ref<(string | number)[]>([])
const selectedRows = ref<DictTypeListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: any[], rows: any[]) => {
    selectedRowKeys.value = keys
    selectedRows.value = rows as DictTypeListVO[]
  },
}))

// 弹窗状态
const formVisible = ref(false)
const currentDictId = ref<number>()

// 抽屉状态
const drawerVisible = ref(false)
const currentDict = ref<DictTypeListVO>()
const currentDictType = ref('')

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

// 新增
const handleAdd = () => {
  currentDictId.value = undefined
  formVisible.value = true
}

// 修改
const handleUpdate = (record?: DictTypeListVO) => {
  if (record) {
    currentDictId.value = record.dictId
  } else if (selectedRows.value.length === 1) {
    const dictId = selectedRows.value[0]?.dictId
    if (dictId !== undefined) {
      currentDictId.value = dictId
    }
  }
  formVisible.value = true
}

// 删除
const handleDelete = (record?: DictTypeListVO) => {
  let dictIds: string
  if (record) {
    dictIds = String(record.dictId)
  } else {
    dictIds = selectedRowKeys.value.join(',')
  }

  Modal.confirm({
    title: t('common.systemTip'),
    content: record ? t('system.dict.deleteDictTypeConfirm', { dictName: record.dictName }) : t('common.deleteConfirm'),
    onOk: async () => {
      try {
        const res = await deleteDictType(dictIds)
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

// 导出
const handleExport = () => {
  message.info(t('common.exportFeatureInDevelopment'))
}

// 刷新缓存
const handleRefreshCache = async () => {
  try {
    const res = await refreshDictCache()
    if (res.code === 200) {
      message.success(t('system.dict.refreshCacheSuccess'))
      // 清空本地字典缓存
      useDictStore().cleanDict()
    }
  } catch (_e) {
    message.error(t('system.dict.refreshCacheFailed'))
  }
}

// 分页组件的 show-total 回调
const showTotal = (total: number) => `${t('common.total')} ${total} ${t('common.items')}`

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 表单提交成功
const handleFormSuccess = () => {
  formVisible.value = false
  getList()
}

// 打开字典数据抽屉
const openDictDataDrawer = (record: DictTypeListVO) => {
  currentDict.value = record
  currentDictType.value = record.dictType
  drawerVisible.value = true

  // 同步到 URL
  updateOpenDictIdToUrl(record.dictId)
}

// 监听抽屉关闭，清除 URL 参数
watch(drawerVisible, (newVal) => {
  if (!newVal) {
    removeOpenDictIdFromUrl()
  }
})

onMounted(() => {
  getList()
})
</script>
