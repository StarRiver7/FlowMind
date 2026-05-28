<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '#/hooks/useMarkdown';

const props = defineProps<{
  content: string;
  class?: string;
}>();

const html = computed(() => renderMarkdown(props.content));
</script>

<template>
  <div
    class="isu-markdown"
    :class="props.class"
    v-html="html"
    @click.capture="(e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains('isu-citation')) {
        const citeId = target.dataset.cite;
        if (citeId) {
          // Dispatch custom event for parent to handle
          target.dispatchEvent(new CustomEvent('citation-click', {
            bubbles: true,
            detail: { id: parseInt(citeId) },
          }));
        }
      }
    }"
  />
</template>
