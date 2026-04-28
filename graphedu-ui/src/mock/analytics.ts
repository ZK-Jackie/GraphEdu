/**
 * 教学分析 Mock 数据
 */
import type {
  CourseAnalyticsVO,
  StudentRankingItemVO,
  StudentChapterLearningResultVO,
  StudentChapterDetailResultVO,
  StudentChapterResourceDetailVO,
} from '@/types/api/education/stats'
import type { StudentChapterExerciseDetailVO } from '@/types/api/education/courseExercise'
import { MOCK_STUDENTS, MOCK_CHAPTERS, MOCK_NODES } from './constants'
import { seededRandom } from './helpers'

export function getCourseAnalytics(): CourseAnalyticsVO {
  return {
    totalStudents: 32,
    activeStudents: 28,
    averageProgress: 58,
    totalStudyTime: 15680,
    chapterCompletion: MOCK_CHAPTERS.map((ch, i) => ({
      chapterId: ch.chapterId,
      chapter: ch.chapterName,
      completion: [92, 78, 85, 62, 70, 55, 48, 40][i] ?? 0,
      students: [30, 28, 29, 24, 26, 22, 20, 18][i] ?? 0,
    })),
    dailyActive: Array.from({ length: 7 }, (_, i) => {
      const d = new Date()
      d.setDate(d.getDate() - (6 - i))
      return {
        date: `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`,
        count: [18, 22, 15, 20, 25, 12, 16][i] ?? 0,
      }
    }),
    progressDistribution: [
      { range: '0-20%', count: 3 },
      { range: '20-40%', count: 5 },
      { range: '40-60%', count: 10 },
      { range: '60-80%', count: 9 },
      { range: '80-100%', count: 5 },
    ],
    totalEventCount: 4520,
    totalQuestionCount: 890,
    totalQuizCount: 1250,
    quizCorrectRate: 68,
    avgMasteryScore: 62,
    highMasteryCount: 5,
    mediumMasteryCount: 16,
    lowMasteryCount: 11,
    nodesTouched: 22,
  }
}

export function getCourseRankings(): StudentRankingItemVO[] {
  const rand = seededRandom(300)
  return MOCK_STUDENTS.map((s) => {
    const pct = s.mastery / 100
    return {
      studentId: s.studentId,
      studentName: s.realName,
      totalEventCount: Math.floor(80 + pct * 300 + rand() * 50),
      questionCount: Math.floor(10 + pct * 40 + rand() * 10),
      quizCount: Math.floor(15 + pct * 50 + rand() * 15),
      quizCorrectRate: Math.floor(40 + pct * 40 + rand() * 10),
      avgMasteryScore: s.mastery + Math.floor(rand() * 6) - 3,
      chaptersTouched: Math.floor(3 + pct * 5),
      chapterCoverageRate: Math.floor(30 + pct * 60 + rand() * 10),
      nodesTouched: Math.floor(5 + pct * 17),
      nodeCoverageRate: Math.floor(20 + pct * 70 + rand() * 10),
      totalStudySeconds: Math.floor(3600 + pct * 18000 + rand() * 3600),
      studyDays: Math.floor(10 + pct * 30 + rand() * 5),
      masteryPercentile: Math.max(0.05, pct),
    }
  })
}

export function getCourseStudents() {
  const rand = seededRandom(400)
  const students = MOCK_STUDENTS.map((s, i) => ({
    enrollmentId: 1000 + i,
    studentId: s.studentId,
    realName: s.realName,
    studentNo: s.studentNo,
    className: s.className,
    faculty: s.faculty,
    gender: s.gender,
    avatarUrl: undefined,
    enrollTime: '2026-02-25T10:00:00Z',
    progress: s.progress,
    lastStudyTime: new Date(Date.now() - Math.floor(rand() * 5 * 86400000)).toISOString(),
    status: '0',
  }))

  return {
    students,
    stats: {
      totalStudents: 32,
      averageProgress: 58,
      completedStudents: 3,
      todayActive: 12,
    },
    total: 32,
  }
}

