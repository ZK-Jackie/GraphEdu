<script setup lang="ts">
import { watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ShareAltOutlined, RobotOutlined, BarChartOutlined, BookOutlined } from '@ant-design/icons-vue'
import useUserStore from '@/stores/modules/user'
import StudentDashboard from '@/views/home/StudentDashboard.vue'
import TeacherDashboard from '@/views/home/TeacherDashboard.vue'
import DashboardQuickNav from '@/components/education/DashboardQuickNav.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// ─── URL param 同步角色 ──────────────────────────────────────────────────────

/**
 * 从 URL param ?role=student|teacher 读取角色并同步到 store
 * 默认不传时走 store 的 activeRole（默认 student）
 */
watch(
  () => route.query.role as string | undefined,
  (roleParam) => {
    if (!userStore.token) return
    if (roleParam === 'student' || roleParam === 'teacher' || roleParam === 'admin') {
      userStore.setActiveRole(roleParam)
    }
  },
  { immediate: true }
)

// 纯管理员（非学生非教师）不重定向，在首页显示空状态
const showAdminEmpty = computed(() => {
  return !!userStore.token && !userStore.isStudent && !userStore.isTeacher
})

/** 当前是否展示学生仪表盘 */
const showStudentDashboard = computed(() => {
  return !!userStore.token && userStore.activeRole === 'student'
})

/** 当前是否展示教师仪表盘 */
const showTeacherDashboard = computed(() => {
  return !!userStore.token && userStore.activeRole === 'teacher'
})

// 功能列表
const features = [
  {
    icon: ShareAltOutlined,
    title: '知识图谱可视化',
    description: '基于课程体系构建知识图谱，直观展示知识点之间的关联关系，帮助学生建立系统化的知识结构',
  },
  {
    icon: RobotOutlined,
    title: 'AI 智能辅导',
    description: '基于 LangGraph 构建的智能辅导系统，支持个性化答疑、知识点讲解和学习路径推荐',
  },
  {
    icon: BarChartOutlined,
    title: '学习数据分析',
    description: '记录学习行为数据，生成学习日历、趋势图表和薄弱知识点分析，让学习情况一目了然',
  },
  {
    icon: BookOutlined,
    title: '多角色课程管理',
    description: '支持学生、教师、管理员多角色协同，提供完整的课程创建、学习、管理功能',
  },
]

// 技术栈标签
const techStack = ['Vue 3', 'TypeScript', 'FastAPI', 'PostgreSQL', 'Neo4j', 'LangGraph', 'Redis']

const handleGetStarted = () => {
  router.push('/register')
}

const handleLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="home-root">
    <!-- 已登录：按激活角色显示个性化仪表盘 -->
    <template v-if="showStudentDashboard || showTeacherDashboard">
      <DashboardQuickNav />
      <StudentDashboard v-if="showStudentDashboard" />
      <TeacherDashboard v-else-if="showTeacherDashboard" />
    </template>

    <!-- 纯管理员（非学生非教师）：显示空状态 -->
    <div v-else-if="showAdminEmpty" class="admin-empty">
      <DashboardQuickNav />
      <a-result status="info" title="管理后台" sub-title="请在左侧菜单中选择管理功能，或点击上方「管理后台」进入">
      </a-result>
    </div>

    <!-- 未登录：项目介绍页 -->
    <div v-else class="landing-page">
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">智图学堂</h1>
          <p class="hero-subtitle">基于知识图谱的智能学习平台</p>
          <p class="hero-desc">
            利用知识图谱技术构建课程知识体系，结合 AI 提供个性化学习路径推荐与智能答疑，让学习更有针对性。
          </p>
          <div class="hero-actions">
            <a-button type="primary" size="large" @click="handleGetStarted">开始使用</a-button>
            <a-button size="large" @click="handleLogin">登录</a-button>
          </div>
        </div>

        <!-- 知识图谱插图 -->
        <div class="hero-illustration">
          <svg viewBox="0 0 400 320" xmlns="http://www.w3.org/2000/svg" class="kg-svg">
            <!-- 连线 -->
            <line x1="200" y1="80" x2="100" y2="160" class="kg-edge" />
            <line x1="200" y1="80" x2="300" y2="160" class="kg-edge" />
            <line x1="100" y1="160" x2="60" y2="260" class="kg-edge" />
            <line x1="100" y1="160" x2="160" y2="260" class="kg-edge" />
            <line x1="300" y1="160" x2="260" y2="260" class="kg-edge" />
            <line x1="300" y1="160" x2="360" y2="260" class="kg-edge" />
            <line x1="200" y1="80" x2="200" y2="180" class="kg-edge" />
            <line x1="200" y1="180" x2="160" y2="260" class="kg-edge" />
            <line x1="200" y1="180" x2="260" y2="260" class="kg-edge" />
            <line x1="100" y1="160" x2="300" y2="160" class="kg-edge" />
            <!-- 中心节点 -->
            <circle cx="200" cy="80" r="28" class="kg-node kg-node--primary" />
            <text x="200" y="85" text-anchor="middle" class="kg-text">课程</text>
            <!-- 二级节点 -->
            <circle cx="100" cy="160" r="22" class="kg-node" />
            <text x="100" y="165" text-anchor="middle" class="kg-text">章节</text>
            <circle cx="300" cy="160" r="22" class="kg-node" />
            <text x="300" y="165" text-anchor="middle" class="kg-text">章节</text>
            <circle cx="200" cy="180" r="20" class="kg-node" />
            <text x="200" y="185" text-anchor="middle" class="kg-text">AI</text>
            <!-- 三级节点 -->
            <circle cx="60" cy="260" r="16" class="kg-node kg-node--leaf" />
            <circle cx="160" cy="260" r="16" class="kg-node kg-node--leaf" />
            <circle cx="260" cy="260" r="16" class="kg-node kg-node--leaf" />
            <circle cx="360" cy="260" r="16" class="kg-node kg-node--leaf" />
          </svg>
        </div>
      </section>

      <!-- 功能展示 Section -->
      <section class="features-section">
        <h2 class="section-title">平台功能</h2>
        <div class="features-grid">
          <div v-for="(feature, index) in features" :key="index" class="feature-card">
            <div class="feature-icon">
              <component :is="feature.icon" />
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.description }}</p>
          </div>
        </div>
      </section>

      <!-- 技术栈 Section -->
      <section class="tech-section">
        <h2 class="section-title">技术架构</h2>
        <div class="tech-tags">
          <span v-for="tech in techStack" :key="tech" class="tech-tag">{{ tech }}</span>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.admin-empty {
  @apply p-6 max-w-7xl mx-auto;
}

