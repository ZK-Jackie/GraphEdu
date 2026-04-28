<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useIntersectionObserver } from '@vueuse/core'
import {
  ReloadOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  BankOutlined,
  TeamOutlined,
  UserOutlined,
  EyeOutlined,
  PlusOutlined,
  PlayCircleOutlined,
  MinusOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { getCourseList } from '@/api/education/course'
import CourseCardSkeleton from './CourseCardSkeleton.vue'
import type { CourseListVO, CourseQueryDTO } from '@/types/api/education/course.ts'

const { t } = useI18n()

interface Props {
  myCourseIds: Set<number>
}

interface Emits {
  (e: 'join', course: CourseListVO): void
  (e: 'leave', course: CourseListVO): void
  (e: 'viewDetail', course: CourseListVO): void
  (e: 'continueLearning', course: CourseListVO): void
  (e: 'manageCourse', course: CourseListVO): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 默认封面
const defaultCover = 'https://via.placeholder.com/300x180?text=Course'

// 列表数据
const courseList = ref<CourseListVO[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const hasMore = ref(true)
const initialLoading = ref(true)

// 学院列表（从已加载数据提取）
const facultyList = computed(() => {
  const faculties = new Set<string>()
  courseList.value.forEach((c) => {
    if (c.faculty) faculties.add(c.faculty)
  })
  return Array.from(faculties).sort()
})

// 搜索表单（自持）
const searchForm = ref({
  courseName: '',
  faculty: undefined as string | undefined,
})

// 无限滚动哨兵
const sentinel = ref<HTMLElement | null>(null)

// 加载一页数
const loadMore = async (reset = false) => {
  if (loading.value || (!hasMore.value && !reset)) return
  loading.value = true

  if (reset) {
    page.value = 1
    hasMore.value = true
  }

  const query: CourseQueryDTO = {
    page: page.value,
    size: pageSize,
    isPublic: 'Y',
    status: '0',
    courseName: searchForm.value.courseName || undefined,
    faculty: searchForm.value.faculty,
  }

  try {
    const res = await getCourseList(query)
    if (res.code === 200) {
      const rows = res.data.rows || []
      if (reset) {
        courseList.value = rows
      } else {
        courseList.value.push(...rows)
      }
      hasMore.value = courseList.value.length < res.data.total
      page.value += 1
    }
  } catch (_) {
    // 静默失败
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

// 搜索
const handleSearch = () => loadMore(true)
const handleReset = () => {
  searchForm.value = { courseName: '', faculty: undefined }
  loadMore(true)
}

// 判断是否已加
const isJoined = (courseId: number) => props.myCourseIds.has(courseId)

// IntersectionObserver：哨兵进入视口时加载下一
useIntersectionObserver(sentinel, ([entry]) => {
  if (entry?.isIntersecting && hasMore.value && !loading.value) {
    loadMore()
  }
})

onMounted(async () => {
  await nextTick()
  loadMore(true)
})

defineExpose({ loadMore })
</script>

<template>
  <div class="all-courses-tab">
    <!-- 搜索和筛�?-->
    <a-card class="search-card" :bordered="false">
      <a-form layout="inline">
        <a-form-item :label="t('education.course.courseName')">
          <a-input
            v-model:value="searchForm.courseName"
            :placeholder="t('education.course.searchCourse')"
            allow-clear
            style="width: 200px"
            @press-enter="handleSearch"
          />
        </a-form-item>
        <a-form-item :label="t('common.faculty')">
          <a-select
            v-model:value="searchForm.faculty"
            :placeholder="t('education.course.filterByFaculty')"
            allow-clear
            style="width: 150px"
          >
            <a-select-option v-for="faculty in facultyList" :key="faculty" :value="faculty">
              {{ faculty }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              {{ t('common.search') }}
            </a-button>
            <a-button @click="handleReset">
              <template #icon><ReloadOutlined /></template>
              {{ t('common.reset') }}
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 骨架屏（首次加载时） -->
    <CourseCardSkeleton v-if="initialLoading" :count="8" />

    <!-- 空状�?-->
    <a-empty
      v-else-if="!loading && courseList.length === 0"
      :description="t('education.course.noCoursesFound')"
      class="empty-container"
    >
      <p class="empty-hint">{{ t('education.course.noCoursesHint') }}</p>
      <a-button type="primary" @click="handleReset">{{ t('common.reset') }}</a-button>
    </a-empty>

    <!-- 课程卡片网格 -->
    <div v-else class="course-grid">
      <a-card
        v-for="course in courseList"
        :key="course.courseId"
        class="course-card"
        hoverable
        :body-style="{ padding: 0 }"
      >
        <div class="card-body">
          <!-- 封面 -->
          <div class="course-cover" @click="emit('viewDetail', course)">
            <img :src="course.coverUrl || defaultCover" :alt="course.courseName" />
            <div v-if="isJoined(course.courseId)" class="joined-badge">
              <CheckCircleOutlined />
              {{ t('education.course.alreadyJoined') }}
            </div>
          </div>

          <!-- 信息 -->
          <div class="course-info">
            <h3 class="course-name" :title="course.courseName">
              {{ course.courseName }}
            </h3>
            <p class="course-code">{{ course.courseCode }}</p>
            <div class="course-meta">
              <span v-if="course.faculty" class="meta-item"> <BankOutlined /> {{ course.faculty }} </span>
              <span v-if="course.teacherName" class="meta-item"> <UserOutlined /> {{ course.teacherName }} </span>
            </div>
            <div class="course-stats">
              <span class="stat-item">
                <TeamOutlined /> {{ course.studentCount || 0 }}
                {{ t('education.course.students') }}
              </span>
              <span class="stat-item">
                <EyeOutlined /> {{ course.viewCount || 0 }}
                {{ t('education.course.views') }}
              </span>
            </div>
          </div>
        </div>

        <!-- 操作 -->
        <div class="course-actions">
          <a-button
            v-if="!isJoined(course.courseId)"
            v-permit="'web:learn:course:join'"
            type="primary"
            @click="emit('join', course)"
          >
            <template #icon><PlusOutlined /></template>
            {{ t('common.joinCourse') }}
          </a-button>
          <template v-else>
            <a-button v-permit="'web:learn:course:learn'" type="primary" @click="emit('continueLearning', course)">
              <template #icon><PlayCircleOutlined /></template>
              {{ t('common.continueLearning') }}
            </a-button>
            <a-button @click="emit('viewDetail', course)">
              <template #icon><EyeOutlined /></template>
              {{ t('education.course.viewDetail') }}
            </a-button>
            <a-button v-permit="'web:learn:course:leave'" danger ghost @click="emit('leave', course)">
              <template #icon><MinusOutlined /></template>
              {{ t('education.course.leaveCourse') }}
            </a-button>
            <a-button v-permit="'web:learn:course:manage'" @click="emit('manageCourse', course)">
              <template #icon><SettingOutlined /></template>
              {{ t('education.course.manageCourse', '管理课程') }}
            </a-button>
          </template>
        </div>
      </a-card>
    </div>

    <!-- 无限滚动哨兵 -->
    <div ref="sentinel" class="sentinel">
      <a-spin v-if="loading && !initialLoading" size="small" />
      <span v-else-if="!hasMore && courseList.length > 0" class="no-more">
        {{ t('common.noMoreData', '没有更多') }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.all-courses-tab {
  width: 100%;
}

.search-card {
  margin-bottom: 24px;
  border-radius: 8px;
}

.empty-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-hint {
  color: #8c8c8c;
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

/* 卡片内容体 */
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
  color: #262626;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-code {
  font-size: 12px;
  color: #8c8c8c;
  margin: 0 0 12px 0;
}

.course-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.meta-item {
  font-size: 12px;
  color: #595959;
  display: flex;
  align-items: center;
  gap: 4px;
}

.course-stats {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.stat-item {
  font-size: 12px;
  color: #8c8c8c;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 操作按钮：桌面端纵向排列、按钮撑满宽度 */
.course-actions {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
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
  color: #bfbfbf;
}

/* ============ 移动端 ============ */
@media (max-width: 768px) {
  .course-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  /* 上半部分：左图右文 */
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

  .course-meta {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 6px;
  }

  /* 下半部分：按钮横向排布 */
  .course-actions {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 12px;
  }

  .course-actions :deep(.ant-btn) {
    width: auto;
  }

  /* 搜索栏响应式 */
  .search-card :deep(.ant-form) {
    flex-direction: column;
  }

  .search-card :deep(.ant-form-item) {
    width: 100%;
    margin-right: 0;
  }

  .search-card :deep(.ant-input),
  .search-card :deep(.ant-select) {
    width: 100% !important;
  }
}
</style>
