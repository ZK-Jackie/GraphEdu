import type { StudentChapterExerciseDetailVO } from '@/types/api/education/courseExercise.ts'
import type { StudentChapterMasteryDetailVO } from '@/types/api/education/mastery.ts'

/**
 * 章节完成率统计项
 */
export interface ChapterCompletionItemVO {
  /** 章节ID */
  chapterId: number
  /** 章节名称 */
  chapter: string
  /** 平均完成率（0-100） */
  completion: number
  /** 已学习学生数 */
  students: number
}

/**
 * 每日活跃度统计项
 */
export interface DailyActiveItemVO {
  /** 日期（MM-DD格式） */
  date: string
  /** 活跃人数 */
  count: number
}

/**
 * 进度分布统计项
 */
export interface ProgressDistributionItemVO {
  /** 范围标签（如 "0-20%"） */
  range: string
  /** 人数 */
  count: number
}

/**
 * 课程数据分析结果
 */
export interface CourseAnalyticsVO {
  /** 总学生数 */
  totalStudents: number
  /** 活跃学生数（指定时间范围内） */
  activeStudents: number
  /** 平均学习进度（0-100） */
  averageProgress: number
  /** 总学习时长（分钟） */
  totalStudyTime: number
  /** 章节完成率列表 */
  chapterCompletion: ChapterCompletionItemVO[]
  /** 每日活跃度列表 */
  dailyActive: DailyActiveItemVO[]
  /** 进度分布列表 */
  progressDistribution: ProgressDistributionItemVO[]
  /** 总事件数（新增） */
  totalEventCount: number
  /** 总提问次数（新增） */
  totalQuestionCount: number
  /** 总答题次数（新增） */
  totalQuizCount: number
  /** 答题正确率（新增） */
  quizCorrectRate: number
  /** 平均掌握度评分（新增） */
  avgMasteryScore?: number
  /** 高掌握度人数（新增） */
  highMasteryCount: number
  /** 中掌握度人数（新增） */
  mediumMasteryCount: number
  /** 低掌握度人数（新增） */
  lowMasteryCount: number
  /** 接触的知识点数（新增） */
  nodesTouched: number
}

/**
 * 学生课程学习概览 VO
 */
export interface StudentCourseOverviewVO {
  /** 课程ID */
  courseId: number
  /** 学生ID */
  studentId: number
  /** 学习进度（0-100） */
  progress: number
  /** 已完成章节数 */
  completedChapters: number
  /** 总章节数 */
  totalChapters: number
  /** 累计学习时长（分钟） */
  totalStudyTime: number
  /** 最后学习时间 */
  lastStudyTime?: string
  /** 连续学习天数 */
  consecutiveDays: number
  /** 排名百分位（如 'Top 5%'） */
  rankPercentile?: string
  /** 课程整体统计 */
  courseStats: CourseStudentStatsVO
  /** 每日学习活跃度 */
  dailyActive: DailyActiveMinutesVO[]
}

/**
 * 课程学生统计 VO
 */
export interface CourseStudentStatsVO {
  /** 总学生数 */
  totalStudents: number
  /** 平均学习进度（0-100） */
  averageProgress: number
  /** 已完成学生数（进度100%） */
  completedStudents: number
  /** 今日活跃学生数 */
  todayActive: number
}

/**
 * 每日学习活跃度项 VO（活跃时长，学生课程概览用）
 */
export interface DailyActiveMinutesVO {
  /** 日期（MM-DD 格式） */
  date: string
  /** 活跃时长（分钟） */
  activeMinutes: number
}

/**
 * 学生资源阅读进度项 VO
 */
export interface StudentResourceProgressItemVO {
  /** 资料ID */
  resourceId: number
  /** 资料名称 */
  resourceName: string
  /** 资料类型（video/document/text） */
  resourceType: string
  /** 完成度（0-100） */
  completionRate: number
  /** 是否完成（Y/N） */
  isCompleted: string
  /** 阅读次数 */
  viewCount: number
  /** 累计阅读时长（秒） */
  totalDuration: number
  /** 最后阅读时间 */
  lastViewTime?: string
}

/**
 * 学生章节学习进度 VO
 */
export interface StudentChapterProgressVO {
  /** 章节ID */
  chapterId: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号 */
  chapterNo: number
  /** 父章节ID */
  parentId: number
  /** 完成度（0-100） */
  completionRate: number
  /** 是否完成（Y/N） */
  isCompleted: string
  /** 总资料数 */
  resourceCount: number
  /** 已完成资料数 */
  completedResourceCount: number
  /** 最后访问时间 */
  lastVisitTime?: string
  /** 资料阅读进度列表 */
  resources: StudentResourceProgressItemVO[]
}

