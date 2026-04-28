<template>
  <div class="course-intro-page">
    <a-spin v-if="loading" tip="加载中..." class="spin-center" />

    <template v-else-if="course">
      <!-- 封面 + 基本信息 -->
      <div class="course-header">
        <div class="cover-wrap">
          <img v-if="course.coverUrl" :src="course.coverUrl" class="cover-img" alt="课程封面" />
          <div v-else class="cover-placeholder">
            <ReadOutlined style="font-size: 48px; color: #ccc" />
          </div>
        </div>

        <div class="course-meta">
          <div class="course-title">
            <h2>{{ course.courseName }}</h2>
            <a-space class="course-tags">
              <a-tag color="blue">{{ course.courseCode }}</a-tag>
              <a-tag v-if="course.faculty">{{ course.faculty }}</a-tag>
              <a-tag v-if="course.category" color="cyan">{{ course.category }}</a-tag>
              <a-tag :color="getDifficultyColor(course.difficultyLevel)">{{
                getDifficultyLabel(course.difficultyLevel)
              }}</a-tag>
              <a-tag v-if="typeof course.totalHours === 'number'" color="geekblue">{{ course.totalHours }} 学时</a-tag>
              <a-tag :color="course.isPublic === 'Y' ? 'green' : 'default'">
                {{ course.isPublic === 'Y' ? '公开' : '非公开' }}
              </a-tag>
              <a-tag :color="course.status === '0' ? 'green' : 'orange'">
                {{ course.status === '0' ? '正常' : '已停用' }}
              </a-tag>
            </a-space>
          </div>

          <a-descriptions :column="2" size="small" class="course-stats">
            <a-descriptions-item label="学生人数">{{ course.studentCount }}</a-descriptions-item>
            <a-descriptions-item label="浏览次数">{{ course.viewCount }}</a-descriptions-item>
            <a-descriptions-item label="课程分类">{{ course.category || '-' }}</a-descriptions-item>
            <a-descriptions-item label="难度级别">{{ getDifficultyLabel(course.difficultyLevel) }}</a-descriptions-item>
            <a-descriptions-item label="总学时">{{
              typeof course.totalHours === 'number' ? `${course.totalHours} 小时` : '-'
            }}</a-descriptions-item>
            <a-descriptions-item label="创建时间">{{ parseTime(course.createTime) || '-' }}</a-descriptions-item>
            <a-descriptions-item label="更新时间">{{ parseTime(course.updateTime) || '-' }}</a-descriptions-item>
          </a-descriptions>

          <div v-if="course.teachers && course.teachers.length" class="teachers">
            <span class="label">授课教师：</span>
            <a-space wrap>
              <a-avatar-group>
                <a-tooltip v-for="t in course.teachers" :key="t.userId" :title="t.realName || t.userName">
                  <a-avatar>{{ (t.realName || t.userName || '?')[0] }}</a-avatar>
                </a-tooltip>
              </a-avatar-group>
            </a-space>
          </div>

          <div class="course-actions">
            <a-space>
              <a-button type="primary" @click="goTo('chapter')">
                <template #icon><UnorderedListOutlined /></template>
                章节管理
              </a-button>
              <a-button @click="goTo('resource')">
                <template #icon><FileOutlined /></template>
                资源管理
              </a-button>
              <a-button @click="goTo('knowledge-point')">
                <template #icon><ShareAltOutlined /></template>
                知识点图谱
              </a-button>
              <a-button @click="goTo('semantic-graph')">
                <template #icon><RobotOutlined /></template>
                AI 问答知识图谱
              </a-button>
              <a-button @click="goTo('student')">
                <template #icon><TeamOutlined /></template>
                学生管理
              </a-button>
            </a-space>
          </div>
        </div>
      </div>

      <!-- 课程描述 -->
      <a-card v-if="course.description" title="课程简介" :bordered="false" class="desc-card">
        <p class="description">{{ course.description }}</p>
      </a-card>
      <a-card v-if="course.courseOutline" title="课程大纲" :bordered="false" class="desc-card">
        <p class="description">{{ course.courseOutline }}</p>
      </a-card>
      <a-card v-if="course.targetAudience" title="适用人群" :bordered="false" class="desc-card">
        <p class="description">{{ course.targetAudience }}</p>
      </a-card>
      <a-card v-if="course.learningGoals" title="学习目标" :bordered="false" class="desc-card">
        <p class="description">{{ course.learningGoals }}</p>
      </a-card>
      <a-card v-if="course.tags && course.tags.length" title="课程标签" :bordered="false" class="desc-card">
        <a-space wrap>
          <a-tag v-for="tag in course.tags" :key="tag" color="processing">{{ tag }}</a-tag>
        </a-space>
      </a-card>

      <!-- ====================================================================== -->
      <!-- 教学数据分析 -->
      <!-- ====================================================================== -->
      <a-divider orientation="left" class="mt-6">教学数据分析</a-divider>

      <a-spin :spinning="analyticsLoading">
        <template v-if="analytics">
          <!-- 统计概览卡片 -->
          <a-row :gutter="[16, 16]" class="mt-4">
            <a-col :xs="12" :sm="6">
              <StatCard title="总学生数" :value="analytics.totalStudents" color="blue" icon="UserOutlined" />
            </a-col>
            <a-col :xs="12" :sm="6">
              <StatCard
                title="活跃学生（30天）"
                :value="analytics.activeStudents"
                color="green"
                icon="LineChartOutlined"
              />
            </a-col>
            <a-col :xs="12" :sm="6">
              <StatCard
                title="总学习时长"
                :value="formatMinutes(analytics.totalStudyTime)"
                color="orange"
                icon="ClockCircleOutlined"
              />
            </a-col>
            <a-col :xs="12" :sm="6">
              <StatCard
                title="答题正确率"
                :value="`${analytics.quizCorrectRate}%`"
                color="purple"
                icon="TrophyOutlined"
              />
            </a-col>
          </a-row>

          <!-- 掌握度分布 -->
          <a-row :gutter="[16, 16]" class="mt-4">
            <a-col :xs="24" :sm="12">
              <a-card title="掌握度分布" :bordered="false" size="small">
                <a-row :gutter="8">
                  <a-col :span="6">
                    <a-statistic title="高" :value="analytics.highMasteryCount" :value-style="{ color: '#52c41a' }" />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic title="中" :value="analytics.mediumMasteryCount" :value-style="{ color: '#1890ff' }" />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic title="低" :value="analytics.lowMasteryCount" :value-style="{ color: '#ff4d4f' }" />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic title="平均掌握度" :value="analytics.avgMasteryScore ?? '-'" />
                  </a-col>
                </a-row>
              </a-card>
            </a-col>
            <a-col :xs="24" :sm="12">
              <a-card title="学习互动" :bordered="false" size="small">
                <a-row :gutter="8">
                  <a-col :span="8">
                    <a-statistic title="总事件" :value="analytics.totalEventCount" />
                  </a-col>
                  <a-col :span="8">
                    <a-statistic title="提问次数" :value="analytics.totalQuestionCount" />
                  </a-col>
                  <a-col :span="8">
                    <a-statistic title="答题次数" :value="analytics.totalQuizCount" />
                  </a-col>
                </a-row>
              </a-card>
            </a-col>
          </a-row>

          <!-- 章节完成率 -->
          <a-card
            v-if="analytics.chapterCompletion && analytics.chapterCompletion.length > 0"
            title="章节学习情况"
            :bordered="false"
            class="mt-4"
            size="small"
          >
            <a-table
              :columns="chapterColumns"
              :data-source="analytics.chapterCompletion"
              :pagination="false"
              size="small"
              row-key="chapterId"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'completion'">
                  <a-progress
                    :percent="record.completion"
                    :stroke-color="getCompletionColor(record.completion)"
                    size="small"
                  />
                </template>
              </template>
            </a-table>
          </a-card>

          <!-- 学生排名 -->
          <a-card v-if="rankings.length > 0" title="学生排名（按掌握度）" :bordered="false" class="mt-4" size="small">
            <a-table
              :columns="rankingColumns"
              :data-source="rankings"
              :pagination="{ pageSize: 10, size: 'small' }"
              size="small"
              row-key="studentId"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'masteryPercentile'">
                  <div class="flex items-center gap-2">
                    <a-progress
                      :percent="Math.round(record.masteryPercentile * 100)"
                      :stroke-color="getPercentileColor(record.masteryPercentile)"
                      :show-info="false"
                      size="small"
                      class="flex-1 min-w-0"
                    />
                    <span class="text-xs text-gray-500 shrink-0">
                      Top {{ Math.round((1 - record.masteryPercentile) * 100) }}%
                    </span>
                  </div>
                </template>
                <template v-if="column.key === 'totalStudySeconds'">
                  {{ formatMinutes(Math.round(record.totalStudySeconds / 60)) }}
                </template>
                <template v-if="column.key === 'quizCorrectRate'">
                  {{ record.quizCorrectRate != null ? `${record.quizCorrectRate}%` : '-' }}
                </template>
              </template>
            </a-table>
          </a-card>
        </template>

        <a-empty v-else description="暂无教学数据，学生开始学习后将展示分析数据" />
      </a-spin>
    </template>

    <a-empty v-else description="课程不存在或已删除" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReadOutlined,
  UnorderedListOutlined,
  FileOutlined,
  ShareAltOutlined,
  RobotOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import { getCourseDetail } from '@/api/education/course'
