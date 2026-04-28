<script setup lang="ts">
/**
 * SemanticGraphBuildDrawer - 统一的语义知识图谱抽屉
 *
 * 两种模式：
 *  - drawerMode = 'build'    → 三步引导构建流程（选择资源 → 配置参数 → 确认提交）
 *  - drawerMode = 'taskView' → 任务详情 + 进度跟踪（合并了原详情抽屉和进度视图）
 */
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlayCircleOutlined, StopOutlined, CheckOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import DictTag from '@/components/dict/DictTag.vue'
import { useDict } from '@/utils/dict.ts'
import {
  cancelGraphRAGTask,
  enableGraphRAGTask,
  deleteGraphRAGTask,
  getBuildableResources,
  getGraphRAGBuildProgress,
  submitGraphRAGBuild,
} from '@/api/education/graphragBuild.ts'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'
import type {
  GraphRAGBuildCreateDTO,
  GraphRAGBuildProgressVO,
  GraphRAGResourceQueryDTO,
  GraphRAGTaskListVO,
} from '@/types/api/education/graphragTask.ts'

// ─── Props / Emits ────────────────────────────────────────────────────────────

interface Props {
  open: boolean
  courseId: number
  /** 传入任务时进入 taskView 模式；不传时进入 build 模式 */
  initialTask?: GraphRAGTaskListVO | null
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'submitted', taskId: number): void
  (e: 'cancelled', taskId: number): void
  (e: 'task-changed'): void
  (e: 'enable', taskId: number): void
  (e: 'retry', taskId: number): void
  (e: 'delete', taskId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { text_processing_status } = useDict('text_processing_status')

// ─── 全局状态 ─────────────────────────────────────────────────────────────────

type DrawerMode = 'build' | 'taskView'
const drawerMode = ref<DrawerMode>('build')

// ─── 步骤控制（build 模式） ──────────────────────────────────────────────────

const currentStep = ref(0) // 0=资源 1=参数 2=确认

// ─── 资源选择（build 模式） ──────────────────────────────────────────────────

const resourceLoading = ref(false)
const resourceList = ref<ChapterResourceListVO[]>([])
const selectedRowKeys = ref<number[]>([])

const resourceQuery = reactive<GraphRAGResourceQueryDTO>({
  courseId: props.courseId,
  parseStatus: '2',
  includeTextDirectly: true,
  resourceName: undefined,
  page: 1,
  size: 10,
})

const resourcePagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const resourceColumns = [
  { title: '资源ID', dataIndex: 'resourceId', key: 'resourceId', width: 80 },
  { title: '资源名称', dataIndex: 'resourceName', key: 'resourceName', ellipsis: true },
  { title: '类型', dataIndex: 'resourceType', key: 'resourceType', width: 90 },
  { title: '文本化', dataIndex: 'parseStatus', key: 'parseStatus', width: 90 },
]

const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedRowKeys.value = keys as number[]
  },
}))

// ─── 构建参数（build 模式） ──────────────────────────────────────────────────

const entityOptions = [
  { label: '概念', value: '概念' },
  { label: '原理', value: '原理' },
  { label: '方法', value: '方法' },
  { label: '定义', value: '定义' },
  { label: '定理', value: '定理' },
  { label: '公式', value: '公式' },
  { label: '例题', value: '例题' },
]

const buildForm = reactive<GraphRAGBuildCreateDTO>({
  courseId: props.courseId,
  resourceIds: [],
  entityTypes: ['概念', '原理', '方法'],
  promptTemplate: 'edu/zh',
})

const customEntityInput = ref('')
const customEntities = ref<string[]>([])

const allEntityTypes = computed(() => [...new Set([...buildForm.entityTypes, ...customEntities.value])])

const submitting = ref(false)

// ─── 任务视图状态（taskView 模式） ───────────────────────────────────────────

