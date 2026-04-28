<template>
  <div class="resource-manage-page">
    <a-page-header title="资源管理" :sub-title="loading ? '加载中...' : `共 ${totalCount} 个资源`">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="filterType"
            placeholder="资源类型"
            allow-clear
            style="width: 130px"
            @change="applyFilter"
          >
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="text">文本</a-select-option>
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="audio">音频</a-select-option>
          </a-select>
          <a-button @click="loadAll">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="page-content">
      <a-spin :spinning="loading">
        <template v-if="filteredGroups.length > 0">
          <a-collapse v-model:active-key="expandedChapters" :bordered="false">
            <a-collapse-panel
              v-for="group in filteredGroups"
              :key="group.chapterId"
              :header="`${group.chapterName}（${group.resources.length} 个资源）`"
            >
              <a-table :data-source="group.resources" :pagination="false" row-key="resourceId" size="small">
                <a-table-column key="resourceName" title="资源名称" data-index="resourceName" />
                <a-table-column key="resourceType" title="类型" data-index="resourceType" :width="100">
                  <template #default="{ record }">
                    <a-tag :color="getTypeColor(record.resourceType)">
                      {{ getTypeName(record.resourceType) }}
                    </a-tag>
                  </template>
                </a-table-column>
                <a-table-column key="isVisible" title="可见" data-index="isVisible" :width="80" align="center">
                  <template #default="{ record }">
                    <a-tag :color="record.isVisible === 'Y' ? 'green' : 'red'">
                      {{ record.isVisible === 'Y' ? '是' : '否' }}
                    </a-tag>
                  </template>
                </a-table-column>
                <a-table-column key="parseStatus" title="解析状态" data-index="parseStatus" :width="100" align="center">
                  <template #default="{ record }">
                    <DictTag :options="text_processing_status" :value="record.parseStatus || '0'" />
                  </template>
                </a-table-column>
                <a-table-column key="textProcess" title="文本化" :width="100" align="center">
                  <template #default="{ record }">
                    <a-button type="link" size="small" @click="openTextDrawer(record)">文本化操作</a-button>
                  </template>
                </a-table-column>
                <a-table-column key="resourceUrl" title="链接" :width="80" align="center">
                  <template #default="{ record }">
                    <a v-if="record.resourceUrl" :href="record.resourceUrl" target="_blank" rel="noopener">
                      <LinkOutlined />
                    </a>
                    <span v-else>-</span>
                  </template>
                </a-table-column>
              </a-table>
            </a-collapse-panel>
          </a-collapse>
        </template>

        <a-empty v-else-if="!loading" description="暂无资源数据" />
      </a-spin>

      <TextProcessDrawer v-model:visible="textDrawerVisible" :resource="activeResource" @success="loadAll" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { ReloadOutlined, LinkOutlined } from '@ant-design/icons-vue'
import DictTag from '@/components/dict/DictTag.vue'
import { useDict } from '@/utils/dict.ts'
import { getChapterTree, getChapterResources } from '@/api/education/chapter.ts'
import TextProcessDrawer from './components/TextProcessDrawer.vue'
import type { ChapterTreeVO } from '@/types/api/chapter.ts'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'

interface ResourceGroup {
  chapterId: number
  chapterName: string
  resources: ChapterResourceListVO[]
}

const route = useRoute()
const courseId = ref<number>(Number(route.params.courseId) || 0)

const loading = ref(false)
const groups = ref<ResourceGroup[]>([])
const filterType = ref<string | undefined>()
const expandedChapters = ref<number[]>([])
const textDrawerVisible = ref(false)
const activeResource = ref<ChapterResourceListVO | undefined>(undefined)
const { text_processing_status } = useDict('text_processing_status')

const filteredGroups = computed(() => {
  if (!filterType.value) return groups.value.filter((g) => g.resources.length > 0)
  return groups.value
    .map((g) => ({
      ...g,
      resources: g.resources.filter((r) => r.resourceType === filterType.value),
    }))
    .filter((g) => g.resources.length > 0)
})

const totalCount = computed(() => filteredGroups.value.reduce((s, g) => s + g.resources.length, 0))

// ── 平铺章节树 ─────────────────────────────────────────────────────────────
const flattenChapters = (nodes: ChapterTreeVO[]): ChapterTreeVO[] => {
  const result: ChapterTreeVO[] = []
  const walk = (list: ChapterTreeVO[]) => {
    for (const n of list) {
      result.push(n)
      if (n.children) walk(n.children)
    }
  }
  walk(nodes)
  return result
}

// ── 加载所有资源 ───────────────────────────────────────────────────────────
const loadAll = async () => {
  if (!courseId.value) return
  loading.value = true
  try {
    const treeRes = await getChapterTree(courseId.value)
    if (treeRes.code !== 200) return
    const chapters = flattenChapters(treeRes.data || [])

    // 并发拉取各章节资源
    const results = await Promise.allSettled(chapters.map((ch) => getChapterResources(ch.chapterId)))

    groups.value = chapters.map((ch, idx) => {
      const result = results[idx] as any
      const resources = result?.status === 'fulfilled' && result?.value?.code === 200 ? result?.value?.data || [] : []
      return { chapterId: ch.chapterId, chapterName: ch.chapterName, resources }
    })

    // 默认展开有资源的章节
    expandedChapters.value = groups.value.filter((g) => g.resources.length > 0).map((g) => g.chapterId)
  } catch (_e) {
    message.error('加载资源数据失败')
  } finally {
    loading.value = false
  }
}

const applyFilter = () => {
  // filterType 是响应式的，filteredGroups 自动重算
}

const getTypeColor = (type: string) =>
  ({
    video: 'blue',
    document: 'green',
    text: 'orange',
    image: 'purple',
    audio: 'cyan',
    archive: 'magenta',
    binary: 'volcano',
  })[type] || 'default'
const getTypeName = (type: string) =>
  ({
    video: '视频',
    document: '文档',
    text: '文本',
    image: '图片',
    audio: '音频',
    archive: '压缩包',
    binary: '二进制文件',
  })[type] || type

const openTextDrawer = (resource: ChapterResourceListVO) => {
  activeResource.value = resource
  textDrawerVisible.value = true
}

onMounted(() => {
  if (!courseId.value) {
    message.error('缺少课程ID参数')
    return
  }
  loadAll()
})
</script>

<style scoped>
.resource-manage-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.page-content {
  flex: 1;
  padding: 0 24px 24px;
  overflow-y: auto;
}
</style>
