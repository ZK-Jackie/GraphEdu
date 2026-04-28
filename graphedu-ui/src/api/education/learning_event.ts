/**
 * 学习事件上报相关 API
 * 对应后端：graphedu/api/services/education/learning_event.py
 */
import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common.ts'

/**
 * 学习事件上报请求参数（前端精简版，studentId 由后端从 JWT 注入）
 */
export interface LearningEventReportDTO {
  /** 课程ID */
  courseId: number
  /** 事件类型 */
  eventType: 'chapter_open' | 'interest' | 'explain_request' | 'map_click' | 'tool_map_query'
  /** 章节ID */
  chapterId?: number
  /** 知识点UUID */
  nodeUuid?: string
  /** 事件文本内容 */
  eventContent?: string
  /** 事件扩展数据 */
  eventPayload?: Record<string, unknown>
  /** 会话ID */
  sessionId?: number
  /** 事件持续时长（秒） */
  durationSeconds?: number
}

/**
 * 上报学习事件
 * POST /education/learning-event
 */
export function reportLearningEvent(data: LearningEventReportDTO): Promise<ResponseType<{ eventId: number }>> {
  return request({
    url: '/education/learning-event',
    method: 'post',
    data,
  })
}
