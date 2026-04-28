/**
 * GraphRAG 任务查询 DTO
 */
export interface GraphRAGTaskQueryDTO {
  /** 任务ID */
  taskId?: number
  /** 关联课程ID */
  courseId?: number
  /** 任务状态（pending待处理/processing处理中/success成功/failed失败） */
  taskStatus?: 'pending' | 'processing' | 'success' | 'failed'
  /** 任务类型（如：graphrag_build构建、graphrag_update更新等） */
  taskType?: string
  /** 创建开始时间 */
  beginTime?: string
  /** 创建结束时间 */
  endTime?: string
  /** 当前页码 */
  page?: number
  /** 每页数量 */
  size?: number
  /** 页码（兼容） */
  pageNum?: number
  /** 每页数量（兼容） */
  pageSize?: number
}

/**
 * 创建 GraphRAG 任务 DTO
 */
export interface GraphRAGTaskCreateDTO {
  /** 关联课程ID */
  courseId: number
  /** 处理的文档ID列表 */
  resourceIds: number[]
  /** 任务类型（如：graphrag_build构建、graphrag_update更新等） */
  taskType: string
  /** 涉及的实体类型列表（可选） */
  entityTypes?: string[]
  /** 使用的提示词模板（可选） */
  promptTemplate?: string
  /** 自定义提示词模板（可选） */
  customPromptTemplate?: Record<string, any>
}

/**
 * 更新 GraphRAG 任务 DTO
 */
export interface GraphRAGTaskUpdateDTO {
  /** 任务ID */
  taskId: number
  /** 任务状态（pending待处理/processing处理中/success成功/failed失败/cancelled已取消） */
  taskStatus?: 'pending' | 'processing' | 'success' | 'failed' | 'cancelled'
  /** 任务最后信息（如果任务失败，记录错误详情） */
  taskMessage?: string
  /** 涉及的实体类型列表（可选） */
  entityTypes?: string[]
  /** 使用的提示词模板（可选） */
  promptTemplate?: string
  /** 自定义提示词模板（可选） */
  customPromptTemplate?: Record<string, any>
  /** 任务统计信息（JSONB格式，可选） */
  stats?: Record<string, any>
  /** 任务开始时间 */
  startTime?: string
  /** 任务结束时间 */
  endTime?: string
}

/**
 * GraphRAG 任务详细信息 VO
 */
export interface GraphRAGTaskDetailVO {
  /** 任务ID */
  taskId: number
  /** 关联课程ID */
  courseId: number
  /** 处理的文档ID列表（JSONB数组） */
  resourceIds: number[]
  /** 任务状态（pending待处理/processing处理中/success成功/failed失败） */
  taskStatus: string
  /** 任务类型（如：graphrag_build构建、graphrag_update更新等） */
  taskType: string
  /** 任务最后信息（如果任务失败，记录错误详情） */
  taskMessage?: string
  /** 涉及的实体类型列表（JSONB数组，对照知识图谱中的实体类型） */
  entityTypes?: string[]
  /** 使用的提示词模板（从 default/en default/zh edu/en edu/zh中选择） */
  promptTemplate?: string
  /** 自定义提示词模板（JSONB格式，允许用户覆盖默认模板中的某些部分） */
  customPromptTemplate?: Record<string, any>
  /** 任务统计信息（JSONB格式，包含处理的文档数量、提取的实体数量、构建的关系数量等） */
  stats?: Record<string, any>
  /** 任务开始时间 */
  startTime?: string
  /** 任务结束时间 */
  endTime?: string
  /** 是否启用（Y是 N否） */
  enabled: string
  /** 任务记录状态，对照 sys_data_status（0正常 1停用 2已删除） */
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
 * GraphRAG 任务列表项 VO
 */
export interface GraphRAGTaskListVO {
  /** 任务ID */
  taskId: number
  /** 关联课程ID */
  courseId: number
  /** 处理的文档ID列表（JSONB数组） */
  resourceIds: number[]
  /** 任务状态（pending待处理/processing处理中/success成功/failed失败） */
  taskStatus: string
  /** 任务类型 */
  taskType: string
  /** 任务最后信息（如果任务失败，记录错误详情） */
  taskMessage?: string
  /** 涉及的实体类型列表（JSONB数组） */
  entityTypes?: string[]
  /** 使用的提示词模板 */
  promptTemplate?: string
  /** 任务统计信息（JSONB格式） */
  stats?: Record<string, any>
  /** 任务开始时间 */
  startTime?: string
  /** 任务结束时间 */
  endTime?: string
  /** 是否启用（Y是 N否） */
  enabled: string
  /** 创建时间 */
  createTime?: string
}

/**
 * 可构建 GraphRAG 的资源查询 DTO
 */
export interface GraphRAGResourceQueryDTO {
  /** 课程ID */
  courseId: number
  /** 文本化状态（固定为 '2'，用于文档类型资源） */
  parseStatus: '2'
  /** 是否包含 text 类型直通资源（无需文本化） */
  includeTextDirectly?: boolean
  /** 资源名称模糊搜索 */
  resourceName?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * GraphRAG 索引构建请求 DTO
 */
export interface GraphRAGBuildCreateDTO {
  /** 课程ID */
  courseId: number
  /** 资源ID列表 */
  resourceIds: number[]
  /** 实体类型列表（预设选项：概念、原理、方法、公式、例题、定义、定理等，支持自定义） */
  entityTypes: string[]
  /** 提示词模板（default/en、default/zh、edu/en、edu/zh） */
  promptTemplate?: 'default/en' | 'default/zh' | 'edu/en' | 'edu/zh'
}

/**
 * GraphRAG 构建进度 VO（从 Redis 获取）
 */
export interface GraphRAGBuildProgressVO {
  /** 任务ID */
  taskId: number
  /** 任务状态 */
  taskStatus: string
  /** 当前步骤描述 */
  currentStep?: string
  /** 进度百分比（0-100） */
  progressPercent: number
  /** 统计信息 */
  stats?: Record<string, any>
  /** 开始时间 */
  startTime?: string
  /** 预计结束时间 */
  estimatedEndTime?: string
}