/**
 * 创建学生资料阅读进度请求
 */
export interface ResourceProgressReportDTO {
  /** 资料ID */
  resourceId: number
  /** 当前位置（页码/秒数/滚动百分比） */
  position?: Record<string, any>
  /** 本次增量时长（秒），后端负责累加（wall-clock 总时长） */
  durationSeconds?: number
  /** 完成度（0-100），不传则后端根据 position 自算 */
  completionRate?: number
  /** 本次有效增量时长（秒），排除空闲时间 */
  effectiveDurationSeconds?: number
  /** 本次空闲时长（秒） */
  idleSeconds?: number
}

/**
 * 学生知识点掌握度画像 VO
 */
export interface StudentResourceProgressDetailVO {
  /** 进度记录ID */
  progressId: number
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 章节ID */
  chapterId: number
  /** 资料ID */
  resourceId: number
  /** 资料类型（video视频/document文档/text文本） */
  resourceType: string
  /** 完成度（0-100） */
  completionRate: number
  /** 是否完成（Y/N） */
  isCompleted: string
  /** 阅读次数 */
  viewCount: number
  /** 累计阅读时长（秒） */
  totalDuration: number
  /** 有效阅读时长（秒），排除空闲时间 */
  effectiveDuration: number
  /** 复习时长（秒），资源完成后再次阅读的有效时长 */
  reviewDuration: number
  /** 首次阅读时长（秒），资源完成前的有效累计时长 */
  firstReadDuration: number
  /** 最后阅读位置（JSONB格式） */
  lastPosition?: Record<string, any>
  /** 首次阅读时间 */
  firstViewTime?: string
  /** 最后阅读时间 */
  lastViewTime?: string
  /** 完成时间 */
  completeTime?: string
  /** 状态（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime: string
  /** 更新时间 */
  updateTime: string
  /** 章节名称 */
  chapterName?: string
  /** 资料名称 */
  resourceName?: string
}

/**
 * 学生知识点掌握度画像 VO
 */
export interface StudentKnowledgeProfileVO {
  /** 知识点UUID */
  nodeUuid: string
  /** 知识点名称 */
  nodeName: string
  /** 首次交互时间 */
  firstInteractionAt?: string
  /** 最后交互时间 */
  lastInteractionAt?: string
  /** 总交互次数 */
  totalInteractionCount: number
  /** 总提问次数 */
  totalQuestionCount: number
  /** 总标记兴趣次数 */
  totalInterestCount: number
  /** 总请求解释次数 */
  totalExplainRequestCount: number
  /** 总学习时长（秒） */
  totalStudySeconds: number
  /** 最新掌握等级 */
  latestMasteryLevel: string
  /** 最新掌握度评分 */
  latestMasteryScore?: number
  /** 最新评估时间 */
  latestAssessedAt?: string
  /** 最新AI评估理由 */
  latestAssessmentReason?: string
}

/**
 * 学生薄弱知识点 VO（学生端视角，不含 studentId/courseId）
 */
export interface StudentWeakPointVO {
  /** 知识点UUID */
  nodeUuid: string
  /** 知识点名称 */
  nodeName: string
  /** 总交互次数 */
  totalInteractionCount: number
  /** 总提问次数 */
  totalQuestionCount: number
  /** 总学习时长（秒） */
  totalStudySeconds: number
  /** 最新掌握等级 */
  latestMasteryLevel: string
  /** 最新掌握度评分 */
  latestMasteryScore?: number
  /** 最新评估时间 */
  latestAssessedAt?: string
  /** 投入产出比 */
  effortRatio: number
}

/**
 * 教师端：课程学生排名项 VO
 */
export interface StudentRankingItemVO {
  /** 学生ID */
  studentId: number
  /** 学生姓名 */
  studentName: string
  /** 总事件数 */
  totalEventCount: number
  /** 提问次数 */
  questionCount: number
  /** 答题次数 */
  quizCount: number
  /** 答题正确率（%） */
  quizCorrectRate?: number
  /** 平均掌握度评分 */
  avgMasteryScore?: number
  /** 接触的章节数 */
  chaptersTouched: number
  /** 章节覆盖率（%） */
  chapterCoverageRate: number
  /** 接触的知识点数 */
  nodesTouched: number
  /** 知识点覆盖率（%） */
  nodeCoverageRate: number
  /** 总学习时长（秒） */
  totalStudySeconds: number
  /** 学习天数 */
  studyDays: number
  /** 掌握度百分位（0-1） */
  masteryPercentile: number
}

/**
 * 学生仪表盘总览统计
 */
