<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('education.course.courseName')">
            <a-input
              v-model:value="queryParams.courseName"
              :placeholder="t('education.course.courseNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('education.course.courseCode')">
            <a-input
              v-model:value="queryParams.courseCode"
              :placeholder="t('education.course.courseCodePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.faculty')">
            <a-input
              v-model:value="queryParams.faculty"
              :placeholder="t('common.facultyPlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('education.course.statusPlaceholder')"
              allow-clear
              style="width: 150px"
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
      </a-space>
    </template>

    <!-- 课程表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="courseList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="courseId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <!-- 状态列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-switch
              :checked="record.status === '0'"
              :checked-children="t('common.normal')"
              :un-checked-children="t('common.disabled')"
              @change="(checked: any) => handleStatusChange(record as CourseListVO, checked)"
            />
          </template>
          <!-- 是否公开列 -->
          <template v-else-if="column.key === 'isPublic'">
            <DictTag :options="sys_yes_no" :value="record.isPublic" />
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('education.chapter.chapterManage')">
                <a-button type="link" size="small" @click="handleManageChapters(record as CourseListVO)">
                  <template #icon><FolderOpenOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('education.course.bindTeachers')">
                <a-button type="link" size="small" @click="handleBindTeachers(record as CourseListVO)">
                  <template #icon><UserOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" @click="handleUpdate(record as CourseListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.delete')">
                <a-button type="link" size="small" danger @click="handleDelete(record as CourseListVO)">
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
  <!-- 课程表单弹窗 -->
  <CourseForm v-model:visible="formVisible" :course-id="currentCourseId ?? undefined" @success="handleFormSuccess" />
  <!-- 绑定教师对话框 -->
  <BindTeacherDialog
    v-model:visible="bindTeacherVisible"
    :course-id="currentCourseId ?? null"
    @success="handleBindTeachersSuccess"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  UserOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getCourseList, deleteCourse, changeCourseStatus } from '@/api/education/course.ts'
import CourseForm from './components/CourseForm.vue'
import BindTeacherDialog from './components/BindTeacherDialog.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import DictSelect from '@/components/dict/DictSelect.vue'
import DictTag from '@/components/dict/DictTag.vue'
import type { CourseListVO, CourseQueryDTO } from '@/types/api/education/course.ts'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

const { t } = useI18n()
const router = useRouter()

// 是否公开映射
const { sys_yes_no } = useDict('sys_yes_no')

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('education.course.courseCode'), dataIndex: 'courseCode', key: 'courseCode', width: 150 },
  { title: t('education.course.courseName'), dataIndex: 'courseName', key: 'courseName', width: 200 },
  { title: t('common.faculty'), dataIndex: 'faculty', key: 'faculty', width: 150 },
  { title: t('education.course.studentCount'), dataIndex: 'studentCount', key: 'studentCount', width: 100 },
  { title: t('education.course.viewCount'), dataIndex: 'viewCount', key: 'viewCount', width: 100 },
  { title: t('education.course.isPublic'), dataIndex: 'isPublic', key: 'isPublic', width: 100 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 150 },
]

// 数据状态
const loading = ref(false)
const courseList = ref<CourseListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: CourseQueryDTO = {
  page: 1,
  size: 10,
  courseName: undefined,
  courseCode: undefined,
  faculty: undefined,
  status: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: CourseQueryDTO = { ...defaultQueryParams }

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<CourseListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[], rows: any[]) => {
    selectedRowKeys.value = keys as number[]
    selectedRows.value = rows as CourseListVO[]
  },
}))

// 弹窗状态
const formVisible = ref(false)
const bindTeacherVisible = ref(false)

// 当前操作的课程
const currentCourseId = ref<number>()

// 获取课程列表
const getList = async () => {
  loading.value = true
  try {
    const res = await getCourseList(queryParams)
    if (res.code === 200) {
      courseList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (_e) {
    message.error(t('education.course.getCourseListFailed'))
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
} = usePaginationQuery<CourseQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['courseName', 'courseCode', 'faculty', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 搜索课程
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

// 新增课程
const handleAdd = () => {
  currentCourseId.value = undefined
  formVisible.value = true
}

// 修改课程
const handleUpdate = (record?: CourseListVO) => {
  if (record) {
    currentCourseId.value = record.courseId
  } else if (selectedRows.value.length === 1) {
    currentCourseId.value = selectedRows.value[0]?.courseId
  }
  formVisible.value = true
}

// 删除课程
const handleDelete = (record?: CourseListVO) => {
  let courseIds: string
  if (record) {
    courseIds = String(record.courseId)
  } else {
    courseIds = selectedRowKeys.value.join(',')
  }

  Modal.confirm({
    title: t('common.systemTip'),
    content: record
      ? t('education.course.deleteCourseConfirm', { courseName: record.courseName })
      : t('common.deleteConfirm'),
    onOk: async () => {
      try {
        const res = await deleteCourse(courseIds)
        if (res.code === 200) {
          message.success(t('common.deleteSuccess'))
          getList()
        }
      } catch (_e) {
        message.error(t('common.deleteFailed'))
      }
    },
  })
}

// 状态变更
const handleStatusChange = async (record: CourseListVO, checked: boolean) => {
  try {
    const res = await changeCourseStatus({
      courseId: record.courseId,
      status: checked ? '0' : '1',
    })
    if (res.code === 200) {
      message.success(t('education.course.courseStatusChangeSuccess'))
      getList()
    }
  } catch (_e) {
    message.error(t('education.course.courseStatusChangeFailed'))
  }
}

// 绑定教师
const handleBindTeachers = (record: CourseListVO) => {
  currentCourseId.value = record.courseId
  bindTeacherVisible.value = true
}

// 绑定教师成功
const handleBindTeachersSuccess = () => {
  bindTeacherVisible.value = false
  message.success(t('education.course.bindTeachersSuccess'))
}

// 管理章节
const handleManageChapters = (record: CourseListVO) => {
  router.push({
    path: `/course/manage/${record.courseId}/chapter`,
  })
}

// 分页组件的 show-total 回调
const showTotal = (total: number) => `${t('common.total')} ${total} ${t('common.items')}`

// 导出课程
const handleExport = () => {
  message.info('导出功能开发中')
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
  getList()
})
</script>
