<template>
  <svg class="svg-icon" aria-hidden="true" :style="{ width: size, height: size }">
    <use :xlink:href="useIconName" :fill="useIconColor" />
  </svg>
</template>

<script lang="ts">
export default defineComponent({
  props: {
    icon: {
      type: String,
      required: true,
    },
    color: {
      type: String,
      default: '',
    },
    size: {
      type: [String, Number],
      default: '1em',
    },
  },
  setup(props) {
    return {
      useIconName: computed(() => `#${props.icon}`),
      useIconColor: computed(() => props.color),
    }
  },
})
</script>

<style scoped>
@reference "#main.css";

.nav-github-icon {
  @apply flex items-center justify-center text-3xl m-1;
}

.svg-icon {
  width: 1em;
  height: 1em;
  position: relative;
  fill: currentColor;
  vertical-align: -2px;
}
</style>