export interface StudentDashboardSummaryVO {
  /** 累计学习天数 */
  totalStudyDays: number
  /** 总学习时长（分钟） */
  totalStudyMinutes: number
  /** 有效学习时长（分钟），排除空闲 */
  effectiveStudyMinutes: number
  /** 复习时长（分钟） */
  reviewStudyMinutes: number
  /** 在修课程数 */
  activeCourseCount: number
  /** 连续学习天数 */
  consecutiveDays: number
}

/**
 * 日历热力图数据项
 */
export interface DashboardCalendarItemVO {
  /** 日期（YYYY-MM-DD） */
  date: string
  /** 学习分钟数 */
  minutes: number
}

/**
 * 仪表盘课程卡片项
 */
export interface DashboardCourseItemVO {
  /** 课程ID */
  courseId: number
  /** 课程名称 */
  courseName: string
  /** 封面URL */
  coverUrl?: string
  /** 学习进度（0-100） */
  progress: number
  /** 最后学习时间 */
  lastStudyTime?: string
}

/**
 * 仪表盘薄弱知识点项（含课程名）
 */
export interface DashboardWeakPointVO {
  /** 知识点UUID */
  nodeUuid: string
  /** 知识点名称 */
  nodeName: string
  /** 所属课程名称 */
  courseName: string
  /** 总交互次数 */
  totalInteractionCount: number
  /** 总提问次数 */
  totalQuestionCount: number
  /** 总学习时长（秒） */
  totalStudySeconds: number
  /** 最新掌握等级 */
  latestMasteryLevel: string
  /** 最新掌握度评分 */
  latestMasteryScore?: number
}

/**
 * 教师仪表盘总览统计
 */
export interface TeacherDashboardSummaryVO {
  /** 课程总数 */
  totalCourses: number
  /** 总学生数 */
  totalStudents: number
  /** 今日活跃学生数 */
  todayActiveStudents: number
  /** 平均掌握度评分 */
  avgMasteryScore?: number
}

/**
 * 教师仪表盘课程概览项
 */
export interface TeacherDashboardCourseVO {
  /** 课程ID */
  courseId: number
  /** 课程名称 */
  courseName: string
  /** 学生数 */
  studentCount: number
  /** 平均掌握度评分 */
  avgMasteryScore: number
  /** 答题正确率（%） */
  quizCorrectRate?: number
}

/**
 * 教师仪表盘学生排名项
 */
export interface TeacherDashboardRankingVO {
  /** 学生ID */
  studentId: number
  /** 学生姓名 */
  studentName: string
  /** 所属课程 */
  courseName: string
  /** 掌握度百分位（0-1） */
  masteryPercentile: number
  /** 平均掌握度评分 */
  avgMasteryScore?: number
}

/**
 * 学生章节学习摘要项 VO
 */
export interface StudentChapterLearningItemVO {
  /** 章节ID */
  chapterId: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号 */
  chapterNo: number
  /** 父章节ID */
  parentId: number
  /** 章节完成度（0-100） */
  completionRate: number
  /** 是否完成（Y/N） */
  isCompleted: string
  /** 总答题次数 */
  quizTotal: number
  /** 答对次数 */
  quizCorrect: number
  /** 答题正确率（0-100） */
  quizCorrectRate?: number
  /** 平均知识点掌握评分（0-100） */
  avgMasteryScore?: number
  /** 学习时长（秒） */
  totalStudySeconds: number
  /** 最后学习时间 */
  lastStudyTime?: string
}

/**
 * 学生章节学习汇总结果 VO
 */
export interface StudentChapterLearningResultVO {
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 章节学习列表 */
  chapters: StudentChapterLearningItemVO[]
  /** 总章节数 */
  totalChapters: number
  /** 已完成章节数 */
  completedChapters: number
  /** 总学习时长（秒） */
  totalStudySeconds: number
}

/**
 * 学生章节资料阅读明细 VO
 */
export interface StudentChapterResourceDetailVO {
  /** 进度记录ID */
  progressId: number
  /** 资料ID */
  resourceId: number
  /** 资料名称 */
  resourceName?: string
  /** 资料类型 */
  resourceType: string
  /** 完成度（0-100） */
  completionRate: number
  /** 是否完成（Y/N） */
  isCompleted: string
  /** 阅读次数 */
  viewCount: number
  /** 累计阅读时长（秒） */
  totalDuration: number
  /** 最后阅读时间 */
  lastViewTime?: string
}

/**
 * 学生章节可展开详情结果 VO
 */
export interface StudentChapterDetailResultVO {
  /** 详情类型（resources/exercises/mastery） */
  detailType: 'resources' | 'exercises' | 'mastery'
  /** 详情列表 */
  items: StudentChapterResourceDetailVO[] | StudentChapterExerciseDetailVO[] | StudentChapterMasteryDetailVO[]
  /** 总数 */
  total: number
}
