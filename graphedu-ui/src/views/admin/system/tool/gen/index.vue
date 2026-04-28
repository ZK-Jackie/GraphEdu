<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline">
          <a-form-item label="表名称">
            <a-input
              v-model:value="queryParams.tableName"
              placeholder="请输入表名称"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="表描述">
            <a-input
              v-model:value="queryParams.tableComment"
              placeholder="请输入表描述"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="创建时间">
            <a-range-picker v-model:value="dateRange as any" value-format="YYYY-MM-DD" style="width: 280px" />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" @click="handleQuery">
                <template #icon><SearchOutlined /></template>
                搜索
              </a-button>
              <a-button @click="resetQuery">
                <template #icon><ReloadOutlined /></template>
                重置
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>
    </template>

    <!-- 操作按钮 -->
    <template #actions>
      <a-space>
        <a-button type="primary" :disabled="multipleSelection" @click="handleGenTable">
          <template #icon><DownloadOutlined /></template>
          生成
        </a-button>
        <a-button type="primary" @click="openCreateTable">
          <template #icon><PlusOutlined /></template>
          创建
        </a-button>
        <a-button @click="openImportTable">
          <template #icon><UploadOutlined /></template>
          导入
        </a-button>
        <a-button type="primary" danger :disabled="singleSelection" @click="handleEditTable">
          <template #icon><EditOutlined /></template>
          修改
        </a-button>
        <a-button danger :disabled="multipleSelection" @click="handleDelete">
          <template #icon><DeleteOutlined /></template>
          删除
        </a-button>
      </a-space>
    </template>

    <!-- 表格 -->
    <template #table="{ scrollY }">
      <a-table
        :row-selection="rowSelection as any"
        :data-source="tableList"
        :loading="loading"
        :pagination="false"
        :columns="columns"
        row-key="tableId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'index'">
            {{ (queryParams.page! - 1) * queryParams.size! + index + 1 }}
          </template>
          <template v-else-if="column.key === 'createTime' || column.key === 'updateTime'">
            {{ parseTime(record[column.dataIndex as keyof typeof record]) }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="预览">
                <a-button type="link" size="small" @click="handlePreview(record)">
                  <template #icon><EyeOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="编辑">
                <a-button type="link" size="small" @click="handleEditTable(record)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button type="link" size="small" danger @click="handleDelete(record)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="同步">
                <a-button type="link" size="small" @click="handleSynchDb(record)">
                  <template #icon><ReloadOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="生成代码">
                <a-button type="link" size="small" @click="handleGenTable(record)">
                  <template #icon><DownloadOutlined /></template>
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
        v-show="total > 0"
        v-model:current="queryParams.page"
        v-model:page-size="queryParams.size"
        :total="total"
        :show-total="(total) => `共 ${total} 条`"
        show-size-changer
        @change="getList"
      />
    </template>
  </TablePageLayout>

  <!-- 预览弹窗 -->
  <PreviewModal ref="previewRef" />

  <!-- 导入表弹窗 -->
  <ImportTable ref="importRef" @ok="handleQuery" />

  <!-- 创建表弹窗 -->
  <CreateTable ref="createRef" @ok="handleQuery" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import type { TableProps } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  PlusOutlined,
  UploadOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'
import {
  getGenTableList,
  previewGenCode,
  deleteGenTable,
  genCodeToPath,
  synchDb,
  batchGenCode,
} from '@/api/system/tool/gen'
import type { GenTableQueryDTO, GenTableVO } from '@/types/api/tool/gen.ts'
import { parseTime } from '@/utils/common.ts'
import ImportTable from './components/ImportTable.vue'
import CreateTable from './components/CreateTable.vue'
import PreviewModal from './components/PreviewModal.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

const router = useRouter()

const loading = ref(false)
const tableList = ref<GenTableVO[]>([])
const total = ref(0)
const dateRange = ref<string[]>([])
const selectedRowKeys = ref<number[]>([])
const selectedTableNames = ref<string[]>([])

// 组件引用
const previewRef = ref<InstanceType<typeof PreviewModal>>()
const importRef = ref<InstanceType<typeof ImportTable>>()
const createRef = ref<InstanceType<typeof CreateTable>>()

// 查询参数的默认值
const defaultQueryParams: GenTableQueryDTO = {
  page: 1,
  size: 10,
  tableName: undefined,
  tableComment: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: GenTableQueryDTO = { ...defaultQueryParams }

const columns = [
  { title: '序号', key: 'index', width: 60, fixed: 'left' as const },
  { title: '表名称', dataIndex: 'tableName', key: 'tableName', ellipsis: true },
  { title: '表描述', dataIndex: 'tableComment', key: 'tableComment', ellipsis: true },
  { title: '实体', dataIndex: 'className', key: 'className', ellipsis: true },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 170 },
  { title: '更新时间', dataIndex: 'updateTime', key: 'updateTime', width: 170 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' as const },
]

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[], rows: GenTableVO[]) => {
    selectedRowKeys.value = keys
    selectedTableNames.value = rows.map((row) => row.tableName || '')
  },
}))

