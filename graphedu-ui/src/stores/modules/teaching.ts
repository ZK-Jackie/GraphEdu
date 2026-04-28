/**
 * Teaching Store - 教师工作台状态管理
 *
 * 管理教师工作台相关的状态，包括课程信息、章节树、知识图谱等
 */
import { defineStore } from 'pinia'
import type { KnowledgeGraphDetailVO } from '@/types/api/knowledge-graph'
import type { CourseDetailVO } from '@/types/api/education/course.ts'
import type { ChapterTreeVO } from '@/types/api/chapter.ts'

export const useTeachingStore = defineStore('teaching', () => {
  // 状态
  const currentCourse = ref<CourseDetailVO | null>(null)
  const chapters = ref<ChapterTreeVO[]>([])
  const knowledgeGraph = ref<KnowledgeGraphDetailVO | null>(null)
  const selectedChapter = ref<ChapterTreeVO | null>(null)
  const selectedChapterId = ref<number | null>(null)
  const graphGenerating = ref(false)

  // 计算属性
  const hasGraph = computed(() => !!knowledgeGraph.value)
  const chapterCount = computed(() => {
    const countNodes = (nodes: ChapterTreeVO[]): number => {
      let count = 0
      nodes.forEach((node) => {
        count += 1
        if (node.children?.length) {
          count += countNodes(node.children)
        }
      })
      return count
    }
    return countNodes(chapters.value)
  })

  // 总内容数
  const totalContentCount = computed(() => {
    const sumContent = (nodes: ChapterTreeVO[]): number => {
      let sum = 0
      nodes.forEach((node) => {
        sum += node.contentCount || 0
        if (node.children?.length) {
          sum += sumContent(node.children)
        }
      })
      return sum
    }
    return sumContent(chapters.value)
  })

  // 是否有章节内容
  const hasChapters = computed(() => chapters.value.length > 0)

  // 方法
  /**
   * 加载课程数据
   */
  const loadCourseData = async (courseId: number) => {
    try {
      const { getCourseDetail } = await import('@/api/education/course')
      const { data } = await getCourseDetail(courseId)
      if (data) {
        currentCourse.value = data
      }
      return data
    } catch (error) {
      console.error('[TeachingStore] 加载课程数据失败:', error)
      throw error
    }
  }

  /**
   * 加载章节树
   */
  const loadChapters = async (courseId: number) => {
    try {
      const { getChapterTree } = await import('@/api/education/chapter')
      const { data } = await getChapterTree(courseId)
      if (data) {
        chapters.value = data
      }
      return data
    } catch (error) {
      console.error('[TeachingStore] 加载章节树失败:', error)
      throw error
    }
  }

  /**
   * 加载知识图谱
   */
  const loadKnowledgeGraph = async (_courseId: number) => {
    try {
      // TODO: 实现加载知识图谱的 API 调用
      // 目前从课程的 books 关联中获取
      if ((currentCourse.value as any)?.books?.length) {
        // 假设第一个书籍关联了知识图谱
        const book = (currentCourse.value as any).books[0]
        if (book.knowledgeGraphs?.length) {
          knowledgeGraph.value = book.knowledgeGraphs[0]
        }
      }
      return knowledgeGraph.value
    } catch (error) {
      console.error('[TeachingStore] 加载知识图谱失败:', error)
      throw error
    }
  }

  /**
   * 生成知识图谱
   */
  const generateGraph = async (_skeleton: any) => {
    graphGenerating.value = true
    try {
      // TODO: 实现生成图谱的 API 调用
      await new Promise((resolve) => setTimeout(resolve, 1000))
      graphGenerating.value = false
    } catch (error) {
      console.error('[TeachingStore] 生成图谱失败:', error)
      graphGenerating.value = false
      throw error
    }
  }

  /**
   * 选择章节
   */
  const selectChapter = (chapter: ChapterTreeVO | null) => {
    selectedChapter.value = chapter
    selectedChapterId.value = chapter?.chapterId || null
  }

  /**
   * 通过ID查找章节
   */
  const findChapterById = (chapterId: number): ChapterTreeVO | null => {
    const find = (nodes: ChapterTreeVO[]): ChapterTreeVO | null => {
      for (const node of nodes) {
        if (node.chapterId === chapterId) return node
        if (node.children?.length) {
          const found = find(node.children)
          if (found) return found
        }
      }
      return null
    }
    return find(chapters.value)
  }

  /**
   * 重置状态
   */
  const resetState = () => {
    currentCourse.value = null
    chapters.value = []
    knowledgeGraph.value = null
    selectedChapter.value = null
    selectedChapterId.value = null
    graphGenerating.value = false
  }

  return {
    // 状态
    currentCourse,
    chapters,
    knowledgeGraph,
    selectedChapter,
    selectedChapterId,
    graphGenerating,

    // 计算属性
    hasGraph,
    chapterCount,
    totalContentCount,
    hasChapters,

    // 方法
    loadCourseData,
    loadChapters,
    loadKnowledgeGraph,
    generateGraph,
    selectChapter,
    findChapterById,
    resetState,
  }
})