import { parseTime } from '@/utils/common.ts'
import { getCourseAnalytics, getCourseRankings } from '@/api/education/teach_analytics.ts'
import StatCard from '@/components/education/StatCard.vue'
import type { CourseDetailVO } from '@/types/api/education/course.ts'
import type { CourseAnalyticsVO, StudentRankingItemVO } from '@/types/api/education/stats.ts'

const route = useRoute()
const router = useRouter()

const courseId = ref<number>(Number(route.params.courseId) || 0)
const course = ref<CourseDetailVO | null>(null)
const loading = ref(false)

// 教学分析数据
const analytics = ref<CourseAnalyticsVO | null>(null)
const rankings = ref<StudentRankingItemVO[]>([])
const analyticsLoading = ref(false)

// 章节表格列
const chapterColumns = [
  { title: '章节', dataIndex: 'chapter', key: 'chapter' },
  { title: '完成率', key: 'completion', width: 200 },
  { title: '学习人数', dataIndex: 'students', key: 'students', width: 100 },
]

// 学生排名表格列
const rankingColumns = [
  { title: '学生姓名', dataIndex: 'studentName', key: 'studentName', width: 120 },
  { title: '掌握度排名', key: 'masteryPercentile', width: 220 },
  {
    title: '掌握度评分',
    dataIndex: 'avgMasteryScore',
    key: 'avgMasteryScore',
    width: 110,
  },
  { title: '答题正确率', key: 'quizCorrectRate', width: 110 },
  { title: '学习时长', key: 'totalStudySeconds', width: 100 },
  { title: '学习天数', dataIndex: 'studyDays', key: 'studyDays', width: 90 },
  {
    title: '知识点覆盖',
    dataIndex: 'nodeCoverageRate',
    key: 'nodeCoverageRate',
    width: 100,
  },
]

