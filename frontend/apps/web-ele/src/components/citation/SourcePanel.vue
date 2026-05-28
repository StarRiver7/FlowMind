<script setup lang="ts">
import { computed } from 'vue';
import type { CitationSource } from '#/api/core/types';

const props = defineProps<{
  sources: CitationSource[];
}>();

const hasSources = computed(() => props.sources.length > 0);

const groupedSources = computed(() => {
  const groups: Record<string, CitationSource[]> = {};
  for (const src of props.sources) {
    const kb = src.knowledge_base || '默认知识库';
    if (!groups[kb]) groups[kb] = [];
    groups[kb].push(src);
  }
  return Object.entries(groups);
});
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="shrink-0 px-4 py-3 border-b border-gray-100">
      <div class="flex items-center gap-2 text-sm font-semibold text-gray-700">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
        </svg>
        引用来源
        <span v-if="hasSources" class="ml-auto text-[10px] font-normal bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
          {{ sources.length }}
        </span>
      </div>
    </div>

    <!-- Source list -->
    <div class="flex-1 overflow-y-auto isu-scrollbar">
      <div v-if="!hasSources" class="flex flex-col items-center justify-center py-12 text-center">
        <svg class="mb-3 text-gray-300" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
        </svg>
        <div class="text-xs text-gray-400">暂无引用来源</div>
        <div class="mt-1 text-[11px] text-gray-300">回答中包含来源时自动展示</div>
      </div>

      <div v-else>
        <div v-for="[kbName, kbSources] in groupedSources" :key="kbName" class="border-b border-gray-50 last:border-0">
          <div class="px-4 py-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider bg-gray-50/50">
            {{ kbName }}
          </div>
          <div
            v-for="(src, i) in kbSources"
            :key="i"
            class="px-4 py-3 hover:bg-blue-50/30 transition-colors cursor-pointer group"
          >
            <div class="flex items-start gap-2.5">
              <!-- Index -->
              <span class="shrink-0 flex items-center justify-center w-5 h-5 rounded-md bg-blue-50 text-blue-600 text-[10px] font-bold group-hover:bg-blue-100 transition-colors">
                {{ i + 1 }}
              </span>
              <div class="min-w-0 flex-1">
                <div class="text-[13px] font-medium text-gray-700 truncate group-hover:text-blue-600 transition-colors">
                  {{ src.document_name }}
                </div>
                <div class="flex items-center gap-3 mt-0.5 text-[10px] text-gray-400">
                  <span v-if="src.page_number">第 {{ src.page_number }} 页</span>
                  <span v-if="src.relevance_score !== undefined" class="flex items-center gap-1">
                    <span class="w-8 h-1 rounded-full bg-gray-100 overflow-hidden">
                      <span class="block h-full rounded-full bg-blue-400" :style="{ width: `${(src.relevance_score * 100).toFixed(0)}%` }" />
                    </span>
                    {{ (src.relevance_score * 100).toFixed(0) }}%
                  </span>
                </div>
                <div v-if="src.excerpt" class="mt-1.5 text-[11px] text-gray-500 leading-relaxed line-clamp-2">
                  {{ src.excerpt }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
