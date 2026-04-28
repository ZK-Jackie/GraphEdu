<template>
  <div class="resource-tab">
    <!-- 操作栏 -->
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="handleAddResource">
          <template #icon><PlusOutlined /></template>
          添加资源
        </a-button>
        <a-button @click="loadResources">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </a-space>
    </div>

    <!-- 资源列表 -->
    <a-table
      :data-source="resources"
      :loading="loading"
      :pagination="pagination"
      row-key="resourceId"
      :scroll="{ x: 900, y: 'calc(100vh - 420px)' }"
    >
      <a-table-column key="sort" title="序号" :width="60" align="center" fixed="left" />
      <a-table-column
        key="resourceName"
        title="资源名称"
        data-index="resourceName"
        :ellipsis="true"
        :custom-render="
          ({ record }: { record: unknown }) =>
            h(ResourceNameCell, { record: record as ChapterResourceListVO, onDownload: handleDownloadResource })
        "
      />
      <a-table-column key="resourceType" title="类型" data-index="resourceType" :width="90" align="center">
        <template #default="{ record }">
          <a-tag :color="getResourceTypeColor(record.resourceType)">
            {{ getResourceTypeName(record.resourceType) }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="isVisible" title="可见" data-index="isVisible" :width="70" align="center">
        <template #default="{ record }">
          <a-tag :color="record.isVisible === 'Y' ? 'green' : 'red'">
            {{ record.isVisible === 'Y' ? '可见' : '隐藏' }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="parseStatus" title="解析状态" data-index="parseStatus" :width="100" align="center">
        <template #default="{ record }">
          <DictTag :options="text_processing_status" :value="record.parseStatus || '0'" />
        </template>
      </a-table-column>
      <a-table-column key="status" title="状态" data-index="status" :width="70" align="center">
        <template #default="{ record }">
          <a-tag :color="record.status === '0' ? 'green' : 'orange'">
            {{ record.status === '0' ? '正常' : '停用' }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="action" title="操作" :width="180" align="center" fixed="right">
        <template #default="{ record }">
          <a-space :size="0">
            <a-button type="link" size="small" @click="openTextProcessDrawer(record)">文本化</a-button>
            <a-button type="link" size="small" @click="handleEditResource(record)">编辑</a-button>
            <a-button type="link" size="small" danger @click="handleDeleteResource(record)">删除</a-button>
          </a-space>
        </template>
      </a-table-column>
    </a-table>

    <!-- 资源表单对话框 -->
    <ResourceForm
      v-model:visible="formVisible"
      :chapter-id="chapterId"
      :resource="editingResource"
      @success="handleFormSuccess"
    />

    <TextProcessDrawer v-model:visible="textDrawerVisible" :resource="activeResource" @success="loadResources" />
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { getChapterResources, deleteChapterResources } from '@/api/education/chapter.ts'
import { downloadFile } from '@/api/system/upload.ts'
import DictTag from '@/components/dict/DictTag.vue'
import { useDict } from '@/utils/dict.ts'
import ResourceForm from './ResourceForm.vue'
import TextProcessDrawer from './TextProcessDrawer.vue'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'

const ResourceNameCell = defineComponent({
  name: 'ResourceNameCell',
  props: {
    record: { type: Object as PropType<ChapterResourceListVO>, required: true },
  },
  emits: ['download'],
  setup(props, { emit }) {
    return () => {
      const { record } = props
      const name = record.resourceName
      if (record.fileId || record.resourceUrl) {
        return h('a', { class: 'resource-link', onClick: () => emit('download', record) }, name)
      }
      return h('span', null, name)
    }
  },
})

interface Props {
  chapterId: number
}

const props = defineProps<Props>()

const loading = ref(false)
const resources = ref<ChapterResourceListVO[]>([])
const formVisible = ref(false)
const editingResource = ref<ChapterResourceListVO | undefined>(undefined)
const textDrawerVisible = ref(false)
const activeResource = ref<ChapterResourceListVO | undefined>(undefined)
const { text_processing_status } = useDict('text_processing_status')

const pagination = computed(() => ({
  pageSize: 10,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`,
}))

const loadResources = async () => {
  if (!props.chapterId) return
  loading.value = true
  try {
    const res = await getChapterResources(props.chapterId)
    if (res.code === 200) {
      resources.value = res.data || []
    }
  } catch (_e) {
    message.error('加载资源列表失败')
  } finally {
    loading.value = false
  }
}

const handleAddResource = () => {
  editingResource.value = undefined
  formVisible.value = true
}

const handleEditResource = (resource: ChapterResourceListVO) => {
  editingResource.value = resource
  formVisible.value = true
}

const handleDeleteResource = (resource: ChapterResourceListVO) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除资源"${resource.resourceName}"吗？`,
    onOk: async () => {
      try {
        const res = await deleteChapterResources(props.chapterId, String(resource.resourceId))
        if (res.code === 200) {
          message.success('删除成功')
          await loadResources()
        }
      } catch (_e) {
        message.error('删除失败')
      }
    },
  })
}

const openTextProcessDrawer = (resource: ChapterResourceListVO) => {
  activeResource.value = resource
  textDrawerVisible.value = true
}

const handleFormSuccess = () => {
  loadResources()
}

const handleDownloadResource = async (resource: ChapterResourceListVO) => {
  if (resource.fileId) {
    try {
      const res = await downloadFile(resource.fileId)
      if (res.code === 200 && res.data) {
        // 优先使用 downloadUrl，否则使用 fileUrl
        const url = res.data.downloadUrl || res.data.fileUrl
        if (url) {
          window.open(url, '_blank')
        } else {
          message.warning('未获取到下载链接')
        }
      }
    } catch (_e) {
      message.error('获取下载链接失败')
    }
  } else if (resource.resourceUrl) {
    window.open(resource.resourceUrl, '_blank')
  } else {
    message.warning('该资源无可下载内容')
  }
}

const getResourceTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    video: 'blue',
    document: 'green',
    text: 'orange',
    image: 'purple',
    audio: 'cyan',
    archive: 'magenta',
    binary: 'volcano',
  }
  return colors[type] || 'default'
}

const getResourceTypeName = (type: string) => {
  const names: Record<string, string> = {
    video: '视频',
    document: '文档',
    text: '文本',
    image: '图片',
    audio: '音频',
    archive: '压缩包',
    binary: '二进制文件',
  }
  return names[type] || type
}

watch(
  () => props.chapterId,
  (newId) => {
    if (newId) loadResources()
  },
  { immediate: true }
)
</script>

<style scoped>
.resource-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  flex-shrink: 0;
  margin-bottom: 16px;
}

.resource-link {
  color: var(--ge-primary);
  cursor: pointer;
}

.resource-link:hover {
  text-decoration: underline;
}

.resource-tab :deep(.ant-table-cell) {
  padding-inline: 12px !important;
}
</style>
