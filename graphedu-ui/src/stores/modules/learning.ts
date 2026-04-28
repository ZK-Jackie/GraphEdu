import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { getMyCourseList, updateLearningProgress, getStudentCourseOverview } from '@/api/education/student_course'
import type { StudentCourseListVO, StudentCourseQueryDTO } from '@/types/api/education/course.ts'
import type { StudentCourseOverviewVO } from '@/types/api/education/stats.ts'

const useLearningStore = defineStore('learning', () => {
  // 状态
  const myCourses = ref<StudentCourseListVO[]>([])
  const loading = ref(false)
  const currentCourseOverview = ref<StudentCourseOverviewVO | null>(null)

  // 计算属性：进行中的课程
  const inProgressCourses = computed(() => myCourses.value.filter((c) => c.progress < 100))

  // 计算属性：已完成的课程
  const completedCourses = computed(() => myCourses.value.filter((c) => c.progress === 100))

  // 加载我的课程列表
  async function loadMyCourses(params?: StudentCourseQueryDTO) {
    loading.value = true
    try {
      const res = await getMyCourseList({ page: 1, size: 100, ...params })
      if (res.code === 200) {
        myCourses.value = res.data.rows || []
      }
    } catch (error) {
      console.error('[Learning Store] 加载课程列表失败:', error)
      message.error('加载课程列表失败')
    } finally {
      loading.value = false
    }
  }

  // 更新学习进度
  async function updateProgress(courseId: number, progress: number) {
    try {
      const res = await updateLearningProgress({ courseId, progress })
      if (res.code === 200) {
        // 更新本地缓存
        const course = myCourses.value.find((c) => c.courseId === courseId)
        if (course) {
          course.progress = progress
          course.lastStudyTime = new Date().toISOString()
        }
        message.success('学习进度已更新')
      }
    } catch (error) {
      console.error('[Learning Store] 更新学习进度失败:', error)
      message.error('更新学习进度失败')
      throw error
    }
  }

  // 检查是否在学习某课程
  function isLearning(courseId: number): boolean {
    return myCourses.value.some((c) => c.courseId === courseId)
  }

  // 获取课程学习进度
  function getCourseProgress(courseId: number): number {
    const course = myCourses.value.find((c) => c.courseId === courseId)
    return course?.progress || 0
  }

  // 清空课程列表
  function clearCourses() {
    myCourses.value = []
  }

  // 加载课程概览
  async function loadCourseOverview(courseId: number) {
    try {
      const res = await getStudentCourseOverview(courseId)
      if (res.code === 200) {
        currentCourseOverview.value = res.data
      } else {
        message.error(res.msg || '加载课程概览失败')
      }
    } catch (error) {
      console.error('[Learning Store] 加载课程概览失败:', error)
      message.error('加载课程概览失败')
      throw error
    }
    return currentCourseOverview.value
  }

  // 清空课程概览
  function clearCourseOverview() {
    currentCourseOverview.value = null
  }

  return {
    // 状态
    myCourses,
    loading,
    currentCourseOverview,

    // 计算属性
    inProgressCourses,
    completedCourses,

    // 方法
    loadMyCourses,
    updateProgress,
    isLearning,
    getCourseProgress,
    clearCourses,
    loadCourseOverview,
    clearCourseOverview,
  }
})

export default useLearningStore