/* ── Landing Page ────────────────────────────────────────────── */

.landing-page {
  min-height: 100vh;
  background: var(--ge-bg-container);
}

/* ── Hero Section ────────────────────────────────────────────── */

.hero-section {
  @apply flex items-center justify-center;
  gap: 60px;
  min-height: 520px;
  padding: 80px 10% 60px;
  background: var(--ge-bg-container);
}

.hero-content {
  @apply flex flex-col;
  max-width: 520px;
}

.hero-title {
  @apply font-bold m-0;
  font-size: 42px;
  line-height: 1.3;
  color: var(--ge-text-primary);
}

.hero-subtitle {
  @apply font-medium m-0 mt-3;
  font-size: 20px;
  color: var(--ge-text-secondary);
}

.hero-desc {
  @apply mt-4 mb-8;
  font-size: 15px;
  line-height: 1.8;
  color: var(--ge-text-secondary);
}

.hero-actions {
  @apply flex gap-3 flex-wrap;
}

/* ── Knowledge Graph SVG ─────────────────────────────────────── */

.hero-illustration {
  @apply flex items-center justify-center;
  flex-shrink: 0;
}

.kg-svg {
  width: 360px;
  height: 280px;
}

.kg-edge {
  stroke: var(--ge-primary);
  stroke-opacity: 0.3;
  stroke-width: 2;
}

.kg-node {
  fill: var(--ge-primary-light);
  stroke: var(--ge-primary);
  stroke-width: 2;
}

.kg-node--primary {
  fill: var(--ge-primary-1);
  stroke: var(--ge-primary);
  stroke-width: 2.5;
}

.kg-node--leaf {
  fill: var(--ge-bg-elevated);
  stroke: var(--ge-primary);
  stroke-opacity: 0.6;
  stroke-width: 1.5;
}

.kg-text {
  fill: var(--ge-text-primary);
  font-size: 13px;
  font-weight: 500;
  user-select: none;
}

/* ── Features Section ────────────────────────────────────────── */

.features-section {
  @apply py-16 px-[10%];
  background: var(--ge-bg-page);
}

.section-title {
  @apply text-center font-semibold m-0 mb-10;
  font-size: 28px;
  color: var(--ge-text-primary);
}

.features-grid {
  @apply grid gap-6;
  grid-template-columns: repeat(2, 1fr);
  max-width: 800px;
  margin: 0 auto;
}

.feature-card {
  @apply rounded-xl p-6;
  background: var(--ge-bg-container);
  border: 1px solid var(--ge-border-color);
  transition:
    box-shadow 0.25s,
    transform 0.25s;
}

.feature-card:hover {
  box-shadow: var(--ge-shadow);
  transform: translateY(-4px);
}

.feature-icon {
  @apply flex items-center justify-center rounded-lg mb-4;
  width: 44px;
  height: 44px;
  font-size: 22px;
  color: var(--ge-primary);
  background: var(--ge-primary-light);
}

.feature-title {
  @apply font-semibold m-0 mb-2;
  font-size: 16px;
  color: var(--ge-text-primary);
}

.feature-desc {
  @apply m-0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--ge-text-secondary);
}

/* ── Tech Stack Section ──────────────────────────────────────── */

.tech-section {
  @apply py-12 px-[10%];
  background: var(--ge-bg-container);
}

.tech-tags {
  @apply flex flex-wrap justify-center gap-3;
}

.tech-tag {
  @apply rounded-full px-4 py-1.5 text-sm;
  background: var(--ge-bg-elevated);
  color: var(--ge-text-secondary);
  border: 1px solid var(--ge-border-color);
  /*font-family: var(--ant-font-family);*/
}

/* ── Responsive ──────────────────────────────────────────────── */

@media (max-width: 768px) {
  .hero-section {
    @apply flex-col text-center py-16 px-5;
    gap: 32px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 17px;
  }

  .hero-actions {
    @apply justify-center;
  }

  .hero-illustration {
    display: none;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>