const currentTaskId = ref<number>()
const currentTaskRecord = ref<GraphRAGTaskListVO | null>(null)
const taskMessage = ref('')
const pollTimer = ref<number | null>(null)
const polling = ref(false)

const progress = reactive<GraphRAGBuildProgressVO>({
  taskId: 0,
  taskStatus: '',
  currentStep: undefined,
  progressPercent: 0,
  stats: undefined,
  startTime: undefined,
  estimatedEndTime: undefined,
})

// ─── 状态映射 ────────────────────────────────────────────────────────────────

const statusTextMap: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  success: '成功',
  failed: '失败',
  cancelled: '已取消',
}

const statusColorMap: Record<string, string> = {
  pending: 'default',
  processing: 'processing',
  success: 'success',
  failed: 'error',
  cancelled: 'warning',
}

// 合并任务记录的 taskStatus 和 progress 的实时 taskStatus
const displayTaskStatus = computed(() => progress.taskStatus || currentTaskRecord.value?.taskStatus || '')
const isTaskActive = computed(() => !!currentTaskId.value && isRunningStatus(displayTaskStatus.value))
const hasProgress = computed(() => displayTaskStatus.value === 'pending' || displayTaskStatus.value === 'processing')

const progressBarStatus = computed(() => {
  const status = displayTaskStatus.value
  if (status === 'success') return 'success'
  if (status === 'failed' || status === 'cancelled') return 'exception'
  if (status === 'processing') return 'active'
  return 'normal'
})

// 统计数据：优先用 progress.stats，回退到 record.stats
const displayStats = computed(() => progress.stats || currentTaskRecord.value?.stats)

// ─── 工具函数 ────────────────────────────────────────────────────────────────

function isRunningStatus(status?: string): boolean {
  return status === 'pending' || status === 'processing'
}

function getTypeColor(type: string) {
  return (
    (
      {
        video: 'blue',
        document: 'green',
        text: 'orange',
        image: 'purple',
        audio: 'cyan',
      } as Record<string, string>
    )[type] || 'default'
  )
}

function getTypeName(type: string) {
  return (
    (
      {
        video: '视频',
        document: '文档',
        text: '文本',
        image: '图片',
        audio: '音频',
      } as Record<string, string>
    )[type] || type
  )
}

function addCustomEntity() {
  const value = customEntityInput.value.trim()
  if (!value) return
  if (customEntities.value.includes(value) || buildForm.entityTypes.includes(value)) {
    message.warning('该实体已存在')
    return
  }
  customEntities.value.push(value)
  customEntityInput.value = ''
}

function removeCustomEntity(entity: string) {
  customEntities.value = customEntities.value.filter((item) => item !== entity)
}

function populateFormFromRecord(record: GraphRAGTaskListVO) {
  const presetTypeValues = entityOptions.map((o) => o.value)
  const allTypes = record.entityTypes || []
  buildForm.entityTypes = allTypes.filter((t) => presetTypeValues.includes(t))
  customEntities.value = allTypes.filter((t) => !presetTypeValues.includes(t))
  buildForm.promptTemplate = (record.promptTemplate as typeof buildForm.promptTemplate) || 'edu/zh'
}

function formatDateTime(dateStr?: string) {
  if (!dateStr) return '-'
  return dateStr
}

// ─── 数据加载 ────────────────────────────────────────────────────────────────

async function loadResources() {
  if (!props.courseId) return
  resourceLoading.value = true
  try {
    const res = await getBuildableResources(resourceQuery)
    if (res.code === 200 && res.data) {
      resourceList.value = res.data.rows || []
      resourcePagination.total = res.data.total || 0
      resourcePagination.current = res.data.page || resourceQuery.page || 1
      resourcePagination.pageSize = res.data.size || resourceQuery.size || 10
    }
  } catch (_e) {
    message.error('加载可构建资源失败')
  } finally {
    resourceLoading.value = false
  }
}