const difficultyLabelMap: Record<string, string> = {
  '1': '初级',
  '2': '中级',
  '3': '高级',
}

const difficultyColorMap: Record<string, string> = {
  '1': 'green',
  '2': 'orange',
  '3': 'red',
}

const getDifficultyLabel = (difficulty?: string) => {
  if (!difficulty) return '未设置'
  return difficultyLabelMap[difficulty] || '未设置'
}

const getDifficultyColor = (difficulty?: string) => {
  if (!difficulty) return 'default'
  return difficultyColorMap[difficulty] || 'default'
}

// 格式化分钟
function formatMinutes(minutes: number): string {
  if (!minutes || minutes === 0) return '0分钟'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h${mins}m` : `${hours}h`
}

// 完成率颜色
function getCompletionColor(percent: number): string {
  if (percent >= 80) return '#52c41a'
  if (percent >= 50) return '#faad14'
  return '#ff4d4f'
}

// 百分位颜色
function getPercentileColor(p: number): string {
  if (p >= 0.8) return '#52c41a'
  if (p >= 0.5) return '#1890ff'
  return '#ff4d4f'
}

const loadCourse = async () => {
  if (!courseId.value) return
  loading.value = true
  try {
    const res = await getCourseDetail(courseId.value)
    if (res.code === 200) {
      course.value = res.data
    }
  } catch (_e) {
    message.error('加载课程信息失败')
  } finally {
    loading.value = false
  }
}

const loadAnalytics = async () => {
  if (!courseId.value) return
  analyticsLoading.value = true
  try {
    const [analyticsRes, rankingsRes] = await Promise.allSettled([
      getCourseAnalytics(courseId.value),
      getCourseRankings(courseId.value),
    ])

    if (analyticsRes.status === 'fulfilled' && analyticsRes.value.code === 200) {
      analytics.value = analyticsRes.value.data
    }
    if (rankingsRes.status === 'fulfilled' && rankingsRes.value.code === 200) {
      rankings.value = rankingsRes.value.data || []
    }
  } catch (_e) {
    // 分析数据加载失败不影响页面
  } finally {
    analyticsLoading.value = false
  }
}

const goTo = (section: string) => {
  router.push(`/course/manage/${courseId.value}/${section}`)
}

onMounted(() => {
  if (!courseId.value) {
    message.error('缺少课程ID参数')
    router.back()
    return
  }
  loadCourse()
  loadAnalytics()
})
</script>

<style scoped>
.course-intro-page {
  padding: 24px;
}

.spin-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  width: 100%;
}

.course-header {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  background: var(--ge-bg-container);
  padding: 24px;
  border-radius: 8px;
}

.cover-wrap {
  flex-shrink: 0;
}

.cover-img {
  width: 200px;
  height: 140px;
  object-fit: cover;
  border-radius: 6px;
}

.cover-placeholder {
  width: 200px;
  height: 140px;
  background: var(--ge-bg-elevated);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.course-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.course-title h2 {
  margin: 0 0 8px;
  font-size: 22px;
  color: var(--ge-text-primary);
}

.course-tags {
  flex-wrap: wrap;
}

.label {
  color: var(--ge-text-secondary);
  margin-right: 8px;
}

.desc-card {
  border-radius: 8px;
}

.description {
  white-space: pre-wrap;
  line-height: 1.8;
  color: var(--ge-text-primary);
}
</style>
