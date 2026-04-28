<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item label="图谱名称">
            <a-input
              v-model:value="queryParams.graphName"
              placeholder="请输入图谱名称"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="书籍ID">
            <a-input-number
              v-model:value="queryParams.bookId"
              placeholder="请输入书籍ID"
              allow-clear
              style="width: 150px"
              :min="1"
            />
          </a-form-item>
          <a-form-item label="构建方法">
            <a-select
              v-model:value="queryParams.buildMethod"
              placeholder="请选择构建方法"
              allow-clear
              style="width: 150px"
            >
              <a-select-option value="nlp">NLP</a-select-option>
              <a-select-option value="llm">LLM</a-select-option>
              <a-select-option value="llm_assisted">LLM辅助</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="状态">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              placeholder="请选择状态"
              allow-clear
              style="width: 120px"
            />
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
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增
        </a-button>
        <a-button type="default" :disabled="single" @click="() => handleUpdate()">
          <template #icon><EditOutlined /></template>
          修改
        </a-button>
        <a-button type="default" danger :disabled="multiple" @click="() => handleDelete()">
          <template #icon><DeleteOutlined /></template>
          删除
        </a-button>
      </a-space>
    </template>

    <!-- 知识图谱表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="graphList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="graphId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 状态列 -->
          <template v-if="column.key === 'status'">
            <a-switch
              :checked="record.status === '0'"
              checked-children="正常"
              un-checked-children="停用"
              @change="(checked: any) => handleStatusChange(record as KnowledgeGraphListVO, checked)"
            />
          </template>
          <!-- 构建方法列 -->
          <template v-else-if="column.key === 'buildMethod'">
            <a-tag v-if="record.buildMethod === 'nlp'" color="blue">NLP</a-tag>
            <a-tag v-else-if="record.buildMethod === 'llm'" color="green">LLM</a-tag>
            <a-tag v-else-if="record.buildMethod === 'llm_assisted'" color="orange">LLM辅助</a-tag>
            <a-tag v-else color="default">{{ record.buildMethod }}</a-tag>
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="修改">
                <a-button type="link" size="small" @click="handleUpdate(record as KnowledgeGraphListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button type="link" size="small" danger @click="handleDelete(record as KnowledgeGraphListVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
          <!-- 时间列 -->
          <template v-else-if="column.key === 'createTime' || column.key === 'lastExtended'">
            {{ formatTime(record[column.key]) }}
          </template>
          <!-- 节点/关系统计 -->
          <template v-else-if="column.key === 'stats'">
            <span>{{ record.totalNodes || 0 }} 节点 / {{ record.totalRelationships || 0 }} 关系</span>
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

  <!-- 知识图谱表单弹窗 -->
  <KnowledgeGraphForm v-model:visible="formVisible" :graph-id="currentGraphId" @success="handleFormSuccess" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { SearchOutlined, ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import {
  getKnowledgeGraphList,
  deleteKnowledgeGraph,
  changeKnowledgeGraphStatus,
} from '@/api/education/knowledge-graph.ts'
import type { KnowledgeGraphQueryDTO, KnowledgeGraphListVO } from '@/types/api/knowledge-graph'
import KnowledgeGraphForm from './components/KnowledgeGraphForm.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import DictSelect from '@/components/dict/DictSelect.vue'
import { parseTime } from '@/utils/common.ts'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

// 表格列定义
const columns: TableProps['columns'] = [
  { title: '图谱ID', dataIndex: 'graphId', key: 'graphId', width: 100 },
  { title: '图谱名称', dataIndex: 'graphName', key: 'graphName', width: 200 },
  { title: '书籍ID', dataIndex: 'bookId', key: 'bookId', width: 100 },
  { title: '书籍名称', dataIndex: 'bookTitle', key: 'bookTitle', width: 200 },
  { title: '数据库名称', dataIndex: 'graphDatabase', key: 'graphDatabase', width: 150 },
  { title: '版本', dataIndex: 'version', key: 'version', width: 100 },
  { title: '节点/关系', key: 'stats', width: 150 },
  { title: '构建方法', dataIndex: 'buildMethod', key: 'buildMethod', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '最后扩展', dataIndex: 'lastExtended', key: 'lastExtended', width: 180 },
  { title: '操作', key: 'action', fixed: 'right' as const, width: 150 },
]

// 数据状态
const loading = ref(false)
const graphList = ref<KnowledgeGraphListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: KnowledgeGraphQueryDTO = {
  page: 1,
  size: 10,
  graphName: undefined,
  bookId: undefined,
  buildMethod: undefined,
  status: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: KnowledgeGraphQueryDTO = { ...defaultQueryParams }

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<KnowledgeGraphListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[], rows: any[]) => {
    selectedRowKeys.value = keys as number[]
    selectedRows.value = rows as KnowledgeGraphListVO[]
  },
}))

// 弹窗状态
const formVisible = ref(false)

// 当前操作的知识图谱
const currentGraphId = ref<number>()

// 获取知识图谱列表
const getList = async () => {
  loading.value = true
  try {
    const res = await getKnowledgeGraphList(queryParams)
    if (res.code === 200) {
      graphList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (_e) {
    message.error('获取知识图谱列表失败')
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
} = usePaginationQuery<KnowledgeGraphQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['graphName', 'bookId', 'buildMethod', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 搜索知识图谱
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  resetAll()
  fetch()
}

// 分页变化
const handlePageChange = () => {
  getList()
}

// 新增知识图谱
const handleAdd = () => {
  currentGraphId.value = undefined
  formVisible.value = true
}

// 修改知识图谱
const handleUpdate = (record?: KnowledgeGraphListVO) => {
  if (record) {
    currentGraphId.value = record.graphId
  } else if (selectedRows.value.length === 1) {
    currentGraphId.value = selectedRows.value[0]?.graphId
  }
  formVisible.value = true
}

// 删除知识图谱
const handleDelete = (record?: KnowledgeGraphListVO) => {
  let graphIds: string
  if (record) {
    graphIds = String(record.graphId)
  } else {
    graphIds = selectedRowKeys.value.join(',')
  }

  Modal.confirm({
    title: '系统提示',
    content: record ? `确定要删除知识图谱"${record.graphName}"吗？` : '确定要删除选中的知识图谱吗？',
    onOk: async () => {
      try {
        const res = await deleteKnowledgeGraph(graphIds)
        if (res.code === 200) {
          message.success('删除成功')
          getList()
        }
      } catch (_e) {
        message.error('删除失败')
      }
    },
  })
}

// 状态变更
const handleStatusChange = async (record: KnowledgeGraphListVO, checked: boolean) => {
  const data = {
    graphId: record.graphId,
    status: checked ? '0' : '1',
  }
  try {
    const res = await changeKnowledgeGraphStatus(data)
    if (res.code === 200) {
      message.success('状态修改成功')
      getList()
    }
  } catch (_e) {
    message.error('状态修改失败')
  }
}

// 分页组件的 show-total 回调
const showTotal = (total: number) => `共 ${total} 条`

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return '-'
  return parseTime(time)
}

// 表单提交成功
const handleFormSuccess = () => {
  getList()
}

// 初始化
onMounted(() => {
  getList()
})
</script>