async function refreshProgress() {
  if (!currentTaskId.value) return
  polling.value = true
  try {
    const res = await getGraphRAGBuildProgress(currentTaskId.value)
    if (res.code === 200 && res.data) {
      progress.taskId = res.data.taskId
      progress.taskStatus = res.data.taskStatus
      progress.currentStep = res.data.currentStep
      progress.progressPercent = res.data.progressPercent || 0
      progress.stats = res.data.stats
      progress.startTime = res.data.startTime
      progress.estimatedEndTime = res.data.estimatedEndTime
    }

    if (!isRunningStatus(progress.taskStatus)) {
      clearPollTimer()
      if (progress.taskStatus === 'success') {
        message.success('GraphRAG 索引构建完成')
      }
    }
  } catch (_e) {
    message.error('获取任务进度失败')
    clearPollTimer()
  } finally {
    polling.value = false
  }
}

function startPolling() {
  clearPollTimer()
  pollTimer.value = window.setInterval(() => {
    refreshProgress()
  }, 4000)
}

function clearPollTimer() {
  if (pollTimer.value !== null) {
    window.clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

// ─── 步骤导航（build 模式） ─────────────────────────────────────────────────

function handleResourceQuery() {
  resourceQuery.page = 1
  loadResources()
}

function handleTableChange(pagination: { current?: number; pageSize?: number }) {
  resourceQuery.page = pagination.current || 1
  resourceQuery.size = pagination.pageSize || 10
  loadResources()
}

function nextStep() {
  if (currentStep.value === 0 && selectedRowKeys.value.length === 0) {
    message.warning('请至少选择 1 个可构建资源')
    return
  }
  if (currentStep.value === 1 && allEntityTypes.value.length === 0) {
    message.warning('请至少选择 1 个实体类型')
    return
  }
  currentStep.value++
}

function prevStep() {
  currentStep.value--
}

// ─── 提交与取消 ──────────────────────────────────────────────────────────────

async function submitBuildTask() {
  if (!props.courseId) {
    message.error('缺少课程ID参数')
    return
  }
  if (selectedRowKeys.value.length === 0) {
    message.warning('请至少选择 1 个可构建资源')
    return
  }
  if (allEntityTypes.value.length === 0) {
    message.warning('请至少选择 1 个实体类型')
    return
  }

  submitting.value = true
  taskMessage.value = ''
  try {
    const payload: GraphRAGBuildCreateDTO = {
      courseId: props.courseId,
      resourceIds: selectedRowKeys.value,
      entityTypes: allEntityTypes.value,
      promptTemplate: buildForm.promptTemplate,
    }

    const res = await submitGraphRAGBuild(payload)
    if (res.code === 200 && res.data?.taskId) {
      currentTaskId.value = res.data.taskId
      progress.taskStatus = res.data.taskStatus
      taskMessage.value = res.data.taskMessage || ''
      message.success(`构建任务已提交，任务ID：${res.data.taskId}`)
      await refreshProgress()
      startPolling()
      emit('submitted', res.data.taskId)
    }
  } catch (_e) {
    message.error('提交构建任务失败')
  } finally {
    submitting.value = false
  }
}

function cancelBuildTask() {
  if (!currentTaskId.value) return
  Modal.confirm({
    title: '确认取消任务',
    content: `将取消任务 #${currentTaskId.value}，是否继续？`,
    okText: '确认',
    cancelText: '返回',
    async onOk() {
      try {
        const res = await cancelGraphRAGTask(currentTaskId.value as number)
        if (res.code === 200) {
          progress.taskStatus = 'cancelled'
          taskMessage.value = '任务已取消'
          clearPollTimer()
          message.success('任务已取消')
          emit('cancelled', currentTaskId.value as number)
          await refreshProgress()
        }
      } catch (_e) {
        message.error('取消任务失败')
      }
    },
  })
}

// ─── 任务操作（taskView 模式） ───────────────────────────────────────────────

function handleEnable() {
  if (currentTaskRecord.value) {
    emit('enable', currentTaskRecord.value.taskId)
  }
}

function handleRetry() {
  if (currentTaskRecord.value) {
    emit('retry', currentTaskRecord.value.taskId)
  }
}

function handleDelete() {
  if (!currentTaskRecord.value) return
  const taskId = currentTaskRecord.value.taskId
  Modal.confirm({
    title: '确认删除',
    content: `将删除任务 #${taskId}，是否继续？`,
    okText: '确认',
    cancelText: '返回',
    async onOk() {
      try {
        const res = await deleteGraphRAGTask(String(taskId))
        if (res.code === 200) {
          message.success('删除成功')
          emit('delete', taskId)
          emit('update:open', false)
        }
      } catch (_e) {
        message.error('删除失败')
      }
    },
  })
}

// ─── 抽屉标题 ────────────────────────────────────────────────────────────────

const drawerTitle = computed(() => {
  if (drawerMode.value === 'taskView' && currentTaskRecord.value) {
    return `任务 #${currentTaskRecord.value.taskId}`
  }
  return '构建语义知识图谱'
})

// ─── 抽屉开关 ────────────────────────────────────────────────────────────────

function handleClose() {
  clearPollTimer()
  emit('update:open', false)
}

function resetState() {
  currentStep.value = 0
  drawerMode.value = 'build'
  currentTaskId.value = undefined
  currentTaskRecord.value = null
  taskMessage.value = ''
  progress.taskStatus = ''
  progress.currentStep = undefined
  progress.progressPercent = 0
  progress.stats = undefined
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      if (props.initialTask) {
        // 任务视图模式：详情 + 进度
        drawerMode.value = 'taskView'
        currentTaskRecord.value = props.initialTask
        currentTaskId.value = props.initialTask.taskId
        taskMessage.value = props.initialTask.taskMessage || ''
        populateFormFromRecord(props.initialTask)
        await refreshProgress()
        if (isRunningStatus(progress.taskStatus)) {
          startPolling()
        }
      } else {
        // 新建构建模式
        drawerMode.value = 'build'
        currentStep.value = 0
        resourceQuery.courseId = props.courseId
        buildForm.courseId = props.courseId
        await loadResources()
      }
    } else {
      clearPollTimer()
      resetState()
    }
  }
)

