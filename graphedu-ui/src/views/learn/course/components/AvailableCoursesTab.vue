<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useIntersectionObserver } from '@vueuse/core'
import {
  ReloadOutlined,
  SearchOutlined,
  BankOutlined,
  UserOutlined,
  EyeOutlined,
  PlusOutlined,
  TeamOutlined,
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
  (e: 'viewDetail', course: CourseListVO): void
  (e: 'manageCourse', course: CourseListVO): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 默认封面图
const defaultCover = 'https://via.placeholder.com/300x180?text=Course'

// 列表数据（全部公开课程，客户端过滤未加入）
const allCourses = ref<CourseListVO[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const hasMore = ref(true)
const initialLoading = ref(true)

// 搜索表单
const searchForm = ref({
  courseName: '',
  faculty: undefined as string | undefined,
})

// 学院列表（从已加载数据提取）
const facultyList = computed(() => {
  const faculties = new Set<string>()
  allCourses.value.forEach((c) => {
    if (c.faculty) faculties.add(c.faculty)
  })
  return Array.from(faculties).sort()
})

// 客户端过滤：只展示未加入的课程
const availableCourses = computed(() => allCourses.value.filter((c) => !props.myCourseIds.has(c.courseId)))

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
        allCourses.value = rows
      } else {
        allCourses.value.push(...rows)
      }
      hasMore.value = allCourses.value.length < res.data.total
      page.value += 1
    }
  } catch (_) {
    // 静默失败
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

const handleSearch = () => loadMore(true)
const handleReset = () => {
  searchForm.value = { courseName: '', faculty: undefined }
  loadMore(true)
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
  <div class="available-courses-tab">
    <!-- 搜索 -->
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

    <!-- 骨架屏（首次加载） -->
    <CourseCardSkeleton v-if="initialLoading" :count="8" />

    <!-- 空状态 -->
    <a-empty
      v-else-if="!loading && availableCourses.length === 0"
      :description="t('learning.availableCourses.empty')"
      class="empty-container"
    >
      <p class="empty-hint">{{ t('learning.availableCourses.emptyHint') }}</p>
      <a-button type="primary" @click="handleReset">{{ t('common.reset') }}</a-button>
    </a-empty>

    <!-- 课程卡片网格 -->
    <div v-else class="course-grid">
      <a-card
        v-for="course in availableCourses"
        :key="course.courseId"
        class="course-card"
        hoverable
        :body-style="{ padding: 0 }"
      >
        <div class="card-body">
          <!-- 封面 -->
          <div class="course-cover" @click="emit('viewDetail', course)">
            <img :src="course.coverUrl || defaultCover" :alt="course.courseName" />
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
          <a-button v-permit="'web:learn:course:join'" type="primary" @click="emit('join', course)">
            <template #icon><PlusOutlined /></template>
            {{ t('common.joinCourse') }}
          </a-button>
          <a-button v-permit="'web:learn:course:manage'" @click="emit('manageCourse', course)">
            <template #icon><SettingOutlined /></template>
            {{ t('education.course.manageCourse', '管理课程') }}
          </a-button>
        </div>
      </a-card>
    </div>

    <!-- 无限滚动哨兵 -->
    <div ref="sentinel" class="sentinel">
      <a-spin v-if="loading && !initialLoading" size="small" />
      <span v-else-if="!hasMore && availableCourses.length > 0" class="no-more">
        {{ t('common.noMoreData', '没有更多了') }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.available-courses-tab {
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

.course-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.meta-item {
  font-size: 12px;
  color: var(--ge-text-secondary);
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
  color: var(--ge-text-secondary);
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

  .course-actions {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 12px;
  }

  .course-actions :deep(.ant-btn) {
    width: auto;
  }

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
