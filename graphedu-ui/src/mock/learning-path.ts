/**
 * 学习路径 Mock 数据
 */
import type {
  LearningPlanListVO,
  LearningPlanDetailVO,
  LearningPlanProgressVO,
  LearningPathProgressDetailVO,
} from '@/types/api/knowledge-graph'
import { MOCK_PLANS, MOCK_NODES } from './constants'
import { buildNvlData } from './knowledge-graph'
import type { NvlGraphDataVO } from '@/types/api/knowledge-graph'

export function getMyLearningPlans(): LearningPlanListVO[] {
  return MOCK_PLANS.map((p) => ({
    plan_id: p.plan_id,
    course_id: p.course_id,
    title: p.title,
    status: p.status,
    create_time: p.create_time,
  }))
}

export function getLearningPlanDetail(planId: string): LearningPlanDetailVO {
  if (planId === 'plan-002') {
    return getCompletedPlanDetail()
  }
  return getActivePlanDetail()
}

function getActivePlanDetail(): LearningPlanDetailVO {
  // 命题逻辑学习路径：包含命题逻辑章的 6 个节点
  const planNodes = MOCK_NODES.filter((n) => n.chapterId === 1)

  const graph: NvlGraphDataVO = buildNvlData(planNodes)

  const masteryScores: Record<string, { level: string; score: number; mastered: boolean }> = {
    'node-prop': { level: 'high', score: 92, mastered: true },
    'node-connective': { level: 'high', score: 88, mastered: true },
    'node-truthtable': { level: 'high', score: 85, mastered: true },
    'node-equiv': { level: 'high', score: 75, mastered: false },
    'node-nf': { level: 'medium', score: 68, mastered: false },
    'node-inference': { level: 'high', score: 82, mastered: false },
  }

  const details: LearningPathProgressDetailVO[] = planNodes.map((n) => {
    const m = masteryScores[n.uuid] ?? {
      level: 'low',
      score: 30,
      mastered: false,
    }
    return {
      node_uuid: n.uuid,
      mastery_level: m.level,
      mastery_score: m.score,
      mastered: m.mastered,
    }
  })

  const mastered = details.filter((d) => d.mastered).length

  const progress: LearningPlanProgressVO = {
    total: planNodes.length,
    mastered,
    progress_pct: Math.round((mastered / planNodes.length) * 100),
    details,
  }

  return {
    plan: {
      plan_id: 'plan-001',
      course_id: 1,
      title: '命题逻辑基础学习路径',
      status: 'active',
      create_time: '2026-04-01T08:00:00Z',
    },
    graph,
    progress,
  }
}

function getCompletedPlanDetail(): LearningPlanDetailVO {
  const planNodes = MOCK_NODES.filter((n) => n.chapterId === 3)
  const graph: NvlGraphDataVO = buildNvlData(planNodes)

  // 与 knowledge profile mock 保持一致：node-set(92), node-setop(72), node-cartesian(70)
  const scores: Record<string, { level: string; score: number }> = {
    'node-set': { level: 'high', score: 92 },
    'node-setop': { level: 'high', score: 72 },
    'node-cartesian': { level: 'high', score: 70 },
  }

  const details: LearningPathProgressDetailVO[] = planNodes.map((n) => {
    const m = scores[n.uuid] ?? { level: 'high', score: 88 }
    return {
      node_uuid: n.uuid,
      mastery_level: m.level,
      mastery_score: m.score,
      mastered: true,
    }
  })

  const progress: LearningPlanProgressVO = {
    total: planNodes.length,
    mastered: planNodes.length,
    progress_pct: 100,
    details,
  }

  return {
    plan: {
      plan_id: 'plan-002',
      course_id: 1,
      title: '集合论学习路径',
      status: 'completed',
      create_time: '2026-03-20T08:00:00Z',
    },
    graph,
    progress,
  }
}
