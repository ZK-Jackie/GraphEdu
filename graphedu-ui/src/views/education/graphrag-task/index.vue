<template>
  <TablePageLayout scroll-behavior="auto">
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false" class="search-card">
        <a-form layout="inline" :model="queryParams">
          <a-form-item label="任务状态">
            <a-select
              v-model:value="queryParams.taskStatus"
              placeholder="请选择任务状态"
              allow-clear
              style="width: 150px"
              @change="handleQuery"
            >
              <a-select-option value="pending">待处理</a-select-option>
              <a-select-option value="processing">处理中</a-select-option>
              <a-select-option value="success">成功</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="任务类型">
            <a-input
              v-model:value="queryParams.taskType"
              placeholder="请输入任务类型"
              allow-clear
              style="width: 150px"
              @press-enter="handleQuery"
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

    <!-- 操作按钮和表格 -->
    <template #actions>
      <div class="actions-container">
        <a-space>
          <a-button type="primary" @click="handleAdd">
            <template #icon><PlusOutlined /></template>
            新增
          </a-button>
          <a-button type="default" danger @click="handleBatchDelete">
            <template #icon><DeleteOutlined /></template>
            批量删除
          </a-button>
        </a-space>

        <!-- 右侧筛选：课程 -->
        <div class="actions-filter">
          <a-select
            v-model:value="selectedCourseId"
            placeholder="请选择课程"
            :loading="courseLoading"
            allow-clear
            style="width: 200px"
            @change="handleCourseChange"
          >
            <a-select-option v-for="course in courseList" :key="course.courseId" :value="course.courseId">
              {{ course.courseName }}
            </a-select-option>
          </a-select>
        </div>
      </div>
    </template>

    <template #table="{ scrollY }">
      <!-- GraphRAG 任务表格 -->
      <a-table
        :columns="columns"
        :data-source="taskList"
        :loading="loading"
        :pagination="pagination"
        :row-selection="rowSelection as any"
        row-key="taskId"
        :scroll="{ x: 'max-content', y: scrollY }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <!-- 任务状态 -->
          <template v-if="column.key === 'taskStatus'">
            <a-tag v-if="record.taskStatus === 'pending'" color="default">待处理</a-tag>
            <a-tag v-else-if="record.taskStatus === 'processing'" color="processing">处理中</a-tag>
            <a-tag v-else-if="record.taskStatus === 'success'" color="success">成功</a-tag>
            <a-tag v-else-if="record.taskStatus === 'failed'" color="error">失败</a-tag>
          </template>

          <!-- 任务类型 -->
          <template v-else-if="column.key === 'taskType'">
            <a-tag color="blue">{{ record.taskType }}</a-tag>
          </template>

          <!-- 文档ID列表 -->
          <template v-else-if="column.key === 'resourceIds'">
            <a-tooltip
              v-if="record.resourceIds && record.resourceIds.length > 0"
              :title="record.resourceIds.join(', ')"
            >
              <span class="text-truncate">{{ record.resourceIds.join(', ') }}</span>
            </a-tooltip>
            <span v-else class="text-muted">-</span>
          </template>

          <!-- 统计信息 -->
          <template v-else-if="column.key === 'stats'">
            <span v-if="record.stats">
              <template v-if="record.stats.entity_count">实体: {{ record.stats.entity_count }}</template>
              <template v-if="record.stats.relation_count"> 关系: {{ record.stats.relation_count }}</template>
            </span>
            <span v-else class="text-muted">-</span>
          </template>

          <!-- 时间信息 -->
          <template v-else-if="column.key === 'timeInfo'">
            <div v-if="record.startTime || record.endTime" class="time-info">
              <div v-if="record.startTime">开始: {{ formatTime(record.startTime) }}</div>
              <div v-if="record.endTime">结束: {{ formatTime(record.endTime) }}</div>
            </div>
            <span v-else class="text-muted">-</span>
          </template>

          <!-- 创建时间 -->
          <template v-else-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="查看">
                <a-button type="link" size="small" @click="handleView(record as GraphRAGTaskListVO)">
                  <template #icon><EyeOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="编辑">
                <a-button type="link" size="small" @click="handleUpdate(record as GraphRAGTaskListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button type="link" size="small" danger @click="handleDelete(record as GraphRAGTaskListVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </template>
  </TablePageLayout>

  <!-- GraphRAG 任务表单弹窗 -->
  <GraphRAGTaskForm v-model:visible="formVisible" :task-id="currentTaskId" @success="handleFormSuccess" />
</template>

<script setup lang="ts">
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getGraphRAGTaskList, deleteGraphRAGTask } from '@/api/education/graphRagTask.ts'
import { getCourseList } from '@/api/education/course.ts'
import GraphRAGTaskForm from './components/GraphRAGTaskForm.vue'
import { parseTime } from '@/utils/common.ts'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import type { CourseListVO } from '@/types/api/education/course.ts'
import type { GraphRAGTaskListVO, GraphRAGTaskQueryDTO } from '@/types/api/education/graphragTask.ts'

