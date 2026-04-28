/**
 * 课程详情 Mock 数据
 */
import type { CourseDetailVO } from '@/types/api/education/course'
import coverDiscrete from '@/assets/mock/discrete.jpeg'

export function getCourseDetail(): CourseDetailVO {
  return {
    courseId: 1,
    courseCode: 'MATH201',
    courseName: '离散数学',
    faculty: '数学与统计学院',
    description:
      '离散数学是计算机科学与技术专业的一门重要基础课程，主要研究离散量的结构及其相互关系，内容包括命题逻辑、谓词逻辑、集合论、二元关系、函数、图论、树和组合数学等。',
    coverUrl: coverDiscrete,
    category: '数学',
    difficultyLevel: '2',
    totalHours: 64,
    status: '0',
    isPublic: 'Y',
    studentCount: 32,
    viewCount: 156,
    tags: ['数学', '计算机基础', '逻辑推理'],
    courseOutline: '涵盖命题逻辑、谓词逻辑、集合论、二元关系、函数、图论、树、组合数学八大模块。',
    targetAudience: '计算机科学与技术、软件工程专业本科生',
    learningGoals: '掌握离散数学的基本概念、理论和方法，培养抽象思维和逻辑推理能力。',
    createTime: '2026-02-20T10:00:00Z',
  }
}
