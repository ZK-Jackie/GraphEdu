import type { QuestionOptionContent } from '@/types/api/education/agent.ts'

/**
 * 课程练习查询请求
 */
export interface CourseExerciseQueryDTO {
  /** 练习ID */
  exerciseId?: number
  /** 课程ID */
  courseId?: number
  /** 章节ID */
  chapterId?: number
  /** 练习来源 */
  source?: string
  /** 练习状态（0正常 1停用 2已删除） */
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
 * 创建课程练习请求
 */
export interface CourseExerciseCreateDTO {
  /** 课程ID */
  courseId: number
  /** 章节ID（可选） */
  chapterId?: number
  /** 练习内容，支持单题或题目列表 */
  exercise?: QuestionOptionContent | QuestionOptionContent[] | null
  /** 练习来源 */
  source?: string
}

/**
 * 更新课程练习请求
 */
export interface CourseExerciseUpdateDTO {
  /** 练习ID */
  exerciseId: number
  /** 章节ID（可选） */
  chapterId?: number
  /** 练习内容，支持单题或题目列表 */
  exercise?: QuestionOptionContent | QuestionOptionContent[] | null
  /** 练习来源 */
  source?: string
  /** 练习状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 教师端批量生成课程练习请求
 */
export interface CourseExerciseBatchGenerateDTO {
  /** 课程ID */
  courseId: number
  /** 章节ID（可选） */
  chapterId?: number
  /** 章节资料ID列表 */
  resourceIds: number[]
  /** 难度等级 */
  difficulty?: string
  /** 题目类型 */
  questionType?: 'single' | 'judge' | 'multi'
  /** 附加描述 */
  extraInfo?: string
  /** 生成数量 */
  number?: number
}

/**
 * 课程练习详情 VO
 */
export interface CourseExerciseDetailVO {
  /** 练习ID */
  exerciseId: number
  /** 课程ID */
  courseId: number
  /** 章节ID（可选） */
  chapterId?: number
  /** 练习内容，支持单题或题目列表 */
  exercise?: QuestionOptionContent | QuestionOptionContent[] | null
  /** 练习来源 */
  source?: string
  /** 练习状态（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
}

/**
 * 课程练习列表项 VO
 */
export interface CourseExerciseListVO {
  /** 练习ID */
  exerciseId: number
  /** 课程ID */
  courseId: number
  /** 章节ID（可选） */
  chapterId?: number
  /** 练习内容，支持单题或题目列表 */
  exercise?: QuestionOptionContent | QuestionOptionContent[] | null
  /** 练习来源 */
  source?: string
  /** 练习状态（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
}

/**
 * 学生提交作答请求
 */
export interface ExerciseAttemptSubmitDTO {
  /** 关联习题ID */
  exerciseId: number
  /** 学生答案（单选/判断为单个字符串，多选为列表） */
  studentAnswer: string[] | string
  /** 用时（秒） */
  timeSpent?: number
}

/**
 * 作答记录查询请求
 */
export interface ExerciseAttemptQueryDTO {
  /** 习题ID */
  exerciseId?: number
  /** 学生ID */
  studentId?: number
  /** 课程ID（通过习题间接关联） */
  courseId?: number
  /** 是否正确 */
  isCorrect?: boolean
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * AI 出题异步任务提交结果 VO
 */
export interface CourseExerciseGenerateTaskVO {
  /** Celery 任务 ID */
  taskId: string
  /** 任务状态 */
  taskStatus: string
  /** 提示信息 */
  message?: string
}

/**
 * AI 出题任务进度 VO
 */
export interface CourseExerciseGenerateProgressVO {
  /** Celery 任务 ID */
  taskId: string
  /** 任务状态 (pending/processing/success/failed) */
  taskStatus: string
  /** 进度百分比 (0-100) */
  progressPercent: number
  /** 已生成题目数量（成功时有效） */
  generatedCount: number
  /** 进度描述或错误信息 */
  message?: string
}

/**
 * 习题作答记录 VO
 */
export interface ExerciseAttemptVO {
  /** 作答记录 ID */
  attemptId: number
  /** 关联习题 ID */
  exerciseId: number
  /** 学生 ID */
  studentId: number
  /** 学生答案 */
  studentAnswer: string[] | string | null
  /** 是否正确 */
  isCorrect: boolean | null
  /** 用时（秒） */
  timeSpent: number | null
  /** 作答时间 */
  attemptTime: string | null
}

/**
 * 学生章节练习详情 VO
 */
export interface StudentChapterExerciseDetailVO {
  /** 作答记录 ID */
  attemptId: number
  /** 关联习题 ID */
  exerciseId: number
  /** 学生答案 */
  studentAnswer: string[] | string | null
  /** 是否正确 */
  isCorrect: boolean | null
  /** 用时（秒） */
  timeSpent: number | null
  /** 作答时间 */
  attemptTime: string | null
}

/**
 * 习题作答统计 VO
 */
export interface ExerciseAttemptStatisticsVO {
  /** 习题 ID */
  exerciseId: number
  /** 总作答次数 */
  totalAttempts: number
  /** 正确次数 */
  correctAttempts: number
  /** 正确率 */
  correctRate: number
  /** 平均用时（秒） */
  avgTimeSpent: number | null
}
