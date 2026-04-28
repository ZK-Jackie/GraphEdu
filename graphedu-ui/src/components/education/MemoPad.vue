<template>
  <a-card :bordered="false" title="备忘录">
    <!-- 输入区 -->
    <div class="memo-input-row">
      <a-input
        v-model:value="newContent"
        placeholder="写下你的待办事项..."
        :maxlength="200"
        allow-clear
        size="small"
        @press-enter="addMemo"
      >
        <template #suffix>
          <span class="char-count">{{ newContent.length }}/200</span>
        </template>
      </a-input>
      <a-button type="primary" size="small" :disabled="!newContent.trim()" @click="addMemo"> 添加 </a-button>
    </div>

    <!-- 列表 -->
    <div v-if="memos.length > 0" class="memo-list">
      <div
        v-for="memo in sortedMemos"
        :key="memo.id"
        class="memo-item"
        :class="{ 'memo-item--completed': memo.completed }"
      >
        <a-checkbox :checked="memo.completed" @change="toggleMemo(memo.id)" />
        <span class="memo-content" @dblclick="startEdit(memo)">
          <template v-if="editingId === memo.id">
            <a-input
              v-model:value="editContent"
              size="small"
              :maxlength="200"
              autofocus
              @press-enter="saveEdit(memo.id)"
              @blur="saveEdit(memo.id)"
            />
          </template>
          <template v-else>{{ memo.content }}</template>
        </span>
        <span class="memo-time">{{ formatMemoTime(memo.createdAt) }}</span>
        <a-button type="text" size="small" danger @click="deleteMemo(memo.id)">
          <template #icon><DeleteOutlined /></template>
        </a-button>
      </div>
    </div>

    <a-empty v-else description="暂无备忘，添加一条吧" :image-style="{ height: '40px' }" />
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { DeleteOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import useUserStore from '@/stores/modules/user'

interface MemoItem {
  id: string
  content: string
  completed: boolean
  createdAt: number
  updatedAt: number
}

interface Props {
  /** localStorage 存储键后缀，用于区分不同场景 */
  storageKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  storageKey: 'default',
})

const userStore = useUserStore()
const memos = ref<MemoItem[]>([])
const newContent = ref('')
const editingId = ref<string | null>(null)
const editContent = ref('')

const MAX_MEMOS = 50

// 存储键按用户 + 场景隔离
const storageKey = computed(() => `graphedu:memos:${userStore.userId}:${props.storageKey}`)

// 按时间倒序排列，未完成的在前
const sortedMemos = computed(() => {
  return [...memos.value].sort((a, b) => {
    if (a.completed !== b.completed) return a.completed ? 1 : -1
    return b.createdAt - a.createdAt
  })
})

// 从 localStorage 加载
function loadMemos() {
  try {
    const raw = localStorage.getItem(storageKey.value)
    if (raw) {
      memos.value = JSON.parse(raw) as MemoItem[]
    }
  } catch {
    memos.value = []
  }
}

// 保存到 localStorage
function saveMemos() {
  try {
    localStorage.setItem(storageKey.value, JSON.stringify(memos.value))
  } catch {
    message.error('存储空间不足，请清理部分备忘')
  }
}

// 监听存储键变化（用户切换）
watch(storageKey, () => {
  loadMemos()
})

// 添加备忘
function addMemo() {
  const content = newContent.value.trim()
  if (!content) return

  if (memos.value.length >= MAX_MEMOS) {
    message.warning(`最多只能添加 ${MAX_MEMOS} 条备忘`)
    return
  }

  const now = Date.now()
  memos.value.push({
    id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
    content,
    completed: false,
    createdAt: now,
    updatedAt: now,
  })

  newContent.value = ''
  saveMemos()
}

// 切换完成状态
function toggleMemo(id: string) {
  const memo = memos.value.find((m) => m.id === id)
  if (memo) {
    memo.completed = !memo.completed
    memo.updatedAt = Date.now()
    saveMemos()
  }
}

// 删除备忘
function deleteMemo(id: string) {
  memos.value = memos.value.filter((m) => m.id !== id)
  saveMemos()
}

// 开始编辑
function startEdit(memo: MemoItem) {
  editingId.value = memo.id
  editContent.value = memo.content
}

// 保存编辑
function saveEdit(id: string) {
  const content = editContent.value.trim()
  if (!content) {
    editingId.value = null
    return
  }

  const memo = memos.value.find((m) => m.id === id)
  if (memo) {
    memo.content = content
    memo.updatedAt = Date.now()
    saveMemos()
  }
  editingId.value = null
}

// 格式化时间
function formatMemoTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - timestamp
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(() => {
  loadMemos()
})
</script>

<style scoped>
@reference '#main.css';

.memo-input-row {
  @apply flex gap-2 mb-3;
}

.char-count {
  @apply text-xs text-gray-300;
}

.memo-list {
  @apply flex flex-col gap-1 max-h-64 overflow-y-auto;
}

.memo-item {
  @apply flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 transition-colors;
}

.memo-item--completed {
  @apply opacity-50;
}

.memo-content {
  @apply flex-1 text-sm text-gray-700 break-all;
}

.memo-item--completed .memo-content {
  @apply line-through text-gray-400;
}

.memo-time {
  @apply text-xs text-gray-300 whitespace-nowrap hidden sm:inline;
}
</style>
