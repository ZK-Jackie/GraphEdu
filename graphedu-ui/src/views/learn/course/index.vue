<script setup lang="ts">
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { ExclamationCircleOutlined, PlusCircleOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { createVNode } from 'vue'
import { getMyCourseList, joinCourse, leaveCourse } from '@/api/education/student_course'
import AllCoursesTab from './components/AllCoursesTab.vue'
import EnrolledCoursesTab from './components/EnrolledCoursesTab.vue'
import AvailableCoursesTab from './components/AvailableCoursesTab.vue'
import JoinByCodeDialog from './components/JoinByCodeDialog.vue'
import TeacherCourseForm from './components/TeacherCourseForm.vue'
import CommonPageLayout from '@/layout/CommonPageLayout.vue'
import type { CourseListVO } from '@/types/api/education/course.ts'

const { t } = useI18n()
const router = useRouter()

// 已加入课程 ID 集合（供"全部"/"未加入"Tab 展示已加入标记使用）
const myCourseIds = ref<Set<number>>(new Set())
const activeTab = ref<'all' | 'enrolled' | 'available'>('all')

// 对话框状态
const joinByCodeVisible = ref(false)
const createCourseVisible = ref(false)

// 批量加载我的课程 ID（全量，最多 500 条）
const loadMyCourseIds = async () => {
  try {
    const res = await getMyCourseList({ page: 1, size: 100 })
    if (res.code === 200) {
      const ids = new Set<number>()
      res.data.rows.forEach((item) => ids.add(item.courseId))
      myCourseIds.value = ids
    }
  } catch (_) {
    // 静默失败，不影响主流程
  }
}

// 加入课程
const handleJoinCourse = async (course: CourseListVO) => {
  try {
    const res = await joinCourse({ courseId: course.courseId })
    if (res.code === 200) {
      myCourseIds.value = new Set([...myCourseIds.value, course.courseId])
      message.success(t('education.course.joinCourseSuccess'))
    } else {
      message.error(res.msg || t('education.course.joinCourseFailed'))
    }
  } catch (error: any) {
    message.error(error.response?.data?.msg || t('education.course.joinCourseFailed'))
  }
}

// 退出课程
const handleLeaveCourse = (course: CourseListVO) => {
  Modal.confirm({
    title: t('education.course.leaveCourse'),
    icon: createVNode(ExclamationCircleOutlined),
    content: t('education.course.leaveCourseConfirm', { courseName: course.courseName }),
    okText: t('common.confirm'),
    cancelText: t('common.cancel'),
    onOk: async () => {
      try {
        const res = await leaveCourse(course.courseId)
        if (res.code === 200) {
          const next = new Set(myCourseIds.value)
          next.delete(course.courseId)
          myCourseIds.value = next
          message.success(t('education.course.leaveCourseSuccess'))
        } else {
          message.error(res.msg || t('education.course.leaveCourseFailed'))
        }
      } catch (error: any) {
        message.error(error.response?.data?.msg || t('education.course.leaveCourseFailed'))
      }
    },
  })
}

// 查看课程门户
const handleViewDetail = (course: CourseListVO) => {
  router.push(`/learn/course/${course.courseId}/portal`)
}

// 继续学习
const handleContinueLearning = (course: CourseListVO) => {
  router.push(`/course/learn/${course.courseId}`)
}

// 管理课程
const handleManageCourse = (course: CourseListVO) => {
  router.push(`/course/manage/${course.courseId}`)
}

// 已选课程加载完毕时同步 myCourseIds（EnrolledCoursesTab 回调）
const handleEnrolledLoaded = (ids: number[]) => {
  myCourseIds.value = new Set(ids)
}

// 通过课程码加入成功
const handleJoinByCodeSuccess = () => {
  loadMyCourseIds()
}

// 课程创建成功 — 刷新全部课程标签
const allCoursesTabRef = ref<InstanceType<typeof AllCoursesTab> | null>(null)
const handleCreateCourseSuccess = () => {
  allCoursesTabRef.value?.loadMore?.(true)
}

onMounted(() => {
  loadMyCourseIds()
})
</script>

<template>
  <CommonPageLayout :title="t('education.course.browseTitle')" :subtitle="t('education.course.browseSubtitle')">
    <template #actions>
      <a-space>
        <a-button v-permit="'web:learn:course:join'" type="primary" @click="joinByCodeVisible = true">
          <template #icon><PlusCircleOutlined /></template>
          {{ t('learning.joinByCode') }}
        </a-button>
        <a-button v-permit="'admin:education:course:add'" type="primary" @click="createCourseVisible = true">
          <template #icon><PlusOutlined /></template>
          {{ t('learning.createCourse') }}
        </a-button>
      </a-space>
    </template>

    <a-tabs v-model:active-key="activeTab" class="course-tabs">
      <!-- 全部课程 -->
      <a-tab-pane key="all" :tab="t('learning.courseTabs.all')">
        <AllCoursesTab
          ref="allCoursesTabRef"
          :my-course-ids="myCourseIds"
          @join="handleJoinCourse"
          @leave="handleLeaveCourse"
          @view-detail="handleViewDetail"
          @continue-learning="handleContinueLearning"
          @manage-course="handleManageCourse"
        />
      </a-tab-pane>

      <!-- 已加入课程 -->
      <a-tab-pane key="enrolled" :tab="t('learning.courseTabs.enrolled')">
        <EnrolledCoursesTab
          @leave="handleLeaveCourse"
          @continue-learning="handleContinueLearning"
          @view-detail="handleViewDetail"
          @manage-course="handleManageCourse"
          @enrolled-loaded="handleEnrolledLoaded"
        />
      </a-tab-pane>

      <!-- 未加入课程 -->
      <a-tab-pane key="available" :tab="t('learning.courseTabs.available')">
        <AvailableCoursesTab
          :my-course-ids="myCourseIds"
          @join="handleJoinCourse"
          @view-detail="handleViewDetail"
          @manage-course="handleManageCourse"
        />
      </a-tab-pane>
    </a-tabs>

    <!-- 通过课程码加入对话框 -->
    <JoinByCodeDialog v-model:visible="joinByCodeVisible" @success="handleJoinByCodeSuccess" />
    <!-- 教师新建课程对话框 -->
    <TeacherCourseForm v-model:visible="createCourseVisible" @success="handleCreateCourseSuccess" />
  </CommonPageLayout>
</template>

<style scoped>
.course-tabs {
  background: var(--ge-bg-container);
  border-radius: 8px;
  padding: 16px 24px 0;
}

.course-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .course-tabs {
    padding: 12px 16px 0;
  }
}
</style>
