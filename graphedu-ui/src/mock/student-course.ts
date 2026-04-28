/**
 * 学生课程页面 Mock 数据
 */
import type {
  StudentCourseOverviewVO,
  StudentKnowledgeProfileVO,
  StudentWeakPointVO,
  StudentChapterProgressVO,
  StudentResourceProgressItemVO,
} from '@/types/api/education/stats'
import { MOCK_NODES, MOCK_CHAPTERS } from './constants'
import { seededRandom, fmtMD } from './helpers'

export function getStudentCourseOverview(): StudentCourseOverviewVO {
  const rand = seededRandom(500)
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (6 - i))
    return {
      date: fmtMD(d),
      activeMinutes: ([85, 120, 60, 95, 140, 45, 110][i] ?? 0) + Math.floor(rand() * 20) - 10,
    }
  })

  return {
    courseId: 1,
    studentId: 10001,
    progress: 65,
    completedChapters: 2,
    totalChapters: 8,
    totalStudyTime: 1280,
    lastStudyTime: new Date().toISOString(),
    consecutiveDays: 7,
    rankPercentile: 'Top 15%',
    courseStats: {
      totalStudents: 32,
      averageProgress: 58,
      completedStudents: 3,
      todayActive: 12,
    },
    dailyActive: days,
  }
}

export function getKnowledgeProfile(): StudentKnowledgeProfileVO[] {
  const rand = seededRandom(600)
  const masteryScores = [92, 88, 85, 75, 68, 82, 80, 72, 60, 65, 70, 55, 78, 45, 40, 72, 65, 50, 48, 35, 38, 30]

  return MOCK_NODES.map((n, i) => {
    const score = masteryScores[i] ?? Math.floor(30 + rand() * 60)
    let level: string
    let reason: string
    if (score >= 75) {
      level = 'high'
      reason = '该知识点掌握良好，能够准确理解和应用。'
    } else if (score >= 50) {
      level = 'medium'
      reason = '该知识点基本理解，但部分应用题仍需加强。'
    } else {
      level = 'low'
      reason = '该知识点掌握薄弱，建议重新学习相关资料并多做练习。'
    }
    return {
      nodeUuid: n.uuid,
      nodeName: n.title,
      firstInteractionAt: new Date(Date.now() - (30 - i) * 86400000 * 2).toISOString(),
      lastInteractionAt: new Date(Date.now() - i * 86400000).toISOString(),
      totalInteractionCount: Math.floor(5 + score * 0.3 + rand() * 10),
      totalQuestionCount: Math.floor(2 + score * 0.15 + rand() * 5),
      totalInterestCount: Math.floor(rand() * 3),
      totalExplainRequestCount: Math.floor(rand() * 2),
      totalStudySeconds: Math.floor(120 + score * 20 + rand() * 600),
      latestMasteryLevel: level,
      latestMasteryScore: score,
      latestAssessedAt: new Date(Date.now() - i * 86400000).toISOString(),
      latestAssessmentReason: reason,
    }
  })
}

export function getWeakPoints(): StudentWeakPointVO[] {
  return [
    {
      nodeUuid: 'node-poset',
      nodeName: '偏序关系',
      totalInteractionCount: 12,
      totalQuestionCount: 8,
      totalStudySeconds: 2400,
      latestMasteryLevel: 'low',
      latestMasteryScore: 35,
      latestAssessedAt: new Date(Date.now() - 86400000).toISOString(),
      effortRatio: 2.8,
    },
    {
      nodeUuid: 'node-combiperm',
      nodeName: '排列与组合',
      totalInteractionCount: 8,
      totalQuestionCount: 5,
      totalStudySeconds: 1800,
      latestMasteryLevel: 'low',
      latestMasteryScore: 30,
      latestAssessedAt: new Date(Date.now() - 2 * 86400000).toISOString(),
      effortRatio: 2.2,
    },
    {
      nodeUuid: 'node-binarytree',
      nodeName: '二叉树',
      totalInteractionCount: 10,
      totalQuestionCount: 6,
      totalStudySeconds: 2100,
      latestMasteryLevel: 'low',
      latestMasteryScore: 38,
      latestAssessedAt: new Date(Date.now() - 86400000).toISOString(),
      effortRatio: 1.8,
    },
    {
      nodeUuid: 'node-nf',
      nodeName: '范式',
      totalInteractionCount: 18,
      totalQuestionCount: 10,
      totalStudySeconds: 3600,
      latestMasteryLevel: 'medium',
      latestMasteryScore: 48,
      latestAssessedAt: new Date(Date.now() - 3 * 86400000).toISOString(),
      effortRatio: 1.5,
    },
    {
      nodeUuid: 'node-path',
      nodeName: '路径与回路',
      totalInteractionCount: 10,
      totalQuestionCount: 6,
      totalStudySeconds: 2100,
      latestMasteryLevel: 'low',
      latestMasteryScore: 40,
      latestAssessedAt: new Date(Date.now() - 86400000).toISOString(),
      effortRatio: 1.9,
    },
  ]
}

export function getChapterProgress(): StudentChapterProgressVO[] {
  const rates = [95, 82, 88, 60, 72, 55, 48, 35]
  return MOCK_CHAPTERS.map((ch, i) => {
    const rate = rates[i] ?? 0
    const resourceCount = Math.floor(2 + Math.random() * 4)
    const completedResources = Math.floor(resourceCount * (rate / 100))
    const resources: StudentResourceProgressItemVO[] = Array.from({ length: resourceCount }, (_, ri) => {
      const types = ['video', 'document', 'text']
      return {
        resourceId: 20000 + ch.chapterId * 100 + ri,
        resourceName: `${ch.chapterName} - 资料${ri + 1}`,
        resourceType: types[ri % 3] ?? 'text',
        completionRate: Math.min(100, Math.floor(rate + Math.random() * 15)),
        isCompleted: rate > 80 || ri < completedResources ? 'Y' : 'N',
        viewCount: Math.floor(1 + Math.random() * 4),
        totalDuration: Math.floor(200 + Math.random() * 1500),
        lastViewTime: new Date(Date.now() - Math.floor(Math.random() * 5 * 86400000)).toISOString(),
      }
    })

    return {
      chapterId: ch.chapterId,
      chapterName: ch.chapterName,
      chapterNo: ch.chapterNo,
      parentId: 0,
      completionRate: rate,
      isCompleted: rate >= 90 ? 'Y' : 'N',
      resourceCount,
      completedResourceCount: completedResources,
      lastVisitTime: new Date(Date.now() - (8 - i) * 86400000).toISOString(),
      resources,
    }
  })
}