onBeforeUnmount(() => {
  clearPollTimer()
})
</script>

<template>
  <a-drawer :open="open" :title="drawerTitle" :width="720" placement="right" @close="handleClose">
    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <!-- build 模式：三步构建流程 -->
    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <template v-if="drawerMode === 'build'">
      <a-steps :current="currentStep" class="build-steps" size="small">
        <a-step title="选择资源" />
        <a-step title="配置参数" />
        <a-step title="确认提交" />
      </a-steps>

      <div class="step-content">
        <!-- 步骤 1: 资源选择 -->
        <template v-if="currentStep === 0">
          <div class="resource-toolbar">
            <a-input
              v-model:value="resourceQuery.resourceName"
              allow-clear
              placeholder="按资源名称筛选"
              class="w-52"
              @press-enter="handleResourceQuery"
            />
            <a-checkbox v-model:checked="resourceQuery.includeTextDirectly">含 text 直通</a-checkbox>
            <a-button type="primary" size="small" @click="handleResourceQuery">查询</a-button>
            <span class="selected-hint">已选 {{ selectedRowKeys.length }} 项资源</span>
          </div>

          <a-table
            row-key="resourceId"
            size="small"
            :columns="resourceColumns"
            :data-source="resourceList"
            :loading="resourceLoading"
            :row-selection="rowSelection"
            :pagination="resourcePagination"
            :scroll="{ y: 360 }"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'resourceType'">
                <a-tag :color="getTypeColor(record.resourceType)">{{ getTypeName(record.resourceType) }}</a-tag>
              </template>
              <template v-else-if="column.key === 'parseStatus'">
                <DictTag :options="text_processing_status" :value="record.parseStatus || '0'" />
              </template>
            </template>
          </a-table>
        </template>

        <!-- 步骤 2: 构建参数 -->
        <template v-else-if="currentStep === 1">
          <a-form layout="vertical">
            <a-form-item label="提示词模板">
              <a-select v-model:value="buildForm.promptTemplate">
                <a-select-option value="default/zh">default/zh</a-select-option>
                <a-select-option value="default/en">default/en</a-select-option>
                <a-select-option value="edu/zh">edu/zh</a-select-option>
                <a-select-option value="edu/en">edu/en</a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item label="实体类型（至少选择 1 项）">
              <div class="entity-grid">
                <label v-for="opt in entityOptions" :key="opt.value" class="entity-chip">
                  <input
                    type="checkbox"
                    :value="opt.value"
                    :checked="buildForm.entityTypes.includes(opt.value)"
                    class="entity-checkbox"
                    @change="
                      (e: Event) => {
                        const checked = (e.target as HTMLInputElement).checked
                        if (checked) {
                          buildForm.entityTypes.push(opt.value)
                        } else {
                          buildForm.entityTypes = buildForm.entityTypes.filter((t) => t !== opt.value)
                        }
                      }
                    "
                  />
                  <span class="entity-chip-text">{{ opt.label }}</span>
                </label>
              </div>
            </a-form-item>

            <a-form-item label="自定义实体">
              <a-space-compact class="w-full">
                <a-input
                  v-model:value="customEntityInput"
                  placeholder="输入实体名称后添加"
                  @press-enter="addCustomEntity"
                />
                <a-button @click="addCustomEntity">添加</a-button>
              </a-space-compact>
              <div v-if="customEntities.length" class="flex flex-wrap gap-1 mt-2">
                <a-tag v-for="entity in customEntities" :key="entity" closable @close="removeCustomEntity(entity)">
                  {{ entity }}
                </a-tag>
              </div>
            </a-form-item>
          </a-form>
        </template>

        <!-- 步骤 3: 确认提交 -->
        <template v-else-if="currentStep === 2">
          <div class="confirm-summary">
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="选择资源">{{ selectedRowKeys.length }} 项</a-descriptions-item>
              <a-descriptions-item label="实体类型">{{ allEntityTypes.length }} 类</a-descriptions-item>
              <a-descriptions-item label="提示词模板">{{ buildForm.promptTemplate }}</a-descriptions-item>
            </a-descriptions>

            <div class="entity-preview">
              <span class="entity-preview-label">实体类型：</span>
              <div class="entity-preview-tags">
                <a-tag v-for="et in allEntityTypes" :key="et" color="blue" size="small">{{ et }}</a-tag>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部操作栏 -->
      <div class="step-footer">
        <a-button v-if="currentStep > 0" @click="prevStep">上一步</a-button>
        <div class="flex-1" />
        <a-button v-if="currentStep < 2" type="primary" @click="nextStep">下一步</a-button>
        <a-button v-else type="primary" :disabled="submitting" @click="submitBuildTask">
          <template #icon><PlayCircleOutlined /></template>
          开始构建
        </a-button>
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <!-- taskView 模式：任务详情 + 进度跟踪 合并视图 -->
    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <template v-else-if="currentTaskRecord">
      <div class="task-view">
        <!-- 顶部状态头部 -->
        <div class="tv-header">
          <div class="tv-badges">
            <a-tag :color="statusColorMap[displayTaskStatus] || 'default'">
              {{ statusTextMap[displayTaskStatus] || displayTaskStatus || '-' }}
            </a-tag>
            <a-tag v-if="currentTaskRecord.enabled === 'Y'" color="green">已启用</a-tag>
          </div>
        </div>

        <!-- 实时进度（运行中时显示） -->
        <div v-if="hasProgress" class="tv-section">
          <div class="tv-section-title">实时进度</div>
          <div v-if="progress.currentStep" class="tv-progress-step">当前步骤：{{ progress.currentStep }}</div>
          <a-progress :percent="progress.progressPercent" :status="progressBarStatus" />
          <div class="tv-progress-actions">
            <a-button size="small" :loading="polling" @click="refreshProgress">刷新</a-button>
            <a-button v-if="isTaskActive" size="small" danger @click="cancelBuildTask">
              <template #icon><StopOutlined /></template>
              取消
            </a-button>
          </div>
        </div>

        <!-- 错误/警告消息 -->
        <a-alert
          v-if="taskMessage && (displayTaskStatus === 'failed' || displayTaskStatus === 'cancelled')"
          type="error"
          show-icon
          :message="taskMessage"
          class="mb-3"
        />
        <a-alert v-else-if="taskMessage && hasProgress" type="warning" show-icon :message="taskMessage" class="mb-3" />

        <!-- 完成提示 -->
        <div v-if="displayTaskStatus === 'success'" class="complete-hint mb-3">
          <CheckOutlined class="complete-icon" />
          <span>构建完成</span>
        </div>

        <!-- 基本信息 -->
        <a-divider orientation="left" :orientation-margin="0">基本信息</a-divider>
        <a-descriptions :column="2" size="small" bordered>
          <a-descriptions-item label="任务类型">{{ currentTaskRecord.taskType || '-' }}</a-descriptions-item>
          <a-descriptions-item label="提示词模板">{{ currentTaskRecord.promptTemplate || '-' }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDateTime(currentTaskRecord.createTime) }}</a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ formatDateTime(currentTaskRecord.startTime) }}</a-descriptions-item>
          <a-descriptions-item label="结束时间" :span="2">
            {{ formatDateTime(currentTaskRecord.endTime) }}
          </a-descriptions-item>
        </a-descriptions>

        <!-- 构建参数 -->
        <a-divider orientation="left" :orientation-margin="0">构建参数</a-divider>
        <div class="tv-param-section">
          <div class="tv-param-row">
            <span class="tv-param-label">资源 ({{ currentTaskRecord.resourceIds?.length || 0 }})</span>
            <div class="tv-param-tags">
              <a-tag v-for="id in (currentTaskRecord.resourceIds || []).slice(0, 10)" :key="id" size="small">{{
                id
              }}</a-tag>
              <span v-if="(currentTaskRecord.resourceIds || []).length > 10" class="tv-param-more">
                +{{ (currentTaskRecord.resourceIds || []).length - 10 }}
              </span>
              <span v-if="!currentTaskRecord.resourceIds?.length" class="tv-param-empty">-</span>
            </div>
          </div>
          <div class="tv-param-row">
            <span class="tv-param-label">实体类型 ({{ currentTaskRecord.entityTypes?.length || 0 }})</span>
            <div class="tv-param-tags">
              <a-tag v-for="entity in currentTaskRecord.entityTypes || []" :key="entity" color="blue" size="small">{{
                entity
              }}</a-tag>
              <span v-if="!currentTaskRecord.entityTypes?.length" class="tv-param-empty">-</span>
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <template v-if="displayStats && Object.keys(displayStats).length">
          <a-divider orientation="left" :orientation-margin="0">统计信息</a-divider>
          <div class="stats-grid">
            <div v-for="(value, key) in displayStats" :key="String(key)" class="stats-item">
              <span class="stats-value">{{ value }}</span>
              <span class="stats-label">{{ key }}</span>
            </div>
          </div>
        </template>

        <!-- 底部操作 -->
        <div class="tv-actions">
          <a-button
            v-if="displayTaskStatus === 'success' && currentTaskRecord.enabled !== 'Y'"
            type="primary"
            @click="handleEnable"
          >
            启用
          </a-button>
          <a-button
            v-if="displayTaskStatus === 'failed' || displayTaskStatus === 'cancelled'"
            type="primary"
            @click="handleRetry"
          >
            重试
          </a-button>
          <a-button v-if="displayTaskStatus === 'success'" @click="handleRetry">重建</a-button>
          <a-button danger @click="handleDelete">删除</a-button>
        </div>
      </div>
    </template>
  </a-drawer>
