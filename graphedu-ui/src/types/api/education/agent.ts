import type { CourseListVO } from '@/types/api/education/course.ts'

/**
 * 创建对话会话请求
 */
export interface ChatSessionCreateDTO {
  /** 会话标题 */
  title?: string
  /** 关联课程ID */
  courseId?: number
}

/**
 * 更新对话会话请求
 */
export interface ChatSessionUpdateDTO {
  /** 会话ID */
  sessionId: number
  /** 会话标题 */
  title?: string
  /** 上下文摘要 */
  contextSummary?: string
}

/**
 * 对话会话查询请求
 */
export interface ChatSessionQueryDTO {
  /** 会话ID */
  sessionId?: number
  /** 用户ID */
  userId?: number
  /** 关联课程ID */
  courseId?: number
  /** 聊天会话状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
  /** 创建开始时间 */
  beginTime?: string
  /** 创建结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 对话会话详细信息
 */
export interface ChatSessionDetailVO {
  /** 对话ID */
  convId: number
  /** 用户ID */
  userId: number
  /** 关联课程ID */
  courseId?: number
  /** 会话标题 */
  title?: string
  /** 上下文摘要 */
  contextSummary?: string
  /** 消息数量 */
  messageCount: number
  /** 聊天会话状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 最后消息时间 */
  lastMessageTime: string
  /** 关联课程信息 */
  course?: CourseListVO
}

/**
 * 对话会话列表项
 */
export interface ChatSessionListVO {
  /** 对话ID */
  convId: number
  /** 用户ID */
  userId: number
  /** 关联课程ID */
  courseId?: number
  /** 会话标题 */
  title?: string
  /** 消息数量 */
  messageCount: number
  /** 聊天会话状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 最后消息时间 */
  lastMessageTime: string
  /** 关联课程名称 */
  courseName?: string
}

export type QuestionType = 'single' | 'multi' | 'judge' | 'essay'

/** 引用文本内容 */
export interface QuoteContent {
  quotes: string[]
  content: string | null
  /** 引用来源，如：课程 > 章节 > 小节 */
  source?: string | null
}

/** 题目选项内容 */
export interface QuestionOptionContent {
  questionType?: string
  title?: string
  content?: string
  options: string[]
  answer?: string[] | null
  explanation?: string
  /** SSE 透传的 snake_case 字段（实际运行时数据） */
  exercise_id?: number | null
  /** 关联习题ID（来自题库时非空，用于提交作答记录） */
  exerciseId?: number | null
}

/** 聊天消息内容（联合类型，type 字段区分） */
export type ChatMessageContent =
  | { type: 'text'; text: string }
  | { type: 'quote_text'; quote_text: QuoteContent }
  | { type: 'question_option'; question_option: QuestionOptionContent }
  | { type: 'image_url'; image_url: Record<string, any> }
  | { type: 'file_object'; file_object: Record<string, any> }
  | { type: 'link'; link: Record<string, any> }

/**
 * 聊天额外功能（与后端 ChatFeature 对齐）
 */
export interface ChatFeature {
  /** 知识问答 / 图数据库检索 */
  graphrag?: boolean
  /** 联网搜索 */
  web_search?: 'enable' | 'disable' | 'auto'
  /** 思考模式 */
  thinking_mode?: 'enable' | 'disable' | 'auto'
  /** 允许读取待办 */
  checklist_visit?: boolean
  /** 允许读取学习计划 */
  plan_visit?: boolean
  /** 当前会话关联的章节ID */
  chapter_id?: number
}

/**
 * 聊天消息（与后端 ChatMessage 对齐）
 */
export interface ChatMessage {
  role: number
  contents: ChatMessageContent[]
  user_id?: number
  conv_id: number
  message_id?: string
  feature?: ChatFeature
}
