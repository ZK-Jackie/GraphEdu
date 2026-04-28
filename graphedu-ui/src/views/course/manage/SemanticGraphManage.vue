<script setup lang="ts">
/**
 * SemanticGraphManage - 语义知识图谱管理页面
 *
 * 精简编排器，协调 Header / TaskList / BuildDrawer（合并了详情+进度+构建）。
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  cancelGraphRAGTask,
  enableGraphRAGTask,
  deleteGraphRAGTask,
  retryGraphRAGTask,
  getGraphRAGTaskListByCourse,
} from '@/api/education/graphragBuild.ts'
import SemanticGraphHeader from './components/SemanticGraphHeader.vue'
import SemanticGraphTaskList from './components/SemanticGraphTaskList.vue'
import SemanticGraphBuildDrawer from './components/SemanticGraphBuildDrawer.vue'
import type { GraphRAGTaskListVO } from '@/types/api/education/graphragTask.ts'

const route = useRoute()
const courseId = ref<number>(Number(route.params.courseId) || 0)

// ─── 任务列表 ─────────────────────────────────────────────────────────────────

const taskListLoading = ref(false)
const taskList = ref<GraphRAGTaskListVO[]>([])
const retryingTaskId = ref<number | null>(null)
const cancelingTaskId = ref<number | null>(null)

async function loadTaskList() {
  if (!courseId.value) return
  taskListLoading.value = true
  try {
    const res = await getGraphRAGTaskListByCourse(courseId.value)
    if (res.code === 200 && res.data) {
      taskList.value = res.data
    }
  } catch (_e) {
    message.error('加载任务列表失败')
  } finally {
    taskListLoading.value = false
  }
}

// ─── 统计 ─────────────────────────────────────────────────────────────────────

const runningCount = computed(() => taskList.value.filter((t) => isRunningStatus(t.taskStatus)).length)
const enabledCount = computed(() => taskList.value.filter((t) => t.enabled === 'Y').length)

function isRunningStatus(status?: string): boolean {
  return status === 'pending' || status === 'processing'
}

// ─── 统一抽屉 ─────────────────────────────────────────────────────────────────

const drawerVisible = ref(false)
const activeTask = ref<GraphRAGTaskListVO | null>(null)

/** 新建构建：不传 initialTask */
function openBuildDrawer() {
  activeTask.value = null
  drawerVisible.value = true
}

/** 查看任务详情/进度：传入 initialTask */
function openTaskView(record: GraphRAGTaskListVO) {
  activeTask.value = record
  drawerVisible.value = true
}

function handleDrawerSubmitted(_taskId: number) {
  loadTaskList()
}

function handleDrawerCancelled(_taskId: number) {
  loadTaskList()
}

function handleDrawerTaskChanged() {
  loadTaskList()
}

// ─── 任务操作 ─────────────────────────────────────────────────────────────────

async function handleEnableTask(taskId: number) {
  try {
    const res = await enableGraphRAGTask(taskId)
    if (res.code === 200) {
      message.success('启用成功')
      await loadTaskList()
    }
  } catch (_e) {
    message.error('启用失败')
  }
}

async function handleCancelTask(taskId: number) {
  cancelingTaskId.value = taskId
  try {
    const res = await cancelGraphRAGTask(taskId)
    if (res.code === 200) {
      message.success('任务已取消')
      await loadTaskList()
    }
  } catch (_e) {
    message.error('取消任务失败')
  } finally {
    cancelingTaskId.value = null
  }
}

async function handleRetryTask(taskId: number) {
  retryingTaskId.value = taskId
  try {
    const res = await retryGraphRAGTask(taskId)
    if (res.code === 200) {
      message.success('任务已重新提交')
      await loadTaskList()
      // 打开抽屉进入任务视图
      const record = taskList.value.find((t) => t.taskId === taskId)
      if (record) {
        openTaskView(record)
      }
    }
  } catch (_e) {
    message.error('重试任务失败')
  } finally {
    retryingTaskId.value = null
  }
}

function handleDeleteTask(taskId: number) {
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
          await loadTaskList()
          // 如果抽屉正在展示该任务，关闭
          if (activeTask.value?.taskId === taskId) {
            drawerVisible.value = false
          }
        }
      } catch (_e) {
        message.error('删除失败')
      }
    },
  })
}

// ─── 生命周期 ─────────────────────────────────────────────────────────────────

onMounted(() => {
  if (!courseId.value) {
    message.error('缺少课程ID参数')
    return
  }
  loadTaskList()
})
</script>

<template>
  <div class="flex flex-col h-full">
    <SemanticGraphHeader
      :total-tasks="taskList.length"
      :running-count="runningCount"
      :enabled-count="enabledCount"
      :loading="taskListLoading"
      @refresh="loadTaskList"
      @create="openBuildDrawer"
    />

    <div class="flex-1 overflow-y-auto px-6 pb-6">
      <SemanticGraphTaskList
        :task-list="taskList"
        :loading="taskListLoading"
        :retrying-task-id="retryingTaskId"
        :canceling-task-id="cancelingTaskId"
        @enable="handleEnableTask"
        @cancel="handleCancelTask"
        @retry="handleRetryTask"
        @delete="handleDeleteTask"
        @view-progress="openTaskView"
        @view-detail="openTaskView"
        @create="openBuildDrawer"
      />
    </div>

    <SemanticGraphBuildDrawer
      v-model:open="drawerVisible"
      :course-id="courseId"
      :initial-task="activeTask"
      @submitted="handleDrawerSubmitted"
      @cancelled="handleDrawerCancelled"
      @task-changed="handleDrawerTaskChanged"
      @enable="handleEnableTask"
      @retry="handleRetryTask"
      @delete="handleDeleteTask"
    />
  </div>
</template>
