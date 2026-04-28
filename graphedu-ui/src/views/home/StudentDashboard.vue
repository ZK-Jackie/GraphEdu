<template>
  <div class="student-dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-text">
        <h2 class="welcome-title">{{ greeting }}，{{ userStore.userName }}！</h2>
        <p class="welcome-sub">{{ todayTip }}</p>
      </div>
      <div class="welcome-action">
        <a-button type="primary" @click="goToLearning">继续学习</a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="[16, 16]" class="mt-4">
      <a-col :xs="12" :sm="8" :md="4">
        <StatCard title="累计学习天数" :value="`${summary.totalStudyDays}天`" color="blue" icon="CalendarOutlined" />
      </a-col>
      <a-col :xs="12" :sm="8" :md="4">
        <StatCard
          title="总学习时长"
          :value="formatMinutes(summary.totalStudyMinutes)"
          color="green"
          icon="ClockCircleOutlined"
        />
      </a-col>
      <a-col :xs="12" :sm="8" :md="4">
        <StatCard
          title="有效学习时长"
          :value="formatMinutes(summary.effectiveStudyMinutes)"
          color="cyan"
          icon="AimOutlined"
        />
      </a-col>
      <a-col :xs="12" :sm="8" :md="4">
        <StatCard
          title="复习时长"
          :value="formatMinutes(summary.reviewStudyMinutes)"
          color="geekblue"
          icon="ReloadOutlined"
        />
      </a-col>
      <a-col :xs="12" :sm="8" :md="4">
        <StatCard title="在修课程" :value="`${summary.activeCourseCount}门`" color="orange" icon="BookOutlined" />
      </a-col>
      <a-col :xs="12" :sm="8" :md="4">
        <StatCard title="连续学习" :value="`${summary.consecutiveDays}天`" color="purple" icon="TrophyOutlined" />
      </a-col>
    </a-row>

    <!-- 日历 + 备忘录 -->
    <a-row :gutter="[16, 16]" class="mt-4 equal-height-row">
      <a-col :xs="24" :lg="14">
        <LearningCalendar />
      </a-col>
      <a-col :xs="24" :lg="10">
        <MemoPad storage-key="student" />
      </a-col>
    </a-row>

    <!-- 学习趋势 -->
    <div class="mt-4">
      <LearningTrendChart :daily-active="trendData" :loading="trendLoading">
        <template #extra>
          <a-space :size="4" align="center">
            <a-button size="small" type="text" @click="changeWeek(-1)">
              <LeftOutlined />
            </a-button>
            <span class="week-label">{{ weekLabel }}</span>
            <a-button size="small" type="text" :disabled="isCurrentWeek" @click="changeWeek(1)">
              <RightOutlined />
            </a-button>
          </a-space>
        </template>
      </LearningTrendChart>
    </div>

    <!-- 我的课程 + 薄弱知识点 -->
    <a-row :gutter="[16, 16]" class="mt-4 equal-height-row">
      <a-col :xs="24" :lg="14">
        <a-card :bordered="false" title="我的课程">
          <div v-if="courses.length > 0" class="course-grid">
            <div
              v-for="course in courses"
              :key="course.courseId"
              class="course-card"
              @click="goToCourse(course.courseId)"
            >
              <div class="course-cover">
                <img v-if="course.coverUrl" :src="course.coverUrl" alt="" />
                <ReadOutlined v-else class="cover-icon" />
              </div>
              <div class="course-info">
                <div class="course-name">{{ course.courseName }}</div>
                <a-progress
                  :percent="course.progress"
                  size="small"
                  :stroke-color="getCompletionColor(course.progress)"
                />
                <div class="course-meta">上次学习：{{ formatRelativeDate(course.lastStudyTime ?? '') }}</div>
              </div>
            </div>
          </div>
          <a-empty v-else description="暂无在修课程" :image-style="{ height: '40px' }" />
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="10">
        <a-card :bordered="false" title="薄弱知识点">
          <template v-if="weakPoints.length > 0">
            <a-list :data-source="weakPoints" size="small">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #title>
                      <span class="font-medium">{{ item.nodeName || item.nodeUuid }}</span>
                      <a-tag v-if="item.courseName" color="blue" class="ml-2">{{ item.courseName }}</a-tag>
                    </template>
                    <template #description>
                      学习 {{ formatSeconds(item.totalStudySeconds) }} · 交互 {{ item.totalInteractionCount }} 次
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </template>
          <a-empty v-else description="暂无薄弱知识点" :image-style="{ height: '40px' }" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { LeftOutlined, ReadOutlined, RightOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import useUserStore from '@/stores/modules/user'
import StatCard from '@/components/education/StatCard.vue'
import LearningCalendar from '@/components/education/LearningCalendar.vue'
import LearningTrendChart from '@/components/education/LearningTrendChart.vue'
import MemoPad from '@/components/education/MemoPad.vue'
import { formatMinutes, formatSeconds, formatRelativeDate, getCompletionColor } from '@/utils/format'
import { isHttp } from '@/utils/string.ts'
import {
  getStudentDashboardSummary,
  getStudentDashboardTrend,
  getStudentDashboardCourses,
  getStudentDashboardWeakPoints,
} from '@/api/education/dashboard'
import type {
  DailyActiveMinutesVO,
  DashboardCourseItemVO,
  DashboardWeakPointVO,
  StudentDashboardSummaryVO,
} from '@/types/api/education/stats.ts'

const router = useRouter()
const userStore = useUserStore()

const summary = ref<StudentDashboardSummaryVO>({
  totalStudyDays: 0,
  totalStudyMinutes: 0,
  effectiveStudyMinutes: 0,
  reviewStudyMinutes: 0,
  activeCourseCount: 0,
  consecutiveDays: 0,
})
const trendData = ref<DailyActiveMinutesVO[]>([])
const courses = ref<DashboardCourseItemVO[]>([])
const weakPoints = ref<DashboardWeakPointVO[]>([])
const trendLoading = ref(false)

// ==================== 周导航 ====================

/** 获取某日期所在周的周一 */
function getMonday(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

/** 格式化日期为 YYYY-MM-DD */
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 格式化日期为 MM-DD */
function formatShortDate(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${m}-${d}`
}

const weekStart = ref(getMonday(new Date()))

const weekLabel = computed(() => {
  const start = weekStart.value
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  return `${formatShortDate(start)} - ${formatShortDate(end)}`
})

const isCurrentWeek = computed(() => {
  const currentMonday = getMonday(new Date())
  return formatDate(weekStart.value) === formatDate(currentMonday)
})

function changeWeek(delta: number) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + delta * 7)
  const currentMonday = getMonday(new Date())
  if (d > currentMonday) return
  weekStart.value = d
}

/** 补全一周 7 天数据，缺失的填充为 0 */
function fillWeekData(data: DailyActiveMinutesVO[]): DailyActiveMinutesVO[] {
  const filled: DailyActiveMinutesVO[] = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart.value)
    d.setDate(d.getDate() + i)
    const dateStr = formatShortDate(d)
    const existing = data.find((item) => item.date === dateStr)
    filled.push(existing || { date: dateStr, activeMinutes: 0 })
  }
  return filled
}

// ==================== 课程封面 URL ====================

function resolveMediaUrl(url?: string): string | undefined {
  if (!url) return undefined
  if (isHttp(url)) return url
  // Vite 打包后的静态资源路径（以 /assets/ 或 /src/ 开头），无需拼接 API 前缀
  if (url.startsWith('/assets/') || url.startsWith('/src/')) return url
  return import.meta.env.VITE_API_BASE_URL + url
}

// ==================== 问候语 ====================

// 切换周时重新加载趋势数据
watch(weekStart, () => {
  loadTrendData()
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const todayTip = computed(() => {
  const tips = [
    '坚持学习，每天进步一点点',
    '知识就是力量，加油！',
    '今天也要元气满满地学习哦',
    '复习是学习之母，温故而知新',
  ]
  return tips[Math.floor(Date.now() / 86400000) % tips.length]
})

// ==================== 数据加载 ====================

async function loadTrendData() {
  trendLoading.value = true
  try {
    const start = formatDate(weekStart.value)
    const end = formatDate(new Date(new Date(weekStart.value).setDate(weekStart.value.getDate() + 6)))
    const res = await getStudentDashboardTrend(start, end)
    if (res.code === 200) {
      trendData.value = fillWeekData(res.data || [])
    }
  } catch (e) {
    console.error('加载趋势数据失败:', e)
  } finally {
    trendLoading.value = false
  }
}

async function loadData() {
  try {
    const [summaryRes, coursesRes, weakRes] = await Promise.allSettled([
      getStudentDashboardSummary(),
      getStudentDashboardCourses(6),
      getStudentDashboardWeakPoints(5),
    ])

    if (summaryRes.status === 'fulfilled' && summaryRes.value.code === 200) {
      summary.value = summaryRes.value.data
    }

    if (coursesRes.status === 'fulfilled' && coursesRes.value.code === 200) {
      courses.value = (coursesRes.value.data || []).map((c) => ({
        ...c,
        coverUrl: resolveMediaUrl(c.coverUrl),
      }))
    }

    if (weakRes.status === 'fulfilled' && weakRes.value.code === 200) {
      weakPoints.value = weakRes.value.data || []
    }
  } catch (error: any) {
    console.error('加载仪表盘数据失败:', error)
    message.error(error.message || '加载数据失败')
  }
}

function goToLearning() {
  router.push('/learn/course')
}

function goToCourse(courseId: number) {
  router.push(`/course/learn/${courseId}`)
}

onMounted(() => {
  loadData()
  loadTrendData()
})
</script>

<style scoped>
@reference '#main.css';

.student-dashboard {
  @apply p-6 max-w-7xl mx-auto;
}

/* 欢迎横幅 */
.welcome-banner {
  @apply flex items-center justify-between p-6 rounded-xl;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  color: white;
}

:root[data-role='teacher'] .welcome-banner {
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
}

html.dark .welcome-banner {
  background: linear-gradient(135deg, #0958d9 0%, #2560b8 100%);
}

:root[data-role='teacher'].dark .welcome-banner {
  background: linear-gradient(135deg, #047857 0%, #1c7a4a 100%);
}

.welcome-title {
  @apply text-2xl font-bold m-0;
}

.welcome-sub {
  @apply text-sm opacity-90 mt-2 m-0;
}

.welcome-action {
  @apply shrink-0;
}

/* 周导航标签 */
.week-label {
  display: inline-block;
  min-width: 120px;
  text-align: center;
  font-weight: 500;
  font-size: 13px;
  color: var(--ge-text-secondary);
}

/* 课程网格 */
.course-grid {
  @apply grid grid-cols-1 sm:grid-cols-2 gap-4;
}

.course-card {
  @apply flex gap-3 p-3 rounded-lg border border-gray-100 dark:border-gray-700 cursor-pointer transition-all hover:shadow-md hover:border-primary;
}

.course-cover {
  @apply shrink-0 w-16 h-16 rounded-md bg-gray-50 dark:bg-gray-700 flex items-center justify-center overflow-hidden;
}

.course-cover img {
  @apply w-full h-full object-cover;
}

.cover-icon {
  @apply text-2xl text-gray-300 dark:text-gray-500;
}

.course-info {
  @apply flex-1 min-w-0;
}

.course-name {
  @apply font-medium text-sm text-gray-800 dark:text-gray-100 truncate mb-1;
}

.course-meta {
  @apply text-xs text-gray-400 dark:text-gray-500 mt-1;
}

/* 等高行：让同一行卡片等高，右侧卡片内容溢出滚动 */
.equal-height-row :deep(.ant-col) {
  display: flex;
}

.equal-height-row :deep(.ant-card) {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.equal-height-row :deep(.ant-card-body) {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.equal-height-row :deep(.memo-list) {
  max-height: none;
}
</style>