/** ADMIN-STUDENT001 (studentId=10001) 的章节学习数据 */
export function getStudentChapterLearning(): StudentChapterLearningResultVO {
  const chapters = MOCK_CHAPTERS.map((ch, i) => {
    const rates = [95, 82, 88, 60, 72, 55, 48, 35]
    const rate = rates[i] ?? 0
    const quizTotal = Math.floor(3 + Math.random() * 8)
    const quizCorrect = Math.floor(quizTotal * (rate / 100) * (0.8 + Math.random() * 0.2))
    return {
      chapterId: ch.chapterId,
      chapterName: ch.chapterName,
      chapterNo: ch.chapterNo,
      parentId: 0,
      completionRate: rate,
      isCompleted: rate >= 90 ? 'Y' : 'N',
      quizTotal,
      quizCorrect,
      quizCorrectRate: quizTotal > 0 ? Math.round((quizCorrect / quizTotal) * 100) : 0,
      avgMasteryScore: Math.floor(rate * 0.9 + Math.random() * 10),
      totalStudySeconds: Math.floor(rate * 120 + Math.random() * 600),
      lastStudyTime: new Date(Date.now() - (8 - i) * 86400000).toISOString(),
    }
  })

  return {
    studentId: 10001,
    courseId: 1,
    chapters,
    totalChapters: 8,
    completedChapters: chapters.filter((c) => c.isCompleted === 'Y').length,
    totalStudySeconds: chapters.reduce((acc, c) => acc + c.totalStudySeconds, 0),
  }
}

/** 章节展开详情 */
export function getStudentChapterDetail(
  chapterId: number,
  detailType: 'resources' | 'exercises' | 'mastery'
): StudentChapterDetailResultVO {
  const chapterNodes = MOCK_NODES.filter((n) => n.chapterId === chapterId)

  if (detailType === 'resources') {
    const types = ['video', 'document', 'text']
    const items: StudentChapterResourceDetailVO[] = chapterNodes.map((n, i) => ({
      progressId: 10000 + chapterId * 100 + i,
      resourceId: 20000 + chapterId * 100 + i,
      resourceName: `${n.title} - 学习资料`,
      resourceType: types[i % 3] ?? 'text',
      completionRate: Math.floor(60 + Math.random() * 40),
      isCompleted: Math.random() > 0.3 ? 'Y' : 'N',
      viewCount: Math.floor(1 + Math.random() * 5),
      totalDuration: Math.floor(300 + Math.random() * 1800),
      lastViewTime: new Date(Date.now() - Math.floor(Math.random() * 7 * 86400000)).toISOString(),
    }))
    return { detailType: 'resources', items, total: items.length }
  }

  if (detailType === 'exercises') {
    const items = Array.from({ length: Math.floor(2 + Math.random() * 4) }, (_, i) => ({
      attemptId: 50000 + chapterId * 100 + i,
      exerciseId: 30000 + chapterId * 100 + i,
      studentAnswer: null,
      isCorrect: Math.random() > 0.35,
      timeSpent: Math.floor(30 + Math.random() * 300),
      attemptTime: new Date(Date.now() - Math.floor(Math.random() * 14 * 86400000)).toISOString(),
    }))
    return { detailType: 'exercises', items: items as StudentChapterExerciseDetailVO[], total: items.length }
  }

  // mastery
  const items = chapterNodes.map((n, i) => ({
    masteryId: 40000 + chapterId * 100 + i,
    nodeUuid: n.uuid,
    nodeTitle: n.title,
    masteryScore: Math.floor(30 + Math.random() * 65),
    masteryLevel: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
    assessedAt: new Date(Date.now() - Math.floor(Math.random() * 7 * 86400000)).toISOString(),
  }))
  return { detailType: 'mastery', items, total: items.length }
}
