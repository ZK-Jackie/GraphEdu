<script setup lang="ts">
/**
 * 课程门户页
 * 显示单个课程的完整信息，包括基本信息、教师、教材等
 * 提供学习入口和加入课程功能
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import CommonPageLayout from '@/layout/CommonPageLayout.vue'
import CoursePortalSkeleton from './components/CoursePortalSkeleton.vue'
import CoursePortalHero from './components/CoursePortalHero.vue'
import CourseDescription from './components/CourseDescription.vue'
import TeacherSection from './components/TeacherSection.vue'
import { getCourseDetail } from '@/api/education/course'
import { joinCourse as apiJoinCourse } from '@/api/education/student_course'
import useLearningStore from '@/stores/modules/learning'
import useUserStore from '@/stores/modules/user'

import type { CourseDetailVO } from '@/types/api/education/course.ts'

const route = useRoute()
const router = useRouter()
const learningStore = useLearningStore()
const userStore = useUserStore()

// 状态
const loading = ref(true)
const courseDetail = ref<CourseDetailVO | null>(null)
const joining = ref(false)

// 获取课程ID
const courseId = computed<number>(() => {
  const id = route.params.courseId
  if (typeof id === 'string') return parseInt(id)
  if (Array.isArray(id)) return parseInt(id[0] ?? '0')
  return 0
})

// 检查是否已加入课程
const isJoined = computed(() => {
  return learningStore.isLearning(courseId.value)
})

// 获取学习进度
const progress = computed(() => {
  return learningStore.getCourseProgress(courseId.value)
})

// 检查是否为访客（未登录）
const isGuest = computed(() => !userStore.isLoggedIn)

// 检查当前用户是否是该课程的授课教师
const isTeacherOfCourse = computed(() => {
  if (!userStore.isTeacher || !courseDetail.value?.teachers) return false
  return courseDetail.value.teachers.some((t) => t.teacherId === userStore.teacherInfo?.teacherId)
})

// 用户是否可以看到管理按钮（是该课程的教师或是管理员）
const canManage = computed(() => isTeacherOfCourse.value || userStore.isAdmin)

// 加载课程详情
const loadCourseDetail = async () => {
  loading.value = true
  try {
    const res = await getCourseDetail(courseId.value)
    if (res.code === 200 && res.data) {
      courseDetail.value = res.data
    } else {
      message.error(res.msg || '加载课程详情失败')
    }
  } catch (error) {
    console.error('[Course Portal] 加载课程详情失败:', error)
    message.error('加载课程详情失败')
  } finally {
    loading.value = false
  }
}

// 加入课程
const handleJoinCourse = async () => {
  if (isGuest.value) {
    message.warning('请先登录')
    router.push({
      name: 'Login',
      query: { redirect: route.fullPath },
    })
    return
  }

  joining.value = true
  try {
    const res = await apiJoinCourse({ courseId: courseId.value })
    if (res.code === 200) {
      message.success('成功加入课程')
      // 刷新学习课程列表
      await learningStore.loadMyCourses()
    } else {
      message.error(res.msg || '加入课程失败')
    }
  } catch (error) {
    console.error('[Course Portal] 加入课程失败:', error)
    message.error('加入课程失败')
  } finally {
    joining.value = false
  }
}

// 开始学习
const handleStartLearning = () => {
  if (!isJoined.value) {
    message.warning('请先加入课程后再开始学习')
    return
  }
  router.push({
    path: `/course/learn/${courseId.value}`,
  })
}

// 管理课程
const handleManageCourse = () => {
  router.push(`/course/manage/${courseId.value}`)
}

// 页面加载时获取数据
onMounted(async () => {
  // 如果已登录，先加载学习课程列表
  if (userStore.isLoggedIn && learningStore.myCourses.length === 0) {
    await learningStore.loadMyCourses()
  }
  // 加载课程详情
  await loadCourseDetail()
})
</script>

<template>
  <CommonPageLayout>
    <!-- 骨架屏 -->
    <CoursePortalSkeleton v-if="loading" />

    <!-- 课程内容 -->
    <div v-else-if="courseDetail" class="course-portal-content">
      <!-- 英雄区 -->
      <CoursePortalHero
        :course="courseDetail"
        :is-joined="isJoined"
        :progress="progress"
        :joining="joining"
        :can-manage="canManage"
        :is-student="userStore.isStudent"
        @join="handleJoinCourse"
        @start-learning="handleStartLearning"
        @manage-course="handleManageCourse"
      />

      <!-- 课程描述 -->
      <CourseDescription :course="courseDetail" />

      <!-- 授课教师 -->
      <TeacherSection :teachers="courseDetail.teachers" />
    </div>

    <!-- 错误状态 -->
    <a-result v-else status="error" title="加载失败" sub-title="课程详情加载失败，请稍后重试">
      <template #extra>
        <a-button type="primary" @click="router.back()"> 返回上一页 </a-button>
      </template>
    </a-result>
  </CommonPageLayout>
</template>

<style scoped>
.course-portal-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  padding: 2px;
}

/* 自定义滚动条样式 */
.course-portal-content::-webkit-scrollbar {
  width: 6px;
}

.course-portal-content::-webkit-scrollbar-track {
  background: var(--ge-bg-page);
  border-radius: 3px;
}

.course-portal-content::-webkit-scrollbar-thumb {
  background: var(--ge-border-color);
  border-radius: 3px;
}

.course-portal-content::-webkit-scrollbar-thumb:hover {
  background: var(--ge-text-tertiary);
}
</style>
