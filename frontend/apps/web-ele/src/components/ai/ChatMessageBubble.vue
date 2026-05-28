<script setup lang="ts">
import { computed } from 'vue';
import MarkdownView from '#/components/markdown/MarkdownView.vue';
import type { ChatMessageUI } from '#/store/ai-chat';

const props = defineProps<{
  message: ChatMessageUI;
  streaming?: boolean;
}>();

const isUser = computed(() => props.message.role === 'user');
const hasSources = computed(() => (props.message.sources?.length ?? 0) > 0);
const hasTrace = computed(() => (props.message.trace?.length ?? 0) > 0);
</script>

<template>
  <div
    class="mb-5 animate-isu-fade-in"
    :class="isUser ? 'flex justify-end' : 'flex gap-3'"
  >
    <!-- Avatar (assistant only) -->
    <div v-if="!isUser" class="shrink-0 mt-1">
      <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white text-[13px] font-semibold">
        SU
      </div>
    </div>

    <div :class="isUser ? 'max-w-[75%]' : 'max-w-[85%] flex-1'">
      <!-- Bubble -->
      <div :class="isUser ? 'isu-bubble-user px-5 py-3' : 'isu-bubble-assistant px-5 py-3'">
        <!-- Role label -->
        <div v-if="!isUser" class="mb-1.5 text-[11px] font-semibold text-blue-500 tracking-wide uppercase">
          internSU
        </div>

        <!-- Content -->
        <div v-if="isUser" class="text-[15px] text-gray-800 leading-relaxed whitespace-pre-wrap">
          {{ message.content }}
        </div>
        <MarkdownView v-else :content="message.content" />

        <!-- Streaming cursor -->
        <span
          v-if="streaming"
          class="inline-block w-1.5 h-5 bg-blue-500 animate-pulse align-text-bottom ml-0.5 rounded-sm"
        />
      </div>

      <!-- Sources inline (on hover) -->
      <div
        v-if="hasSources && !isUser"
        class="mt-2 flex flex-wrap gap-1.5"
      >
        <span
          v-for="(src, i) in message.sources"
          :key="i"
          class="inline-flex items-center gap-1 rounded-md bg-gray-50 border border-gray-100 px-2.5 py-1
                 text-[11px] text-gray-500 cursor-pointer hover:border-blue-200 hover:bg-blue-50/50 transition-all"
          :title="src.excerpt || src.document_name"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
          </svg>
          <span class="max-w-[140px] truncate">{{ src.document_name }}</span>
          <span v-if="src.page_number" class="text-gray-400">p.{{ src.page_number }}</span>
          <span v-if="src.relevance_score" class="text-gray-400 ml-0.5">{{ (src.relevance_score * 100).toFixed(0) }}%</span>
        </span>
      </div>

      <!-- Agent trace summary (collapsed) -->
      <details v-if="hasTrace && !isUser" class="mt-2 group">
        <summary class="text-[11px] text-gray-400 cursor-pointer hover:text-gray-500 select-none">
          {{ message.trace!.length }} 步工作过程
        </summary>
        <div class="mt-1.5 space-y-1 pl-1 border-l-2 border-gray-100">
          <div
            v-for="(step, i) in message.trace"
            :key="i"
            class="flex items-center gap-2 text-[11px]"
            :class="step.status === 'completed' ? 'text-gray-400' : step.status === 'failed' ? 'text-red-400' : 'text-blue-500'"
          >
            <span v-if="step.status === 'completed'" class="text-green-400">&#10003;</span>
            <span v-else-if="step.status === 'failed'" class="text-red-400">&#10007;</span>
            <span v-else class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            <span class="text-gray-500">{{ step.node }}</span>
            <span class="text-gray-400 truncate">{{ step.message }}</span>
          </div>
        </div>
      </details>
    </div>
  </div>
</template>
