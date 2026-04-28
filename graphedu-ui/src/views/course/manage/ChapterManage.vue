<template>
  <div class="chapter-manage-page">
    <!-- 页面头部 -->
    <a-page-header title="章节管理" :sub-title="courseName">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="handleAddChapter">
            <template #icon><PlusOutlined /></template>
            新增章节
          </a-button>
          <a-button @click="loadChapterTree">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 主内容区域 -->
    <div class="chapter-content">
      <!-- 骨架屏 -->
      <div v-if="pageLoading" class="chapter-layout">
        <div class="chapter-sidebar">
          <a-card title="章节列表" :bordered="false">
            <a-skeleton active :paragraph="{ rows: 8 }" />
          </a-card>
        </div>
        <div class="chapter-main">
          <a-card :bordered="false">
            <a-skeleton active :paragraph="{ rows: 6 }" />
          </a-card>
        </div>
      </div>

      <!-- 真实内容 -->
      <div v-else class="chapter-layout">
        <!-- 左侧：章节树 -->
        <div class="chapter-sidebar">
          <a-card title="章节列表" :bordered="false">
            <a-tree
              v-if="chapterTree.length > 0"
              :tree-data="chapterTree as any"
              :field-names="{ key: 'chapterId', title: 'chapterName', children: 'children' } as any"
              :selected-keys="selectedChapterId ? [selectedChapterId] : []"
              show-line
              @select="handleSelectChapter"
            >
              <template #title="{ chapterName, status }">
                <span>
                  {{ chapterName }}
                  <a-tag v-if="status === '1'" color="orange" size="small" style="margin-left: 4px">停用</a-tag>
                </span>
              </template>
            </a-tree>
            <a-empty v-else description="暂无章节，请新增" />
          </a-card>
        </div>

        <!-- 右侧：章节详情 -->
        <div class="chapter-main">
          <a-card v-if="selectedChapter" :bordered="false">
            <template #title>{{ selectedChapter.chapterName }}</template>
            <template #extra>
              <a-space>
                <a-button size="small" @click="handleAddChildChapter">
                  <template #icon><PlusOutlined /></template>
                  新增子章节
                </a-button>
                <a-button size="small" @click="handleEditChapter">
                  <template #icon><EditOutlined /></template>
                  编辑
                </a-button>
                <a-button size="small" :loading="generatingDescription" @click="handleGenerateDescription">
                  <template #icon><ThunderboltOutlined /></template>
                  AI 生成描述
                </a-button>
                <a-button size="small" danger @click="handleDeleteChapter">
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-space>
            </template>

            <a-tabs v-model:active-key="activeTab">
              <!-- 基本信息 -->
              <a-tab-pane key="basic" tab="基本信息">
                <a-descriptions :column="2" bordered size="small">
                  <a-descriptions-item label="章节名称">
                    {{ selectedChapter.chapterName }}
                  </a-descriptions-item>
                  <a-descriptions-item label="章节序号">
                    {{ selectedChapter.chapterNo }}
                  </a-descriptions-item>
                  <a-descriptions-item label="父章节">
                    {{ getParentChapterName(selectedChapter.parentId) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="状态">
                    <a-tag :color="selectedChapter.status === '0' ? 'green' : 'orange'">
                      {{ selectedChapter.status === '0' ? '正常' : '停用' }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="资料数量">
                    {{ selectedChapter.contentCount }}
                  </a-descriptions-item>
                  <a-descriptions-item label="章节描述" :span="2">
                    <span style="white-space: pre-wrap">{{ selectedChapter.description || '-' }}</span>
                  </a-descriptions-item>
                </a-descriptions>
              </a-tab-pane>

              <!-- 资源管理 -->
              <a-tab-pane key="resources" tab="资源管理" force-render>
                <ResourceTab :chapter-id="selectedChapter.chapterId" />
              </a-tab-pane>

              <!-- 习题管理 -->
              <a-tab-pane key="exercise" tab="习题管理" force-render>
                <CourseExerciseTab :course-id="courseId" :chapter-id="selectedChapter.chapterId" />
              </a-tab-pane>

              <!-- 知识点关联 -->
              <a-tab-pane key="knowledge" tab="知识点关联">
                <div class="kp-toolbar">
                  <a-button size="small" @click="loadKnowledgePoints">
                    <template #icon><ReloadOutlined /></template>
                    刷新
                  </a-button>
                </div>
                <a-table
                  :data-source="knowledgePoints"
                  :loading="kpLoading"
                  :pagination="false"
                  row-key="nodeChapterId"
                  size="small"
                >
                  <template #emptyText>
                    <a-empty description="暂无关联知识点" />
                  </template>
                  <a-table-column key="nodeTitle" title="知识点名称" data-index="nodeTitle" />
                  <a-table-column
                    key="nodeImportance"
                    title="重要程度"
                    data-index="nodeImportance"
                    :width="100"
                    align="center"
                  >
                    <template #default="{ record }">
                      <a-rate :value="Number(record.nodeImportance)" disabled :count="5" style="font-size: 12px" />
                    </template>
                  </a-table-column>
                  <a-table-column key="nodeDescription" title="描述" data-index="nodeDescription" :ellipsis="true" />
                  <a-table-column key="action" title="操作" :width="80" align="center">
                    <template #default="{ record }">
                      <a-button type="link" size="small" danger @click="handleUnlinkKP(record)">取消关联</a-button>
                    </template>
                  </a-table-column>
                </a-table>
              </a-tab-pane>
            </a-tabs>
          </a-card>

          <a-card v-else :bordered="false">
            <a-empty description="请在左侧选择章节" />
          </a-card>
        </div>
      </div>
    </div>

    <!-- 章节表单弹窗 -->
    <a-modal
      v-model:open="formVisible"
      :title="formTitle"
      :confirm-loading="formLoading"
      @ok="handleSubmitForm"
      @cancel="formVisible = false"
    >
      <a-form :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="章节名称" required>
          <a-input v-model:value="form.chapterName" placeholder="请输入章节名称" />
        </a-form-item>
        <a-form-item label="父章节">
          <a-tree-select
            v-model:value="form.parentId"
            :tree-data="parentChapterOptions as any"
            :field-names="{ key: 'chapterId', value: 'chapterId', label: 'chapterName', children: 'children' } as any"
            placeholder="选择父章节（不选则为根章节）"
            allow-clear
            tree-default-expand-all
          />
        </a-form-item>
        <a-form-item label="章节序号">
          <a-input-number v-model:value="form.chapterNo" :min="0" placeholder="排序序号" style="width: 100%" />
        </a-form-item>
        <a-form-item label="章节描述">
          <a-textarea v-model:value="form.description" placeholder="章节描述（可选）" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import {
  getChapterTree,
  addChapter,
  updateChapter,
  deleteChapter,
  generateChapterDescription,
  getChapterKnowledgePoints,
  unlinkChapterKnowledgePoint,
} from '@/api/education/chapter.ts'
import ResourceTab from './components/ResourceTab.vue'
import CourseExerciseTab from './components/CourseExerciseTab.vue'
import type { ChapterCreateDTO, ChapterTreeVO, ChapterUpdateDTO } from '@/types/api/chapter.ts'
import type { KnowledgeNodeChapterDetailVO } from '@/types/api/education/knowledgeGraph.ts'

const route = useRoute()

const courseId = ref<number>(Number(route.params.courseId) || 0)
const courseName = ref<string>('')

// ── 页面加载状态 ──────────────────────────────────────────────────────────
const pageLoading = ref(true)

// ── 章节树 ──────────────────────────────────────────────────────────────────
const chapterTree = ref<ChapterTreeVO[]>([])
const selectedChapterId = ref<number | undefined>()
const selectedChapter = ref<ChapterTreeVO | undefined>()
const activeTab = ref('basic')
const generatingDescription = ref(false)

// ── 知识点 ─────────────────────────────────────────────────────────────────
const knowledgePoints = ref<KnowledgeNodeChapterDetailVO[]>([])
const kpLoading = ref(false)

// ── 表单 ──────────────────────────────────────────────────────────────────
const formVisible = ref(false)
const formLoading = ref(false)
const formTitle = ref('')
const isEdit = ref(false)
const form = ref<ChapterCreateDTO & { chapterId?: number }>({
  courseId: courseId.value,
  parentId: 0,
  chapterName: '',
  chapterNo: 0,
  description: '',
})

const parentChapterOptions = computed(() => [
  {
    chapterId: 0,
    chapterName: '根章节',
    parentId: 0,
    children: chapterTree.value,
  } as any,
])

// ── 加载章节树 ────────────────────────────────────────────────────────────
const loadChapterTree = async () => {
  try {
    const res = await getChapterTree(courseId.value)
    if (res.code === 200) {
      chapterTree.value = res.data || []
      // 如果有已选章节，更新引用
      if (selectedChapterId.value) {
        selectedChapter.value = findChapterById(chapterTree.value, selectedChapterId.value)
      }
    }
  } catch (_e) {
    message.error('加载章节树失败')
  }
}

const findChapterById = (nodes: ChapterTreeVO[], id: number): ChapterTreeVO | undefined => {
  for (const node of nodes) {
    if (node.chapterId === id) return node
    if (node.children) {
      const found = findChapterById(node.children, id)
      if (found) return found
    }
  }
}

const getParentChapterName = (parentId: number): string => {
  if (parentId === 0) return '根章节'
  const found = findChapterById(chapterTree.value, parentId)
  return found?.chapterName || '-'
}

// ── 章节选中 ──────────────────────────────────────────────────────────────
const handleSelectChapter = (selectedKeys: (string | number)[]) => {
  const chapterId = selectedKeys[0] as number
  if (!chapterId) return
  selectedChapterId.value = chapterId
  selectedChapter.value = findChapterById(chapterTree.value, chapterId)
  activeTab.value = 'basic'
  knowledgePoints.value = []
}

// ── 知识点操作 ────────────────────────────────────────────────────────────
const loadKnowledgePoints = async () => {
  if (!selectedChapter.value) return
  kpLoading.value = true
  try {
    const res = await getChapterKnowledgePoints(selectedChapter.value.chapterId)
    if (res.code === 200) {
      knowledgePoints.value = res.data || []
    }
  } catch (_e) {
    message.error('加载知识点关联失败')
  } finally {
    kpLoading.value = false
  }
}

const handleUnlinkKP = (record: KnowledgeNodeChapterDetailVO) => {
  Modal.confirm({
    title: '确认取消关联',
    content: `确定取消章节与知识点"${record.nodeTitle || record.nodeUuid}"的关联吗？`,
    onOk: async () => {
      try {
        const res = await unlinkChapterKnowledgePoint(record.chapterId, record.nodeUuid)
        if (res.code === 200) {
          message.success('取消关联成功')
          await loadKnowledgePoints()
        }
      } catch (_e) {
        message.error('取消关联失败')
      }
    },
  })
}

watch(activeTab, (newTab) => {
  if (newTab === 'knowledge' && selectedChapter.value) {
    loadKnowledgePoints()
  }
})

// ── 新增/编辑章节 ─────────────────────────────────────────────────────────
const handleAddChapter = () => {
  formTitle.value = '新增章节'
  isEdit.value = false
  form.value = { courseId: courseId.value, parentId: 0, chapterName: '', chapterNo: 0, description: '' }
  formVisible.value = true
}

const handleAddChildChapter = () => {
  if (!selectedChapter.value) return
  formTitle.value = '新增子章节'
  isEdit.value = false
  form.value = {
    courseId: courseId.value,
    parentId: selectedChapter.value.chapterId,
    chapterName: '',
    chapterNo: 0,
    description: '',
  }
  formVisible.value = true
}

const handleEditChapter = () => {
  if (!selectedChapter.value) return
  formTitle.value = '编辑章节'
  isEdit.value = true
  form.value = {
    chapterId: selectedChapter.value.chapterId,
    courseId: courseId.value,
    parentId: selectedChapter.value.parentId,
    chapterName: selectedChapter.value.chapterName,
    chapterNo: selectedChapter.value.chapterNo,
    description: selectedChapter.value.description || '',
  }
  formVisible.value = true
}

const handleDeleteChapter = () => {
  if (!selectedChapter.value) return
  Modal.confirm({
    title: '确认删除',
    content: `确定删除章节"${selectedChapter.value.chapterName}"吗？此操作不可撤销。`,
    onOk: async () => {
      try {
        const res = await deleteChapter(String(selectedChapter.value!.chapterId))
        if (res.code === 200) {
          message.success('删除成功')
          selectedChapterId.value = undefined
          selectedChapter.value = undefined
          activeTab.value = 'basic'
          await loadChapterTree()
        }
      } catch (_e) {
        message.error('删除失败')
      }
    },
  })
}

const handleGenerateDescription = async () => {
  if (!selectedChapter.value) return
  generatingDescription.value = true
  try {
    const { data } = await generateChapterDescription(selectedChapter.value.chapterId)
    if (data?.description) {
      selectedChapter.value.description = data.description
      message.success('章节描述已生成')
    }
  } catch (err: any) {
    message.error(err?.message || '生成失败，请确认已完成 GraphRAG 索引构建')
  } finally {
    generatingDescription.value = false
  }
}

const handleSubmitForm = async () => {
  if (!form.value.chapterName.trim()) {
    message.warning('请输入章节名称')
    return
  }
  formLoading.value = true
  try {
    if (isEdit.value) {
      const updateData: ChapterUpdateDTO = {
        chapterId: form.value.chapterId!,
        parentId: form.value.parentId,
        chapterName: form.value.chapterName,
        chapterNo: form.value.chapterNo,
        description: form.value.description,
      }
      const res = await updateChapter(updateData)
      if (res.code === 200) message.success('更新成功')
    } else {
      const res = await addChapter(form.value)
      if (res.code === 200) message.success('新增成功')
    }
    formVisible.value = false
    await loadChapterTree()
  } catch (_e) {
    message.error(isEdit.value ? '更新失败' : '新增失败')
  } finally {
    formLoading.value = false
  }
}

onMounted(async () => {
  if (!courseId.value) {
    message.error('缺少课程ID参数')
    return
  }
  await loadChapterTree()
  pageLoading.value = false
})
</script>

<style scoped>
.chapter-manage-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

:deep(.ant-page-header) {
  padding: 8px 24px;
}

.chapter-content {
  flex: 1;
  padding: 0 24px 24px;
  overflow: hidden;
}

.chapter-layout {
  display: flex;
  height: 100%;
  gap: 16px;
}

.chapter-sidebar {
  width: 280px;
  flex-shrink: 0;
  overflow: auto;
}

.chapter-main {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}

.kp-toolbar {
  margin-bottom: 12px;
}
</style>
