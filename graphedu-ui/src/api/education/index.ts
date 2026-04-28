/**
 * 教育模块 API 统一出口
 */
export * from './chapter'
export * from './chat'
export {
  getChapterResourceList,
  deleteChapterResource,
  changeResourceStatus,
  getChapterResourceDetail,
  getResourcesByChapter,
  reorderResources,
  submitParse,
  getParseStatus,
} from './chapterResource'
export * from './course'
export * from './courseExercise'
export * from './exerciseAttempt'
export * from './graphRagTask'
export * from './knowledge-graph'
export * from './learning-path'
export * from './resourceProgress'
export * from './student'
export * from './student_course'
export * from './teacher'
