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
      :scroll="{ y: 400 }"
    >
      <a-table-column key="sort" title="序号" :width="80" align="center">
        <template #default="{ index }">{{ index + 1 }}</template>
      </a-table-column>
      <a-table-column key="resourceName" title="资源名称" data-index="resourceName" />
      <a-table-column key="resourceType" title="资源类型" data-index="resourceType" :width="120">
        <template #default="{ record }">
          <a-tag :color="getResourceTypeColor(record.resourceType)">
            {{ getResourceTypeName(record.resourceType) }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="isVisible" title="可见性" data-index="isVisible" :width="100" align="center">
        <template #default="{ record }">
          <a-tag :color="record.isVisible === 'Y' ? 'green' : 'red'">
            {{ record.isVisible === 'Y' ? '可见' : '隐藏' }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="status" title="状态" data-index="status" :width="100" align="center">
        <template #default="{ record }">
          <a-tag :color="record.status === '0' ? 'green' : 'orange'">
            {{ record.status === '0' ? '正常' : '停用' }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="action" title="操作" :width="180" align="center" fixed="right">
        <template #default="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="handleEditResource(record)"> 编辑 </a-button>
            <a-button type="link" size="small" danger @click="handleDeleteResource(record)"> 删除 </a-button>
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
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { getChapterResources, deleteChapterResources } from '@/api/education/chapter.ts'
import ResourceForm from './ResourceForm.vue'

interface Props {
  chapterId: number
}

interface ResourceVO {
  resourceId: number
  chapterId: number
  resourceName: string
  resourceType: string
  resourceUrl?: string
  isVisible: string
  status: string
  displayOrder?: number
}

const props = defineProps<Props>()

const loading = ref(false)
const resources = ref<ResourceVO[]>([])
const formVisible = ref(false)
const editingResource = ref<ResourceVO | undefined>(undefined)

// 分页配置
const pagination = computed(() => ({
  pageSize: 10,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`,
}))

// 加载资源列表
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

// 添加资源
const handleAddResource = () => {
  editingResource.value = undefined
  formVisible.value = true
}

// 编辑资源
const handleEditResource = (resource: ResourceVO) => {
  editingResource.value = resource
  formVisible.value = true
}

// 删除资源
const handleDeleteResource = (resource: ResourceVO) => {
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

// 表单成功回调
const handleFormSuccess = () => {
  loadResources()
}

// 获取资源类型颜色
const getResourceTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    video: 'blue',
    document: 'green',
    text: 'orange',
    image: 'purple',
    audio: 'cyan',
  }
  return colors[type] || 'default'
}

// 获取资源类型名称
const getResourceTypeName = (type: string) => {
  const names: Record<string, string> = {
    video: '视频',
    document: '文档',
    text: '文本',
    image: '图片',
    audio: '音频',
  }
  return names[type] || type
}

// 监听 chapterId 变化
watch(
  () => props.chapterId,
  (newId) => {
    if (newId) {
      loadResources()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.resource-tab {
  width: 100%;
}

.toolbar {
  margin-bottom: 16px;
}
</style>
