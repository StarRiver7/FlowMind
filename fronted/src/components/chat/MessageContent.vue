<!-- ============================================================ -->
<!-- MessageContent — Markdown rendering with code highlighting     -->
<!-- ============================================================ -->
<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{ content: string; isUser: boolean }>()

const rendered = computed(() => {
  if (!props.content) return ''
  if (props.isUser) {
    // User messages: just escape HTML, no markdown
    return props.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
  }
  return renderMarkdown(props.content)
})
</script>

<template>
  <div
    v-if="isUser"
    class="user-content"
    v-html="rendered"
  ></div>
  <div
    v-else
    class="markdown-body"
    v-html="rendered"
  ></div>
</template>

<style scoped>
.user-content {
  line-height: 1.55;
}
.markdown-body {
  color: var(--text-primary);
}
</style>