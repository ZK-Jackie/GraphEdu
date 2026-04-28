import { type ComponentItemConfig, type LayoutConfig } from 'golden-layout'

/**
 * 教师课程设计初始布局配置
 * 默认打开课程首页
 */
export const buildInitConfig = (courseId: number | string): LayoutConfig => ({
  root: {
    type: 'row',
    content: [
      {
        type: 'component',
        title: '课程管理首页',
        header: { show: 'top' },
        isClosable: false,
        componentType: 'RouterTemplate',
        componentState: {
          path: `/course/manage/${courseId}`,
          name: 'TeacherCourseHome',
          meta: { title: '课程管理首页' },
        },
      } as ComponentItemConfig,
    ],
  },
})
