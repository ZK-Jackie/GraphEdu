<template>
  <div class="student-manage-page">
    <!-- 页面头部 -->
    <a-page-header :title="t('education.student.studentManage')" @back="goBack">
      <template #extra>
        <a-button @click="loadStudents">
          <template #icon><ReloadOutlined /></template>
          {{ t('common.refresh') }}
        </a-button>
      </template>
    </a-page-header>

    <!-- 主内容区域 -->
    <div class="student-content">
      <!-- 顶部统计条 -->
      <a-row v-if="stats" :gutter="16" class="mb-4">
        <a-col :span="6">
          <a-card size="small">
            <a-statistic :title="t('education.student.totalStudents')" :value="stats.totalStudents" />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <a-statistic :title="t('education.student.avgProgress')" :value="stats.averageProgress" suffix="%" />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <a-statistic :title="t('education.student.completedStudents')" :value="stats.completedStudents" />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <a-statistic :title="t('education.student.todayActive')" :value="stats.todayActive" />
          </a-card>
        </a-col>
      </a-row>

      <!-- 搜索栏 -->
      <a-card :bordered="false" class="mb-4">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('common.realName')">
            <a-input
              v-model:value="queryParams.realName"
              :placeholder="t('common.realNamePlaceholder')"
              allow-clear
              style="width: 160px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('education.student.studentNo')">
            <a-input
              v-model:value="queryParams.studentNo"
              :placeholder="t('education.student.studentNoPlaceholder')"
              allow-clear
              style="width: 160px"
              @press-enter="handleQuery"
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

      <!-- 操作栏 -->
      <div class="mb-4 flex items-center justify-between">
        <a-space>
          <a-button type="primary" @click="assignVisible = true">
            <template #icon><UserAddOutlined /></template>
            {{ t('common.assignCourse') }}
          </a-button>
        </a-space>
      </div>

      <!-- 学生列表表格 -->
      <a-table
        :columns="columns"
        :data-source="filteredStudents"
        :loading="loading"
        :pagination="pagination"
        row-key="studentId"
        :scroll="{ y: 400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'index'">
            {{ (queryParams.page - 1) * queryParams.size + filteredStudents.indexOf(record as CourseStudentVO) + 1 }}
          </template>
          <template v-else-if="column.key === 'progress'">
            <a-progress :percent="record.progress || 0" :size="'small'" :stroke-width="6" />
          </template>
          <template v-else-if="column.key === 'enrollTime'">
            {{ parseTime(record.enrollTime) || '-' }}
          </template>
          <template v-else-if="column.key === 'lastStudyTime'">
            {{ parseTime(record.lastStudyTime) || '-' }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleViewDetail(record)">
                {{ t('common.viewDetail') }}
              </a-button>
              <a-popconfirm
                :title="
                  t('education.student.revokeConfirm', {
                    name: record.realName,
                  })
                "
                @confirm="handleRevoke(record)"
              >
                <a-button type="link" size="small" danger>{{ t('education.student.revoke') }}</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <!-- 学生详情 Modal -->
      <StudentDetailModal
        v-model:visible="detailVisible"
        :course-id="courseId"
        :student-id="currentStudentId"
        :student-name="currentStudentName"
      />

      <!-- 派发课程对话框 -->
      <AssignStudentDialog
        v-model:visible="assignVisible"
        :course-id="courseId"
        :existing-student-ids="existingStudentIds"
        @success="handleAssignSuccess"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { SearchOutlined, ReloadOutlined, UserAddOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getCourseStudents } from '@/api/education/teach_analytics.ts'
import { revokeCourseFromStudent } from '@/api/education/student_course.ts'
import StudentDetailModal from './components/StudentDetailModal.vue'
import AssignStudentDialog from './components/AssignStudentDialog.vue'
import type { CourseStudentStatsVO, CourseStudentVO } from '@/types/api/education/course.ts'
import { parseTime } from '@/utils/common.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const courseId = ref<number>(Number(route.params.courseId) || 0)

// 数据状态
const loading = ref(false)
const students = ref<CourseStudentVO[]>([])
const stats = ref<CourseStudentStatsVO>()
const serverTotal = ref(0)

// 查询参数
const queryParams = reactive({
  page: 1,
  size: 20,
  realName: undefined as string | undefined,
  studentNo: undefined as string | undefined,
})

// 前端过滤（搜索字段后端暂不支持，保留客户端过滤）
const filteredStudents = computed(() => {
  let result = students.value
  if (queryParams.realName) {
    result = result.filter((s) => s.realName?.includes(queryParams.realName!))
  }
  if (queryParams.studentNo) {
    result = result.filter((s) => s.studentNo?.includes(queryParams.studentNo!))
  }
  return result
})

// 分页
const pagination = computed(() => ({
  current: queryParams.page,
  pageSize: queryParams.size,
  total: serverTotal.value,
  showSizeChanger: true,
  showTotal: (total: number) => `${t('common.total')} ${total} ${t('common.items')}`,
  onChange: (page: number, size: number) => {
    queryParams.page = page
    queryParams.size = size
    loadStudents()
  },
}))

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('common.index'), key: 'index', width: 60, align: 'center' },
  {
    title: t('common.realName'),
    dataIndex: 'realName',
    key: 'realName',
    width: 120,
  },
  {
    title: t('education.student.studentNo'),
    dataIndex: 'studentNo',
    key: 'studentNo',
    width: 120,
  },
  {
    title: t('education.student.className'),
    dataIndex: 'className',
    key: 'className',
    width: 120,
  },
  {
    title: t('common.faculty'),
    dataIndex: 'faculty',
    key: 'faculty',
    width: 120,
  },
  { title: t('common.learningProgress'), key: 'progress', width: 130 },
  {
    title: t('education.student.enrollTime'),
    key: 'enrollTime',
    width: 160,
  },
  {
    title: t('common.lastStudyTime'),
    key: 'lastStudyTime',
    width: 160,
  },
  { title: t('common.operation'), key: 'action', fixed: 'right', width: 140 },
]