const singleSelection = computed(() => selectedRowKeys.value.length !== 1)
const multipleSelection = computed(() => selectedRowKeys.value.length === 0)

/** 查询表集合 */
function getList() {
  loading.value = true
  const params = { ...queryParams }
  if (dateRange.value && dateRange.value.length === 2) {
    ;(params as any).beginTime = dateRange.value[0]
    ;(params as any).endTime = dateRange.value[1]
  }
  getGenTableList(params)
    .then((res) => {
      tableList.value = res.data.rows || []
      total.value = res.data.total || 0
    })
    .finally(() => {
      loading.value = false
    })
}

// 使用 usePaginationQuery Hook 管理查询参数
const {
  queryParams: syncedQueryParams,
  resetPage,
  resetAll,
  fetch,
} = usePaginationQuery<GenTableQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['tableName', 'tableComment'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.page = 1
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  dateRange.value = []
  resetAll()
  fetch()
}

/** 生成代码操作 */
function handleGenTable(row?: any) {
  const tableName = row ? row.tableName : selectedTableNames.value.join(',')
  if (!tableName) {
    message.warning('请选择要生成的数据')
    return
  }

  const table = row || tableList.value.find((t) => t.tableName === tableName?.split(',')[0])
  if (table?.genType === '1') {
    // 自定义路径生成
    genCodeToPath(tableName).then((res) => {
      message.success('成功生成到自定义路径：' + (res.data || ''))
    })
  } else {
    // 下载 ZIP 压缩包
    batchGenCode(tableName).then((blob) => {
      const url = window.URL.createObjectURL(new Blob([blob]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'graphedu.zip')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success('代码生成成功')
    })
  }
}

/** 同步数据库操作 */
function handleSynchDb(row: GenTableVO) {
  const tableName = row.tableName
  Modal.confirm({
    title: '系统提示',
    content: `确认要强制同步"${tableName}"表结构吗？`,
    onOk: () => {
      return synchDb(tableName!).then(() => {
        message.success('同步成功')
        getList()
      })
    },
  })
}

/** 打开导入表弹窗 */
function openImportTable() {
  importRef.value?.show()
}

/** 打开创建表弹窗 */
function openCreateTable() {
  createRef.value?.show()
}

/** 预览按钮 */
function handlePreview(row: GenTableVO) {
  previewGenCode(row.tableId!).then((res) => {
    previewRef.value?.show(res.data)
  })
}

/** 修改按钮操作 */
function handleEditTable(row?: any) {
  const tableId = row ? row.tableId : selectedRowKeys.value[0]
  const tableName = row ? row.tableName : selectedTableNames.value[0]
  router.push({
    path: `/tool/gen/edit/${tableId}`,
    query: { tableName, pageNum: String(queryParams.page) },
  })
}

/** 删除按钮操作 */
function handleDelete(row?: any) {
  const tableIds = row ? [row.tableId!] : selectedRowKeys.value
  const tableNames = row ? row.tableName : selectedTableNames.value.join(',')

  Modal.confirm({
    title: '系统提示',
    content: `是否确认删除表编号为"${tableIds.join(',')}"的数据项？`,
    onOk: () => {
      return deleteGenTable(tableIds.join(',')).then(() => {
        message.success('删除成功')
        getList()
      })
    },
  })
}

onMounted(() => {
  getList()
})
</script>