</template>

<style scoped>
@reference '#main.css';

/* ─── build 模式 ──────────────────────────────────────────────────────────── */

.build-steps {
  @apply mb-6;
}

.step-content {
  @apply mt-4;
  min-height: 400px;
}

.resource-toolbar {
  @apply flex items-center gap-3 mb-3 flex-wrap;
}

.selected-hint {
  @apply text-xs text-gray-500 dark:text-gray-400 ml-auto;
}

.entity-grid {
  @apply grid grid-cols-2 sm:grid-cols-3 gap-2;
}

.entity-chip {
  @apply flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors;
  @apply border-gray-200 dark:border-gray-700;
  @apply hover:border-blue-300 dark:hover:border-blue-600;
  @apply select-none;
}

.entity-chip:has(.entity-checkbox:checked) {
  @apply border-blue-400 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-500;
}

.entity-checkbox {
  @apply accent-blue-500;
}

.entity-chip-text {
  @apply text-sm;
}

.confirm-summary {
  @apply flex flex-col gap-3;
}

.entity-preview {
  @apply flex items-start gap-2 mt-2;
}

.entity-preview-label {
  @apply text-sm text-gray-500 dark:text-gray-400 flex-shrink-0;
}

.entity-preview-tags {
  @apply flex flex-wrap gap-1;
}

