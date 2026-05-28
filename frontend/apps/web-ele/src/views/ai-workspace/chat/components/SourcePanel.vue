<script setup lang="ts">
import type { CitationSource } from '#/api/core/types';

defineProps<{
  sources: CitationSource[];
}>();
</script>

<template>
  <div class="px-3 py-4 border-t border-gray-100">
    <div class="mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
      引用来源
    </div>

    <div v-if="sources.length === 0" class="py-4 text-center text-xs text-gray-400">
      暂无引用来源
    </div>

    <div class="space-y-2">
      <div
        v-for="(src, i) in sources"
        :key="i"
        class="rounded-lg border border-gray-100 bg-gray-50/50 p-3 transition-all hover:border-blue-200 hover:bg-blue-50/30"
      >
        <!-- Header -->
        <div class="flex items-center gap-2 mb-1.5">
          <span class="flex h-5 w-5 items-center justify-center rounded bg-blue-500 text-[10px] font-bold text-white">
            {{ i + 1 }}
          </span>
          <span class="text-xs font-medium text-gray-700 truncate">
            {{ src.document_name || '未知文档' }}
          </span>
        </div>

        <!-- Meta -->
        <div class="flex flex-wrap gap-2 text-[11px] text-gray-500 mb-1.5">
          <span v-if="src.page_number" class="flex items-center gap-1">
            📄 第{{ src.page_number }}页
          </span>
          <span v-if="src.knowledge_base" class="flex items-center gap-1">
            📁 {{ src.knowledge_base }}
          </span>
          <span v-if="src.relevance_score" class="flex items-center gap-1">
            🎯 {{ (src.relevance_score * 100).toFixed(0) }}%
          </span>
        </div>

        <!-- Score bar -->
        <div v-if="src.relevance_score" class="mb-1.5 h-1 rounded-full bg-gray-200 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="{
              'bg-green-400': src.relevance_score >= 0.7,
              'bg-yellow-400': src.relevance_score >= 0.4 && src.relevance_score < 0.7,
              'bg-red-300': src.relevance_score < 0.4,
            }"
            :style="{ width: (src.relevance_score * 100) + '%' }"
          />
        </div>

        <!-- Excerpt -->
        <div
          v-if="src.excerpt"
          class="text-[11px] text-gray-500 leading-relaxed line-clamp-2"
        >
          {{ src.excerpt }}
        </div>
      </div>
    </div>
  </div>
</template>