// 表格列定义
const columns = [
  {
    title: '任务ID',
    dataIndex: 'taskId',
    key: 'taskId',
    width: 80,
    fixed: 'left' as const,
  },
  { title: '任务状态', dataIndex: 'taskStatus', key: 'taskStatus', width: 100 },
  { title: '任务类型', dataIndex: 'taskType', key: 'taskType', width: 150 },
  { title: '文档ID列表', dataIndex: 'resourceIds', key: 'resourceIds', width: 200, ellipsis: true },
  { title: '统计信息', dataIndex: 'stats', key: 'stats', width: 150 },
  { title: '任务信息', dataIndex: 'taskMessage', key: 'taskMessage', width: 200, ellipsis: true },
  { title: '时间信息', key: 'timeInfo', width: 150 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: '操作', key: 'action', fixed: 'right' as const, width: 180 },
]

// 数据状态
const loading = ref(false)
const taskList = ref<GraphRAGTaskListVO[]>([])
const courseLoading = ref(false)
const courseList = ref<CourseListVO[]>([])
const selectedCourseId = ref<number>()
const selectedRowKeys = ref<number[]>([])

// 查询参数
const queryParams = reactive<GraphRAGTaskQueryDTO>({
  courseId: undefined as any,
  taskStatus: undefined,
  taskType: undefined,
  pageNum: 1,
  pageSize: 10,
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys
  },
}))

// 弹窗状态
const formVisible = ref(false)
const currentTaskId = ref<number>()

// 获取课程列表
const loadCourseList = async () => {
  courseLoading.value = true
  try {
    const res = await getCourseList({
      page: 1,
      size: 1000,
      status: '0',
    })
    if (res.code === 200 && res.data) {
      courseList.value = res.data.rows || []
    }
  } catch (_e) {
    message.error('获取课程列表失败')
  } finally {
    courseLoading.value = false
  }
}

// 获取任务列表
const getList = async () => {
  loading.value = true
  try {
    // 确保使用当前选择的课程ID
    queryParams.courseId = selectedCourseId.value

    const res = await getGraphRAGTaskList(queryParams)
    if (res.code === 200 && res.data) {
      taskList.value = res.data.rows || []
      pagination.total = res.data.total || 0
    }
  } catch (_e) {
    message.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 课程切换
const handleCourseChange = () => {
  queryParams.page = 1
  pagination.current = 1
  selectedRowKeys.value = []
  getList()
}

// 搜索功能
const handleQuery = () => {
  queryParams.page = 1
  pagination.current = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  queryParams.taskStatus = undefined
  queryParams.taskType = undefined
  queryParams.page = 1
  pagination.current = 1
  getList()
}

// 表格变化（分页、排序）
const handleTableChange = (pag: any) => {
  queryParams.page = pag.current
  queryParams.size = pag.pageSize
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  getList()
}

// 新增任务
const handleAdd = () => {
  if (!selectedCourseId.value) {
    message.warning('请先选择课程')
    return
  }
  currentTaskId.value = undefined
  formVisible.value = true
}

// 查看任务
const handleView = (record: GraphRAGTaskListVO) => {
  currentTaskId.value = record.taskId
  formVisible.value = true
}

// 修改任务
const handleUpdate = (record: GraphRAGTaskListVO) => {
  currentTaskId.value = record.taskId
  formVisible.value = true
}

// 删除任务
const handleDelete = (record: GraphRAGTaskListVO) => {
  Modal.confirm({
    title: '系统提示',
    content: `确认要删除任务ID为 ${record.taskId} 的记录吗？`,
    onOk: async () => {
      try {
        const res = await deleteGraphRAGTask(String(record.taskId))
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

// 批量删除
const handleBatchDelete = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请至少选择一条记录')
    return
  }
  Modal.confirm({
    title: '系统提示',
    content: `确认要删除选中的 ${selectedRowKeys.value.length} 条记录吗？`,
    onOk: async () => {
      try {
        const res = await deleteGraphRAGTask(selectedRowKeys.value.join(','))
        if (res.code === 200) {
          message.success('删除成功')
          selectedRowKeys.value = []
          getList()
        }
      } catch (_e) {
        message.error('删除失败')
      }
    },
  })
}

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

// 初始化
onMounted(() => {
  loadCourseList()
  // 如果有默认课程，可以在这里设置
  // selectedCourseId.value = xxx
  // getList()
})
</script>

<style scoped>
.actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 16px;
}

.actions-filter {
  flex-shrink: 0;
}

.text-truncate {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-muted {
  color: #999;
}

.time-info {
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .actions-container {
    flex-direction: column;
    align-items: stretch;
  }

  .actions-filter {
    width: 100%;
  }
}
</style>
