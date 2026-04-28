<template>
  <div class="course-overview-page">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 课程基本信息 -->
      <div v-if="overview" class="page-header">
        <h1 class="page-title">{{ courseName || '课程概览' }}</h1>
        <p class="page-subtitle">课程ID: {{ courseId }}</p>
        <div v-if="canManage" class="page-header-actions">
          <a-button type="primary" @click="router.push(`/course/manage/${courseId}`)">
            <template #icon><SettingOutlined /></template>
            管理课程
          </a-button>
        </div>
      </div>

      <div v-if="overview" class="overview-content">
        <!-- 未学习引导提示 -->
        <a-alert v-if="!overview.lastStudyTime" type="info" show-icon class="start-learning-banner">
          <template #message>
            <div class="banner-content">
              <span>开始学习课程内容后，这里将显示您的学习进度和统计数据。</span>
              <a-button type="primary" size="small" @click="startLearning">开始学习</a-button>
            </div>
          </template>
        </a-alert>

        <!-- 基础统计卡片 -->
        <a-row :gutter="[16, 16]" class="stats-grid">
          <a-col :xs="24" :sm="12" :lg="6">
            <StatCard title="学习进度" :value="`${overview.progress || 0}%`" color="blue" icon="BarChartOutlined" />
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <StatCard
              title="已完成章节"
              :value="`${overview.completedChapters || 0}/${overview.totalChapters || 0}`"
              color="green"
              icon="BookOutlined"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <StatCard
              title="学习时长"
              :value="formatDuration(overview.totalStudyTime || 0)"
              color="orange"
              icon="ClockCircleOutlined"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <StatCard
              title="连续学习"
              :value="`${overview.consecutiveDays || 0}天`"
              color="purple"
              icon="FireOutlined"
            />
          </a-col>
        </a-row>

        <!-- 章节学习进度 -->
        <a-card title="章节学习进度" :bordered="false" class="mt-4">
          <a-spin :spinning="chapterLoading">
            <a-empty v-if="chapterProgress.length === 0" description="暂无章节数据" />
            <a-collapse v-else v-model:activeKey="expandedChapters" :bordered="false" class="chapter-collapse">
              <a-collapse-panel
                v-for="chapter in chapterProgress"
                :key="String(chapter.chapterId)"
                :header-style="{ padding: '12px 16px' }"
              >
                <template #header>
                  <div class="chapter-header">
                    <div class="chapter-info">
                      <span class="chapter-no">第{{ chapter.chapterNo }}章</span>
                      <span class="chapter-name">{{ chapter.chapterName }}</span>
                      <a-tag v-if="chapter.isCompleted === 'Y'" color="success" class="ml-2">已完成</a-tag>
                    </div>
                    <div class="chapter-progress-info">
                      <span class="resource-count">
                        {{ chapter.completedResourceCount }}/{{ chapter.resourceCount }} 资源
                      </span>
                      <a-progress
                        :percent="chapter.completionRate"
                        :size="'small'"
                        :stroke-width="8"
                        :style="{ width: '120px', marginLeft: '12px' }"
                      />
                    </div>
                  </div>
                </template>
                <!-- 展开内容：资源阅读进度 -->
                <a-empty v-if="chapter.resources.length === 0" description="该章节暂无资源" />
                <div v-else class="resource-list">
                  <div v-for="resource in chapter.resources" :key="resource.resourceId" class="resource-item">
                    <div class="resource-info">
                      <span class="resource-type-tag">
                        <component :is="getResourceIcon(resource.resourceType)" />
                        {{ getResourceTypeName(resource.resourceType) }}
                      </span>
                      <span class="resource-name">{{ resource.resourceName }}</span>
                      <a-tag v-if="resource.isCompleted === 'Y'" color="success" size="small"> 已完成 </a-tag>
                    </div>
                    <div class="resource-progress">
                      <span class="resource-stat">
                        {{ resource.viewCount }}次 · {{ formatSeconds(resource.totalDuration) }}
                      </span>
                      <a-progress
                        :percent="resource.completionRate"
                        :size="'small'"
                        :stroke-width="4"
                        :style="{ width: '100px' }"
                      />
                    </div>
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </a-spin>
        </a-card>

        <!-- 排名 + 课程整体数据 -->
        <a-row :gutter="[16, 16]" class="mt-4">
          <a-col :xs="24" :sm="12">
            <a-card title="我的排名" :bordered="false">
              <div class="rank-display">
                <span class="rank-value">{{ overview.rankPercentile || '-' }}</span>
                <span class="rank-label">掌握度排名</span>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-card v-if="overview.courseStats" title="课程整体数据" :bordered="false">
              <a-row :gutter="[16, 16]">
                <a-col :span="8">
                  <div class="stat-item">
                    <div class="stat-item-label">总学生数</div>
                    <div class="stat-item-value">
                      {{ overview.courseStats.totalStudents ?? '-' }}
                    </div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="stat-item">
                    <div class="stat-item-label">平均进度</div>
                    <div class="stat-item-value">{{ overview.courseStats.averageProgress ?? '-' }}%</div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="stat-item">
                    <div class="stat-item-label">今日活跃</div>
                    <div class="stat-item-value">
                      {{ overview.courseStats.todayActive ?? '-' }}
                    </div>
                  </div>
                </a-col>
              </a-row>
            </a-card>
          </a-col>
        </a-row>

        <!-- 学习趋势图表（带周导航） -->
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

        <!-- 知识点掌握度画像 -->
        <a-card v-if="knowledgeProfile.length > 0" title="知识点掌握度" :bordered="false" class="mt-4">
          <a-table
            :columns="profileColumns"
            :data-source="knowledgeProfile"
            :pagination="{ pageSize: 10, size: 'small' }"
            size="small"
            row-key="nodeUuid"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'nodeName'">
                <a-tooltip v-if="record.nodeName" :title="record.nodeUuid">
                  <span>{{ record.nodeName }}</span>
                </a-tooltip>
                <span v-else class="text-gray-400">{{ record.nodeUuid }}</span>
              </template>
              <template v-if="column.key === 'masteryLevel'">
                <a-tag :color="getMasteryColor(record.latestMasteryLevel)">
                  {{ getMasteryLabel(record.latestMasteryLevel) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'masteryScore'">
                <span>
                  {{ record.latestMasteryScore != null ? record.latestMasteryScore.toFixed(1) : '-' }}
                </span>
              </template>
              <template v-if="column.key === 'studySeconds'">
                <span>{{ formatSeconds(record.totalStudySeconds) }}</span>
              </template>
            </template>
          </a-table>
        </a-card>

        <!-- 薄弱知识点提醒 -->
        <a-card v-if="weakPoints.length > 0" title="薄弱知识点提醒" :bordered="false" class="mt-4">
          <a-alert type="warning" :show-icon="true" class="mb-3">
            <template #message> 以下知识点您投入了较多精力但掌握度较低，建议重点复习 </template>
          </a-alert>
          <a-list :data-source="weakPoints" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span class="font-medium">{{ item.nodeName || item.nodeUuid }}</span>
                    <a-tag :color="getMasteryColor(item.latestMasteryLevel)" class="ml-2">
                      {{ getMasteryLabel(item.latestMasteryLevel) }}
                    </a-tag>
                  </template>
                  <template #description>
                    <span>
                      交互 {{ item.totalInteractionCount }} 次 · 提问 {{ item.totalQuestionCount }} 次 · 学习
                      {{ formatSeconds(item.totalStudySeconds) }}
                    </span>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <!-- 最后学习时间 -->
        <a-card v-if="overview.lastStudyTime" title="最近学习" :bordered="false" class="mt-4">
          <p class="text-gray-600">
            上次学习时间：<span class="font-medium">{{ formatDateStr(overview.lastStudyTime) }}</span>
          </p>
          <a-button type="primary" @click="continueLearning">继续学习</a-button>
        </a-card>
      </div>

      <!-- 空状态 -->
      <a-empty v-else-if="!loading" description="暂无课程数据">
        <a-button type="primary" @click="loadData">重新加载</a-button>
      </a-empty>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { LeftOutlined, RightOutlined, VideoCameraOutlined, FileTextOutlined, ReadOutlined } from '@ant-design/icons-vue'
import { SettingOutlined } from '@ant-design/icons-vue'
import useUserStore from '@/stores/modules/user'
import StatCard from '@/components/education/StatCard.vue'
import LearningTrendChart from '@/components/education/LearningTrendChart.vue'
import {
  getStudentCourseOverview,
  getKnowledgeProfile,
  getWeakPoints,
  getMyChapterProgress,
} from '@/api/education/student_course'
import { getCourseDetail } from '@/api/education/course'
import type {
  DailyActiveMinutesVO,
  StudentChapterProgressVO,
  StudentCourseOverviewVO,
  StudentKnowledgeProfileVO,
  StudentWeakPointVO,
} from '@/types/api/education/stats.ts'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const courseId = ref<number>(Number(route.params.courseId))
const courseName = ref<string>('')
const overview = ref<StudentCourseOverviewVO | null>(null)

// 教师/管理员可管理课程
const canManage = computed(() => userStore.isTeacher || userStore.isAdmin)
const knowledgeProfile = ref<StudentKnowledgeProfileVO[]>([])
const weakPoints = ref<StudentWeakPointVO[]>([])
const loading = ref(false)

// 章节进度
const chapterProgress = ref<StudentChapterProgressVO[]>([])
const chapterLoading = ref(false)
const expandedChapters = ref<string[]>([])

// ==================== 周导航 ====================

const trendData = ref<DailyActiveMinutesVO[]>([])
const trendLoading = ref(false)

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

// 知识点画像表格列
const profileColumns = [
  {
    title: '知识点',
    dataIndex: 'nodeName',
    key: 'nodeName',
    ellipsis: true,
  },
  { title: '掌握等级', key: 'masteryLevel', width: 100 },
  { title: '掌握度评分', key: 'masteryScore', width: 110 },
  {
    title: '交互次数',
    dataIndex: 'totalInteractionCount',
    key: 'interactionCount',
    width: 90,
  },
  {
    title: '提问次数',
    dataIndex: 'totalQuestionCount',
    key: 'questionCount',
    width: 90,
  },
  { title: '学习时长', key: 'studySeconds', width: 100 },
]

// 资源类型图标
function getResourceIcon(type: string) {
  switch (type) {
    case 'video':
      return VideoCameraOutlined
    case 'document':
      return FileTextOutlined
    default:
      return ReadOutlined
  }
}

function getResourceTypeName(type: string) {
  switch (type) {
    case 'video':
      return '视频'
    case 'document':
      return '文档'
    case 'text':
      return '文本'
    default:
      return '资料'
  }
}

// 格式化时长（分钟 -> 小时:分钟）
function formatDuration(minutes: number): string {
  if (minutes === 0) return '0分钟'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

// 格式化秒数
function formatSeconds(seconds: number): string {
  if (!seconds || seconds === 0) return '0分钟'
  return formatDuration(Math.round(seconds / 60))
}

// 格式化日期字符串
function formatDateStr(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// 掌握等级颜色
function getMasteryColor(level: string): string {
  switch (level) {
    case 'high':
      return 'green'
    case 'medium':
      return 'blue'
    case 'low':
      return 'red'
    default:
      return 'default'
  }
}

// 掌握等级标签
function getMasteryLabel(level: string): string {
  switch (level) {
    case 'high':
      return '高'
    case 'medium':
      return '中'
    case 'low':
      return '低'
    default:
      return '未知'
  }
}

// 切换周时重新加载趋势数据
watch(weekStart, () => {
  loadTrendData()
})

async function loadTrendData() {
  if (!courseId.value) return
  trendLoading.value = true
  try {
    const start = formatDate(weekStart.value)
    const res = await getStudentCourseOverview(courseId.value, { weekStart: start })
    if (res.code === 200 && res.data) {
      trendData.value = fillWeekData(res.data.dailyActive || [])
    }
  } catch (_e) {
    console.error('加载趋势数据失败:', _e)
  } finally {
    trendLoading.value = false
  }
}

// 加载章节进度
async function loadChapterProgress() {
  if (!courseId.value) return
  chapterLoading.value = true
  try {
    const res = await getMyChapterProgress(courseId.value)
    if (res.code === 200) {
      chapterProgress.value = res.data || []
    }
  } catch (_e) {
    // 静默处理
  } finally {
    chapterLoading.value = false
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const [overviewRes, profileRes, weakRes, courseRes] = await Promise.allSettled([
      getStudentCourseOverview(courseId.value),
      getKnowledgeProfile(courseId.value),
      getWeakPoints(courseId.value),
      getCourseDetail(courseId.value),
    ])

    if (overviewRes.status === 'fulfilled' && overviewRes.value.code === 200) {
      overview.value = overviewRes.value.data
    } else if (overviewRes.status === 'fulfilled') {
      message.error(overviewRes.value.msg || '加载概览失败')
    }

    if (profileRes.status === 'fulfilled' && profileRes.value.code === 200) {
      knowledgeProfile.value = profileRes.value.data || []
    }

    if (weakRes.status === 'fulfilled' && weakRes.value.code === 200) {
      weakPoints.value = weakRes.value.data || []
    }

    if (courseRes.status === 'fulfilled' && courseRes.value.code === 200) {
      courseName.value = courseRes.value.data?.courseName || ''
    }

    // 并行加载章节进度
    loadChapterProgress()
  } catch (error: any) {
    console.error('加载课程概览失败:', error)
    message.error(error.message || '加载失败，请重试')
  } finally {
    loading.value = false
  }
}

// 开始学习
function startLearning() {
  router.push(`/course/learn/${courseId.value}`)
}

// 继续学习
function continueLearning() {
  router.push(`/course/learn/${courseId.value}`)
}

onMounted(() => {
  if (!courseId.value || isNaN(courseId.value)) {
    message.error('课程ID无效')
    return
  }
  loadData()
  loadTrendData()
})
</script>

<style scoped>
@reference '#main.css';

.course-overview-page {
  @apply p-6;
}

.page-header {
  @apply mb-6;
}

.page-title {
  @apply text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2;
}

.page-subtitle {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.page-header-actions {
  @apply mt-3;
}

.overview-content {
  @apply flex flex-col gap-4;
}

.stats-grid {
  @apply mb-4;
}

.stat-item {
  @apply flex flex-col gap-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg;
}

.stat-item-label {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.stat-item-value {
  @apply text-2xl font-bold text-gray-800 dark:text-gray-100;
}

.rank-display {
  @apply flex flex-col items-center justify-center py-4;
}

.rank-value {
  @apply text-4xl font-bold text-purple-600 dark:text-purple-400;
}

.rank-label {
  @apply text-sm text-gray-500 dark:text-gray-400 mt-2;
}

.start-learning-banner {
  @apply mb-4;
}

.banner-content {
  @apply flex items-center justify-between gap-4;
}

/* 章节进度 */
.chapter-collapse {
  @apply bg-transparent;
}

.chapter-header {
  @apply flex items-center justify-between w-full;
}

.chapter-info {
  @apply flex items-center gap-2;
}

.chapter-no {
  @apply text-xs text-gray-400 dark:text-gray-500 font-mono;
}

.chapter-name {
  @apply font-medium;
}

.chapter-progress-info {
  @apply flex items-center;
}

.resource-count {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.resource-list {
  @apply flex flex-col gap-2 pl-4;
}

.resource-item {
  @apply flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded;
}

.resource-info {
  @apply flex items-center gap-2 flex-1 min-w-0;
}

.resource-type-tag {
  @apply text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1 shrink-0;
}

.resource-name {
  @apply text-sm truncate;
}

.resource-progress {
  @apply flex items-center gap-2 shrink-0;
}

.resource-stat {
  @apply text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap;
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
</style>
