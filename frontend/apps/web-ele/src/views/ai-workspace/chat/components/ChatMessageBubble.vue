<script setup lang="ts">
import type { CitationSource } from '#/api/core/types';

const props = defineProps<{
  message: {
    role: string;
    content: string;
    sources?: CitationSource[];
    trace?: any[];
  };
}>();

const emit = defineEmits<{ 'cite-click': [source: CitationSource] }>();

// Simple markdown rendering (bold, italic, code, lists)
function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-blue-700 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
    .replace(/\[来源(\d+)\]/g, '<span class="citation-ref" data-cite="$1">[来源$1]</span>')
    .replace(/\n/g, '<br>');
}

function handleCiteClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (target.classList.contains('citation-ref')) {
    const citeId = parseInt(target.dataset.cite || '1');
    const source = props.message.sources?.find((_, i) => i + 1 === citeId);
    if (source) emit('cite-click', source);
  }
}
</script>

<template>
  <div class="mb-4" :class="message.role === 'user' ? 'flex justify-end' : ''">
    <!-- User message -->
    <div
      v-if="message.role === 'user'"
      class="max-w-[75%] rounded-2xl bg-blue-500 px-4 py-2.5 text-sm text-white shadow-sm"
    >
      {{ message.content }}
    </div>

    <!-- Assistant message -->
    <div
      v-else
      class="rounded-2xl bg-white border border-gray-100 px-5 py-3 shadow-sm max-w-[85%]"
    >
      <div class="mb-1.5 flex items-center gap-2">
        <div class="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-blue-400 to-purple-500 text-[10px] font-bold text-white">
          i
        </div>
        <span class="text-xs font-medium text-gray-500">小SU</span>
      </div>

      <div
        class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap"
        v-html="renderMarkdown(message.content)"
        @click="handleCiteClick"
      />

      <!-- Source citations footer -->
      <div
        v-if="message.sources && message.sources.length > 0"
        class="mt-3 border-t border-gray-100 pt-2"
      >
        <div class="text-[11px] font-medium text-gray-400 mb-1.5">参考来源</div>
        <div
          v-for="(src, i) in message.sources.slice(0, 5)"
          :key="i"
          class="mb-1 flex items-center gap-2 text-xs text-gray-500 cursor-pointer hover:text-blue-600 transition-colors"
          @click="emit('cite-click', src)"
        >
          <span class="flex h-4 w-4 items-center justify-center rounded bg-blue-100 text-[10px] font-bold text-blue-600">
            {{ i + 1 }}
          </span>
          <span class="truncate">{{ src.document_name || '未知文档' }}</span>
          <span v-if="src.page_number" class="text-gray-400 shrink-0">第{{ src.page_number }}页</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.citation-ref {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  border-radius: 4px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  vertical-align: middle;
}
.citation-ref:hover {
  background: #bfdbfe;
}
</style>
