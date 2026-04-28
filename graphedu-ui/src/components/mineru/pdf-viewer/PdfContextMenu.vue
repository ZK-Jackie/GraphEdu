<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="pdf-context-menu"
      :style="{
        left: position.x + 'px',
        top: position.y + 'px',
      }"
    >
      <div class="context-menu-item" @click="handleQuote">
        <LinkOutlined />
        <span>引用此文本</span>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { LinkOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import useQuoteStore from '@/stores/modules/quote'

interface Props {
  visible: boolean
  position: { x: number; y: number }
  selectedText: string
  sourcePath: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const quoteStore = useQuoteStore()

function handleQuote(): void {
  if (props.selectedText) {
    quoteStore.addQuote(props.selectedText, props.sourcePath)
    message.success('已添加引用，可在聊天框中查看')
  }
  emit('close')
}
</script>

<style scoped>
@reference '#main.css';

.pdf-context-menu {
  @apply fixed z-[9999] rounded-lg shadow-lg py-1 min-w-40;
  background: var(--ge-bg-elevated);
  border: 1px solid var(--ge-border-color);
}

.context-menu-item {
  @apply flex items-center gap-2 px-4 py-2 text-sm cursor-pointer transition-colors;
  color: var(--ge-text-primary);
}

.context-menu-item:hover {
  color: var(--ge-primary);
  background: var(--ge-primary-light);
}
</style>
