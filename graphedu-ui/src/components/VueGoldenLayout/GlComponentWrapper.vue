<template>
  <div ref="GlComponent" style="position: absolute; overflow: auto">
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
const GlComponent = ref<null | HTMLElement>(null)

const numberToPixels = (value: number): string => {
  return value.toString(10) + 'px'
}

const setPosAndSize = (left: number, top: number, width: number, height: number): void => {
  if (GlComponent.value) {
    const el = GlComponent.value
    el.style.left = numberToPixels(left)
    el.style.top = numberToPixels(top)
    el.style.width = numberToPixels(width)
    el.style.height = numberToPixels(height)
  }
}

const setVisibility = (visible: boolean): void => {
  if (GlComponent.value) {
    const el = GlComponent.value
    if (visible) {
      el.style.display = ''
    } else {
      el.style.display = 'none'
    }
  }
}

const setZIndex = (value: string): void => {
  if (GlComponent.value) {
    const el = GlComponent.value
    el.style.zIndex = value
  }
}

defineExpose({
  setPosAndSize,
  setVisibility,
  setZIndex,
})
</script>
