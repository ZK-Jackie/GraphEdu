<template>
  <div class="chapter-manage-page">
    <!-- 页面头部 -->
    <a-page-header :title="courseName" @back="handleBack">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="handleAddChapter">
            <template #icon><PlusOutlined /></template>
            {{ t('education.chapter.addChapter') }}
          </a-button>
          <a-button @click="loadChapterTree">
            <template #icon><ReloadOutlined /></template>
            {{ t('common.refresh') }}
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 主内容区域 -->
    <div class="chapter-content">
      <a-row :gutter="16">
        <!-- 左侧：章节树 -->
        <a-col :span="8">
          <a-card :title="t('education.chapter.chapterManage')" :bordered="false">
            <a-tree
              v-if="chapterTree.length > 0"
              :tree-data="chapterTree as any"
              :field-names="({ value: 'chapterId', title: 'chapterName', children: 'children' }) as any"
              :selected-keys="[selectedChapterId as any]"
              show-line
              @select="handleSelectChapter"
            >
              <template #title="{ chapterName, status }">
                <span>
                  <span class="chapter-name">{{ chapterName }}</span>
                  <a-tag v-if="status === '1'" color="orange" size="small" style="margin-left: 8px">
                    {{ t('common.disabled') }}
                  </a-tag>
                </span>
              </template>
            </a-tree>
            <a-empty v-else :description="t('education.chapter.noChapters')" />
          </a-card>
        </a-col>

        <!-- 右侧：章节详情和操作 -->
        <a-col :span="16">
          <a-card v-if="selectedChapter" :bordered="false">
            <template #title>
              <span>{{ selectedChapter.chapterName }}</span>
            </template>
            <template #extra>
              <a-space>
                <a-button size="small" @click="handleAddChildChapter">
                  <template #icon><PlusOutlined /></template>
                  新增子章节
                </a-button>
                <a-button size="small" @click="handleEditChapter">
                  <template #icon><EditOutlined /></template>
                  {{ t('common.edit') }}
                </a-button>
                <a-button size="small" :loading="generatingDescription" @click="handleGenerateDescription">
                  <template #icon><ThunderboltOutlined /></template>
                  生成描述
                </a-button>
                <a-button size="small" danger @click="handleDeleteChapter">
                  <template #icon><DeleteOutlined /></template>
                  {{ t('common.delete') }}
                </a-button>
              </a-space>
            </template>

            <!-- 标签页 -->
            <a-tabs v-model:active-key="activeTab">
              <!-- 基本信息标签页 -->
              <a-tab-pane key="basic" tab="基本信息">
                <a-descriptions :column="2" bordered>
                  <a-descriptions-item :label="t('education.chapter.chapterName')">
                    {{ selectedChapter.chapterName }}
                  </a-descriptions-item>
                  <a-descriptions-item :label="t('education.chapter.chapterNo')">
                    {{ selectedChapter.chapterNo }}
                  </a-descriptions-item>
                  <a-descriptions-item :label="t('education.chapter.parentChapter')">
                    {{ getParentChapterName(selectedChapter.parentId) }}
                  </a-descriptions-item>
                  <a-descriptions-item :label="t('common.status')">
                    <a-tag v-if="selectedChapter.status === '0'" color="green">
                      {{ t('common.normal') }}
                    </a-tag>
                    <a-tag v-else color="orange">
                      {{ t('common.disabled') }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item :label="t('education.chapter.description')" :span="2">
                    {{ selectedChapter.description || '-' }}
                  </a-descriptions-item>
                </a-descriptions>
              </a-tab-pane>

              <!-- 知识点标签页 -->
              <a-tab-pane key="knowledge" tab="知识点" force-render>
                <KnowledgePointTab :chapter-id="selectedChapter.chapterId" />
              </a-tab-pane>

              <!-- 资源标签页 -->
              <a-tab-pane key="resources" tab="资源" force-render>
                <ResourceTab :chapter-id="selectedChapter.chapterId" />
              </a-tab-pane>
            </a-tabs>
          </a-card>
          <a-card v-else :bordered="false">
            <a-empty :description="t('common.pleaseSelect')" />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 章节表单弹窗 -->
    <a-modal v-model:open="formVisible" :title="formTitle" @ok="handleSubmitForm" @cancel="formVisible = false">
      <a-form :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item :label="t('education.chapter.chapterName')" required>
          <a-input v-model:value="form.chapterName" :placeholder="t('education.chapter.chapterNamePlaceholder')" />
        </a-form-item>
        <a-form-item :label="t('education.chapter.parentChapter')">
          <a-tree-select
            v-model:value="form.parentId"
            :tree-data="parentChapterOptions as any"
            :field-names="({ key: 'chapterId', value: 'chapterId', label: 'chapterName', children: 'children' }) as any"
            :placeholder="t('education.chapter.parentChapterPlaceholder')"
            allow-clear
            tree-default-expand-all
          />
        </a-form-item>
        <a-form-item :label="t('education.chapter.chapterNo')">
          <a-input-number
            v-model:value="form.chapterNo"
            :min="0"
            :placeholder="t('education.chapter.chapterNoPlaceholder')"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item :label="t('education.chapter.description')">
          <a-textarea
            v-model:value="form.description"
            :placeholder="t('education.chapter.descriptionPlaceholder')"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import {
  getChapterTree,
  addChapter,
  updateChapter,
  deleteChapter,
  generateChapterDescription,
} from '@/api/education/chapter.ts'
import KnowledgePointTab from './components/KnowledgePointTab.vue'
import ResourceTab from './components/ResourceTab.vue'
import type { ChapterCreateDTO, ChapterTreeVO, ChapterUpdateDTO } from '@/types/api/chapter.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

// 获取路由参数
const courseId = ref<number>(Number(route.query.courseId) || 0)
const courseName = ref<string>(String(route.query.courseName || ''))

// 章节树数据
const chapterTree = ref<ChapterTreeVO[]>([])
const selectedChapterId = ref<number>()
const selectedChapter = ref<ChapterTreeVO>()

/** 当前激活的标签页 */
const activeTab = ref('basic')
/** 正在生成描述 */
const generatingDescription = ref(false)

// 表单状态
const formVisible = ref(false)
const formTitle = ref('')
const isEdit = ref(false)
const form = ref<ChapterCreateDTO & { chapterId?: number }>({
  courseId: courseId.value,
  parentId: 0,
  chapterName: '',
  chapterNo: 0,
  description: '',
})

// 父章节选项（用于新增/编辑时选择）
const parentChapterOptions = computed(() => {
  const options = [
    { chapterId: 0, chapterName: t('education.chapter.rootChapter'), parentId: 0, children: [] as any[] },
  ]
  options[0]!.children = chapterTree.value
  return options
})

// 获取章节树
const loadChapterTree = async () => {
  try {
    const res = await getChapterTree(courseId.value)
    if (res.code === 200) {
      chapterTree.value = res.data || []
    }
  } catch (_e) {
    message.error(t('education.chapter.getChapterTreeFailed'))
  }
}

// 选择章节
const handleSelectChapter = (selectedKeys: (string | number)[], info: any) => {
  const chapterId = selectedKeys[0] as number
  selectedChapterId.value = chapterId

  // 查找选中的章节
  const findChapter = (nodes: ChapterTreeVO[]): ChapterTreeVO | undefined => {
    for (const node of nodes) {
      if (node.chapterId === chapterId) {
        return node
      }
      if (node.children) {
        const found = findChapter(node.children)
        if (found) return found
      }
    }
  }

  selectedChapter.value = findChapter(chapterTree.value)

  // 重置标签页到基本信息
  activeTab.value = 'basic'
}

// 新增章节
const handleAddChapter = () => {
  formTitle.value = t('education.chapter.addChapter')
  isEdit.value = false
  form.value = {
    courseId: courseId.value,
    parentId: 0,
    chapterName: '',
    chapterNo: 0,
    description: '',
  }
  formVisible.value = true
}

// 新增子章节
const handleAddChildChapter = () => {
  if (!selectedChapter.value) return

  formTitle.value = t('education.chapter.addChapter')
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

// 编辑章节
const handleEditChapter = () => {
  if (!selectedChapter.value) return

  formTitle.value = t('education.chapter.editChapter')
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

// 删除章节
const handleDeleteChapter = () => {
  if (!selectedChapter.value) return

  Modal.confirm({
    title: t('common.systemTip'),
    content: t('education.chapter.deleteChapterConfirm', { chapterName: selectedChapter.value.chapterName }),
    onOk: async () => {
      try {
        const res = await deleteChapter(String(selectedChapter.value!.chapterId))
        if (res.code === 200) {
          message.success(t('common.deleteSuccess'))
          selectedChapterId.value = undefined
          selectedChapter.value = undefined
          activeTab.value = 'basic'
          await loadChapterTree()
        }
      } catch (_e) {
        message.error(t('common.deleteFailed'))
      }
    },
  })
}

// 生成章节描述（AI 驱动，直接返回结果）
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
    message.error(err?.message || '生成失败，请确认已完成 GraphRAG 索引构建。')
  } finally {
    generatingDescription.value = false
  }
}

// 提交表单
const handleSubmitForm = async () => {
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
      if (res.code === 200) {
        message.success(t('common.updateSuccess'))
      }
    } else {
      const res = await addChapter(form.value)
      if (res.code === 200) {
        message.success(t('common.addSuccess'))
      }
    }

    formVisible.value = false
    await loadChapterTree()
  } catch (_e) {
    message.error(isEdit.value ? t('common.updateFailed') : t('common.addFailed'))
  }
}

// 获取父章节名称
const getParentChapterName = (parentId: number) => {
  if (parentId === 0) {
    return t('education.chapter.rootChapter')
  }

  const findChapter = (nodes: ChapterTreeVO[], id: number): ChapterTreeVO | undefined => {
    for (const node of nodes) {
      if (node.chapterId === id) {
        return node
      }
      if (node.children) {
        const found = findChapter(node.children, id)
        if (found) return found
      }
    }
  }

  const parent = findChapter(chapterTree.value, parentId)
  return parent?.chapterName || '-'
}

// 返回
const handleBack = () => {
  router.back()
}

// 初始化
onMounted(() => {
  if (!courseId.value) {
    message.error('缺少课程ID参数')
    handleBack()
    return
  }
  loadChapterTree()
})
</script>

<style scoped>
.chapter-manage-page {
  padding: 16px;
}

.chapter-content {
  margin-top: 16px;
}

.chapter-name {
  font-size: 14px;
}

.content-list {
  margin-top: 16px;
}

.content-list h4 {
  margin-bottom: 12px;
}
</style>