// 详情 Modal
const detailVisible = ref(false)
const currentStudentId = ref<number>()
const currentStudentName = ref<string>()

// 派发对话框
const assignVisible = ref(false)
const existingStudentIds = computed(() => students.value.map((s) => s.studentId))

// 加载学生列表
const loadStudents = async () => {
  if (!courseId.value) return
  loading.value = true
  try {
    const res = await getCourseStudents(courseId.value, { page: queryParams.page, size: queryParams.size })
    if (res.code === 200 && res.data) {
      students.value = res.data.students || []
      stats.value = res.data.stats
      serverTotal.value = res.data.total ?? 0
    }
  } catch (_e) {
    message.error(t('education.student.loadStudentListFailed'))
  } finally {
    loading.value = false
  }
}

// 搜索
const handleQuery = () => {
  queryParams.page = 1
  loadStudents()
}

// 重置
const resetQuery = () => {
  queryParams.realName = undefined
  queryParams.studentNo = undefined
  queryParams.page = 1
  loadStudents()
}

// 查看详情
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleViewDetail = (record: any) => {
  const s = record as CourseStudentVO
  currentStudentId.value = s.studentId
  currentStudentName.value = s.realName
  detailVisible.value = true
}

// 撤销选课
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleRevoke = async (record: any) => {
  const s = record as CourseStudentVO
  try {
    const res = await revokeCourseFromStudent(s.enrollmentId)
    if (res.code === 200) {
      message.success(t('education.student.revokeSuccess'))
      await loadStudents()
    }
  } catch (_e) {
    message.error(t('education.student.revokeFailed'))
  }
}

// 派发成功
const handleAssignSuccess = () => {
  assignVisible.value = false
  message.success(t('education.student.assignSuccess'))
  loadStudents()
}

// 返回上一页
const goBack = () => {
  router.push(`/course/manage/${courseId.value}`)
}

onMounted(() => {
  if (!courseId.value) {
    message.error(t('education.student.missingCourseId'))
    router.back()
    return
  }
  loadStudents()
})
</script>

<style scoped>
@reference "#main.css";

.student-manage-page {
  @apply h-full;
}

.student-content {
  @apply px-6 pb-6;
}
</style>
