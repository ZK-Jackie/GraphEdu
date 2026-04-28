/**
 * Layout 导出文件
 *
 * 提供布局方案：
 * 1. WorkbenchLayout - 工作台布局（包含顶部导航、侧边栏和 Golden Layout 内容区）
 * 2. CommonLayout - 通用布局（顶部导航栏 + 路由页面 + Footer）
 * 3. CourseLearningLayout - 课程学习布局（左侧课程信息 + 右侧学习内容区）
 * 4. CourseTeachingLayout - 教师课程工作台布局（左侧功能菜单 + 右侧内容区）
 */

export { default as WorkbenchLayout } from './WorkbenchLayout/index.vue'
export { default as CommonLayout } from './CommonLayout/index.vue'
export { default as StudentCourseLayout } from './StudentCourseLayout/index.vue'
export { default as TeacherCourseLayout } from './TeacherCourseLayout/index.vue'
