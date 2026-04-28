import { type ComponentItemConfig, type LayoutConfig } from 'golden-layout'

/**
 * 课程学习初始布局配置
 * @param courseId 课程 ID，用于构造正确的子路由路径
 */
export const buildInitConfig = (courseId: number | string): LayoutConfig => ({
  root: {
    type: 'row',
    content: [
      {
        type: 'component',
        title: '课程详情首页',
        header: { show: 'top' },
        isClosable: false,
        componentType: 'RouterTemplate',
        componentState: {
          path: `/course/learn/${courseId}`,
          name: 'StudentCourseHome',
          meta: { title: '课程详情首页' },
        },
      } as ComponentItemConfig,
    ],
  },
})
