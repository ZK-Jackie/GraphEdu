<script setup lang="ts">
/**
 * 视频资源面板
 * 在 ChapterResource.vue 的 Golden Layout 中展示视频类型资源
 *
 * 优先使用 fileUrl（上传至 OSS 的视频文件），次选 resourceUrl（外链视频）
 * 集成 useResourceProgress 追踪播放进度，支持断点续学
 */
import { useResourceProgress } from '@/composables/useResourceProgress'

const props = defineProps<{
  /** 资料 ID */
  resourceId: number
  /** 资料名称（Tab 标题，供调试用） */
  resourceName?: string
  /** 文件 URL（OSS 上传文件，优先使用） */
  fileUrl?: string
  /** 外部链接 URL（次选） */
  resourceUrl?: string
  /** Golden Layout 注入的 refId（内部使用）*/
  refId?: number
}>()

/** 实际播放地址 */
const videoSrc = computed(() => props.fileUrl ?? props.resourceUrl ?? '')

// ─── 进度追踪 ──────────────────────────────────────────────────────────────

const videoRef = ref<HTMLVideoElement | null>(null)
const { position, initialized, report, startTracking, reportImmediate } = useResourceProgress({
  resourceId: props.resourceId,
  resourceType: 'video',
  enabled: !!videoSrc.value,
})

/** 节流标记：上次上报 timeupdate 的时间戳 */
let lastTimeUpdateTime = 0
const TIME_UPDATE_THROTTLE_MS = 5000

/** 监听视频 timeupdate 事件，节流更新位置 */
function onTimeUpdate() {
  const video = videoRef.value
  if (!video) return

  const now = Date.now()
  if (now - lastTimeUpdateTime < TIME_UPDATE_THROTTLE_MS) return
  lastTimeUpdateTime = now

  position.value = {
    video_second: Math.round(video.currentTime * 10) / 10,
    duration: Math.round(video.duration * 10) / 10 || 0,
  }
}

/** 视频元数据加载完成 → 开始计时 */
function onLoadedMetadata() {
  const video = videoRef.value
  if (!video) return

  // 资源加载完成，开始计时（内部等待 initialized，已完成的资源自动跳过）
  startTracking()
}

/** 断点续学：恢复视频播放位置（等待进度查询完成后再定位） */
watch(initialized, (ready) => {
  if (!ready) return
  const video = videoRef.value
  const restored = position.value
  if (video && restored?.video_second && restored.video_second > 0) {
    video.currentTime = restored.video_second
  }
})

/** 视频播放结束 → 立即上报完成 */
function onVideoEnded() {
  position.value = {
    video_second: videoRef.value?.duration ?? 0,
    duration: videoRef.value?.duration ?? 0,
  }
  reportImmediate()
}
</script>

<template>
  <div class="chapter-video-panel h-full w-full flex flex-col bg-black">
    <!-- 有视频地址：渲染 HTML5 视频播放器 -->
    <video
      v-if="videoSrc"
      ref="videoRef"
      class="flex-1 w-full h-full object-contain"
      controls
      :src="videoSrc"
      preload="metadata"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="onVideoEnded"
    >
      您的浏览器不支持 HTML5 video 标签
    </video>

    <!-- 无视频地址：错误提示 -->
    <div v-else class="flex-1 flex items-center justify-center bg-gray-950">
      <a-result status="warning" title="无法加载视频" sub-title="该资料尚未上传视频文件或视频链接无效" />
    </div>
  </div>
</template>

<style scoped>
.chapter-video-panel {
  background: #000;
}
</style>
