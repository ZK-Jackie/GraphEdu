<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useIntersectionObserver } from '@vueuse/core'
import {
  CheckCircleOutlined,
  BankOutlined,
  UserOutlined,
  PlayCircleOutlined,
  MinusOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { getMyCourseList } from '@/api/education/student_course'
import CourseCardSkeleton from './CourseCardSkeleton.vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import type { CourseListVO, StudentCourseListVO } from '@/types/api/education/course.ts'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { t } = useI18n()

interface Emits {
  (e: 'leave', course: CourseListVO): void
  (e: 'continueLearning', course: CourseListVO): void
  (e: 'viewDetail', course: CourseListVO): void
  (e: 'manageCourse', course: CourseListVO): void
  /** 数据加载完成，通知父组件同步 myCourseIds */
  (e: 'enrolledLoaded', ids: number[]): void
}

const emit = defineEmits<Emits>()

// 默认封面
const defaultCover = 'https://via.placeholder.com/300x180?text=Course'

// 列表数据
const enrollmentList = ref<StudentCourseListVO[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const hasMore = ref(true)
const initialLoading = ref(true)

// 无限滚动哨兵
const sentinel = ref<HTMLElement | null>(null)

// 加载一页
const loadMore = async (reset = false) => {
  if (loading.value || (!hasMore.value && !reset)) return
  loading.value = true
  if (reset) {
    page.value = 1
    hasMore.value = true
  }
  try {
    const res = await getMyCourseList({ page: page.value, size: pageSize })
    if (res.code === 200) {
      const rows = res.data.rows || []
      if (reset) {
        enrollmentList.value = rows
      } else {
        enrollmentList.value.push(...rows)
      }
      hasMore.value = enrollmentList.value.length < res.data.total
      page.value += 1
      // 首页加载完毕通知父组件同步 myCourseIds
      if (reset || page.value === 2) {
        emit(
          'enrolledLoaded',
          enrollmentList.value.map((e) => e.courseId)
        )
      }
    }
  } catch (_) {
    // 静默失败
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

// 将 enrollment 转为 CourseListVO 片段（供 leave/continue/viewDetail 事件使用）
const toCourseVO = (item: StudentCourseListVO): CourseListVO => ({
  courseId: item.courseId,
  courseCode: item.courseCode || '',
  courseName: item.courseName || '',
  coverFileId: item.coverFileId,
  coverUrl: item.coverUrl,
  status: '0',
  isPublic: 'Y',
  studentCount: 0,
  viewCount: 0,
})

// 格式化最后学习时间
const formatLastStudyTime = (lastStudyTime?: string): string => {
  if (!lastStudyTime) return t('learning.neverLearned', '尚未开始学习')
  return dayjs(lastStudyTime).fromNow()
}

// IntersectionObserver
useIntersectionObserver(sentinel, ([entry]) => {
  if (entry?.isIntersecting && hasMore.value && !loading.value) {
    loadMore()
  }
})

onMounted(() => loadMore(true))
</script>

<template>
  <div class="enrolled-courses-tab">
    <!-- 骨架屏（首次加载） -->
    <CourseCardSkeleton v-if="initialLoading" :count="6" />

    <!-- 空状态 -->
    <a-empty
      v-else-if="!loading && enrollmentList.length === 0"
      :description="t('learning.enrolledCourses.empty')"
      class="empty-container"
    >
      <p class="empty-hint">{{ t('learning.enrolledCourses.emptyHint') }}</p>
    </a-empty>

    <!-- 课程卡片网格 -->
    <div v-else class="course-grid">
      <a-card v-for="item in enrollmentList" :key="item.id" class="course-card" hoverable :body-style="{ padding: 0 }">
        <!-- 封面 -->
        <div class="card-body">
          <div class="course-cover" @click="emit('viewDetail', toCourseVO(item))">
            <img :src="item.coverUrl || defaultCover" :alt="item.courseName" />
            <div class="joined-badge">
              <CheckCircleOutlined />
              {{ t('education.course.alreadyJoined') }}
            </div>
          </div>

          <!-- 信息 -->
          <div class="course-info">
            <h3 class="course-name" :title="item.courseName">
              {{ item.courseName }}
            </h3>
            <p class="course-code">{{ item.courseCode }}</p>

            <!-- 学习进度 -->
            <div class="course-progress">
              <div class="progress-header">
                <span class="progress-label">{{ t('common.learningProgress') }}</span>
                <span
                  class="progress-value"
                  :style="{
                    color: item.progress === 100 ? '#52c41a' : '#1890ff',
                  }"
                >
                  {{ item.progress }}%
                </span>
              </div>
              <a-progress
                :percent="item.progress"
                :stroke-color="item.progress === 100 ? '#52c41a' : '#1890ff'"
                :show-info="false"
              />
            </div>

            <!-- 最后学习时间 -->
            <p class="last-study-time">
              <ClockCircleOutlined />
              {{ t('learning.lastStudyTime') }}:
              {{ formatLastStudyTime(item.lastStudyTime) }}
            </p>
          </div>
        </div>

        <!-- 操作 -->
        <div class="course-actions">
          <a-button
            v-permit="'web:learn:course:learn'"
            type="primary"
            @click="emit('continueLearning', toCourseVO(item))"
          >
            <template #icon><PlayCircleOutlined /></template>
            {{ t('common.continueLearning') }}
          </a-button>
          <a-button @click="emit('viewDetail', toCourseVO(item))">
            <template #icon><EyeOutlined /></template>
            {{ t('education.course.viewDetail') }}
          </a-button>
          <a-button v-permit="'web:learn:course:leave'" danger ghost @click="emit('leave', toCourseVO(item))">
            <template #icon><MinusOutlined /></template>
            {{ t('education.course.leaveCourse') }}
          </a-button>
          <a-button v-permit="'web:learn:course:manage'" @click="emit('manageCourse', toCourseVO(item))">
            <template #icon><SettingOutlined /></template>
            {{ t('education.course.manageCourse', '管理课程') }}
          </a-button>
        </div>
      </a-card>
    </div>

    <!-- 无限滚动哨兵 -->
    <div ref="sentinel" class="sentinel">
      <a-spin v-if="loading && !initialLoading" size="small" />
      <span v-else-if="!hasMore && enrollmentList.length > 0" class="no-more">
        {{ t('common.noMoreData', '没有更多') }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.enrolled-courses-tab {
  width: 100%;
}

.empty-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-hint {
  color: var(--ge-text-secondary);
  margin-bottom: 16px;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 16px;
}

.course-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  height: 100%;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-body {
  display: flex;
  flex-direction: column;
}

.course-cover {
  height: 180px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
}

.course-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.course-card:hover .course-cover img {
  transform: scale(1.05);
}

.joined-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(82, 196, 26, 0.9);
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.course-info {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.course-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--ge-text-primary);
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-code {
  font-size: 12px;
  color: var(--ge-text-secondary);
  margin: 0 0 12px 0;
}

.course-progress {
  margin-bottom: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.progress-label {
  font-size: 12px;
  color: var(--ge-text-secondary);
}

.progress-value {
  font-size: 12px;
  font-weight: 600;
}

.last-study-time {
  font-size: 12px;
  color: var(--ge-text-secondary);
  margin: 8px 0 0 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.course-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--ge-border-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.course-actions :deep(.ant-btn) {
  width: 100%;
}

.sentinel {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px 0;
  min-height: 60px;
}

.no-more {
  font-size: 13px;
  color: var(--ge-text-disabled);
}

/* ============ 移动端 ============ */
@media (max-width: 768px) {
  .course-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .card-body {
    flex-direction: row;
  }

  .course-cover {
    width: 120px;
    height: auto;
    min-height: 100px;
    flex-shrink: 0;
  }

  .joined-badge {
    top: 6px;
    right: 6px;
    padding: 2px 6px;
    font-size: 10px;
  }

  .course-info {
    padding: 10px 12px;
    min-width: 0;
  }

  .course-name {
    font-size: 14px;
    margin: 0 0 4px 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    white-space: normal;
  }

  .course-code {
    margin: 0 0 6px 0;
  }

  .course-progress {
    margin-bottom: 4px;
  }

  .last-study-time {
    margin: 4px 0 0 0;
  }

  .course-actions {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 12px;
  }

  .course-actions :deep(.ant-btn) {
    width: auto;
  }
}
</style>
