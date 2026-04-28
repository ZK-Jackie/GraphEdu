<script setup lang="ts">
interface InputTagProps {
  modelValue: string
  placeholder?: string
  delimiter?: string
}

const { modelValue, placeholder, delimiter = ',' } = defineProps<InputTagProps>()
const emit = defineEmits(['update:modelValue'])
</script>

<template></template>

<style scoped></style>
