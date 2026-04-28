/**
 * 仪表盘 Mock 数据
 */
import type {
  StudentDashboardSummaryVO,
  DashboardCalendarItemVO,
  DashboardCourseItemVO,
  DashboardWeakPointVO,
  DailyActiveItemVO,
  TeacherDashboardSummaryVO,
  TeacherDashboardCourseVO,
  TeacherDashboardRankingVO,
  DailyActiveMinutesVO,
} from '@/types/api/education/stats'
import { MOCK_STUDENTS } from './constants'
import { fmtYMD, recentDays, seededRandom } from './helpers'
import coverDiscrete from '@/assets/mock/discrete.jpeg'
import coverLinear from '@/assets/mock/linear.jpeg'
import coverComnet from '@/assets/mock/comnet.jpeg'

// ==================== 学生端 ====================

export function getStudentSummary(): StudentDashboardSummaryVO {
  return {
    totalStudyDays: 45,
    totalStudyMinutes: 3280,
    effectiveStudyMinutes: 2650,
    reviewStudyMinutes: 420,
    activeCourseCount: 3,
    consecutiveDays: 7,
  }
}

export function getStudentCalendar(): DashboardCalendarItemVO[] {
  const rand = seededRandom(42)
  const days = recentDays(120)
  return days.map((d) => {
    const dow = d.getDay()
    const isWeekend = dow === 0 || dow === 6
    const base = isWeekend ? 15 : 45
    const minutes = Math.floor(rand() * base) + (rand() > 0.15 ? base : 0)
    return { date: fmtYMD(d), minutes: Math.round(minutes) }
  })
}

export function getStudentTrend(): DailyActiveMinutesVO[] {
  const rand = seededRandom(100)
  const days = recentDays(7)
  const minutes = [85, 120, 60, 95, 140, 45, 110]
  return days.map((d, i) => ({
    date: `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`,
    activeMinutes: (minutes[i] ?? 0) + Math.floor(rand() * 20) - 10,
  }))
}

export function getStudentCourses(): DashboardCourseItemVO[] {
  return [
    {
      courseId: 1,
      courseName: '离散数学',
      coverUrl: coverDiscrete,
      progress: 65,
      lastStudyTime: new Date().toISOString(),
    },
    {
      courseId: 2,
      courseName: '数据结构',
      coverUrl: coverComnet,
      progress: 42,
      lastStudyTime: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      courseId: 3,
      courseName: '线性代数',
      coverUrl: coverLinear,
      progress: 78,
      lastStudyTime: new Date(Date.now() - 172800000).toISOString(),
    },
  ]
}

export function getStudentWeakPoints(): DashboardWeakPointVO[] {
  return [
    {
      nodeUuid: 'node-poset',
      nodeName: '偏序关系',
      courseName: '离散数学',
      totalInteractionCount: 12,
      totalQuestionCount: 8,
      totalStudySeconds: 2400,
      latestMasteryLevel: 'low',
      latestMasteryScore: 35,
    },
    {
      nodeUuid: 'node-nf',
      nodeName: '范式',
      courseName: '离散数学',
      totalInteractionCount: 18,
      totalQuestionCount: 10,
      totalStudySeconds: 3600,
      latestMasteryLevel: 'medium',
      latestMasteryScore: 48,
    },
    {
      nodeUuid: 'node-combiperm',
      nodeName: '排列与组合',
      courseName: '离散数学',
      totalInteractionCount: 8,
      totalQuestionCount: 5,
      totalStudySeconds: 1800,
      latestMasteryLevel: 'low',
      latestMasteryScore: 32,
    },
    {
      nodeUuid: 'node-binarytree',
      nodeName: '二叉树',
      courseName: '数据结构',
      totalInteractionCount: 15,
      totalQuestionCount: 9,
      totalStudySeconds: 3000,
      latestMasteryLevel: 'medium',
      latestMasteryScore: 52,
    },
    {
      nodeUuid: 'node-path',
      nodeName: '路径与回路',
      courseName: '离散数学',
      totalInteractionCount: 10,
      totalQuestionCount: 6,
      totalStudySeconds: 2100,
      latestMasteryLevel: 'low',
      latestMasteryScore: 40,
    },
  ]
}

// ==================== 教师端 ====================

export function getTeacherSummary(): TeacherDashboardSummaryVO {
  return {
    totalCourses: 3,
    totalStudents: 42,
    todayActiveStudents: 12,
    avgMasteryScore: 62,
  }
}

export function getTeacherCourses(): TeacherDashboardCourseVO[] {
  return [
    {
      courseId: 1,
      courseName: '离散数学',
      studentCount: 32,
      avgMasteryScore: 62,
      quizCorrectRate: 68,
    },
    {
      courseId: 2,
      courseName: '高等数学 A',
      studentCount: 45,
      avgMasteryScore: 58,
      quizCorrectRate: 65,
    },
    {
      courseId: 3,
      courseName: '概率论与数理统计',
      studentCount: 38,
      avgMasteryScore: 55,
      quizCorrectRate: 60,
    },
  ]
}

export function getTeacherRankings(): TeacherDashboardRankingVO[] {
  return MOCK_STUDENTS.slice(0, 10).map((s, i) => ({
    studentId: s.studentId,
    studentName: s.realName,
    courseName: '离散数学',
    masteryPercentile: Math.max(0.05, 1 - i * 0.09),
    avgMasteryScore: s.mastery,
  }))
}

export function getTeacherTrend(): DailyActiveItemVO[] {
  const rand = seededRandom(200)
  const days = recentDays(30)
  return days.map((d) => {
    const dow = d.getDay()
    const isWeekend = dow === 0 || dow === 6
    const base = isWeekend ? 5 : 15
    return {
      date: `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`,
      count: Math.floor(rand() * base) + base,
    }
  })
}