.step-footer {
  @apply flex items-center gap-3 pt-4 mt-6 border-t;
  @apply border-gray-200 dark:border-gray-700;
}

/* ─── taskView 模式 ───────────────────────────────────────────────────────── */

.task-view {
  @apply flex flex-col gap-1;
}

.tv-header {
  @apply flex items-center justify-between mb-2;
}

.tv-badges {
  @apply flex items-center gap-2;
}

.tv-section {
  @apply p-3 rounded-lg mb-2;
  @apply bg-gray-50 dark:bg-gray-800/40;
}

.tv-section-title {
  @apply text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2;
}

.tv-progress-step {
  @apply text-xs text-gray-500 dark:text-gray-400 mb-2;
}

.tv-progress-actions {
  @apply flex items-center gap-2 mt-2;
}

.tv-param-section {
  @apply flex flex-col gap-3;
}

.tv-param-row {
  @apply flex items-start gap-2;
}

.tv-param-label {
  @apply text-xs text-gray-500 dark:text-gray-400 flex-shrink-0 pt-0.5;
}

.tv-param-tags {
  @apply flex flex-wrap gap-1;
}

.tv-param-more {
  @apply text-xs text-gray-400;
}

.tv-param-empty {
  @apply text-xs text-gray-400;
}

.tv-actions {
  @apply flex items-center gap-2 pt-4 mt-4 border-t;
  @apply border-gray-200 dark:border-gray-700;
}

/* ─── 通用 ────────────────────────────────────────────────────────────────── */

.stats-grid {
  @apply grid grid-cols-3 gap-3;
}

.stats-item {
  @apply flex flex-col items-center p-3 rounded-lg;
  @apply bg-gray-50 dark:bg-gray-800/60;
}

.stats-value {
  @apply text-lg font-semibold text-gray-800 dark:text-gray-200;
}

.stats-label {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.complete-hint {
  @apply flex items-center gap-2 p-3 rounded-lg;
  @apply bg-green-50 dark:bg-green-900/20;
  @apply text-green-700 dark:text-green-400;
}

.complete-icon {
  @apply text-lg;
}
</style>
