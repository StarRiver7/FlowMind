<script setup lang="ts">
import { computed, ref } from 'vue';
import type { AgentTrace, CitationSource } from '#/api/core/types';

const props = defineProps<{
  traces: AgentTrace[];
  streaming: boolean;
}>();

// ── LangGraph Node Flow ──
const flowNodes = [
  { id: 'start',      label: 'START',       icon: '&#9654;' },
  { id: 'intent',     label: 'Intent',       icon: '&#9678;' },
  { id: 'clarify',    label: 'Clarify',      icon: '&#63;' },
  { id: 'retrieval',  label: 'Retrieval',    icon: '&#8981;' },
  { id: 'rerank',     label: 'Rerank',       icon: '&#8645;' },
  { id: 'citation',   label: 'Citation',     icon: '&#8470;' },
  { id: 'answer',     label: 'Answer',       icon: '&#9998;' },
  { id: 'end',        label: 'END',          icon: '&#9632;' },
];

// Map trace node names to flow node IDs
function mapNodeId(nodeName: string): string {
  const name = nodeName.toLowerCase();
  if (name.includes('intent')) return 'intent';
  if (name.includes('clarif')) return 'clarify';
  if (name.includes('retriev') || name.includes('rag_retriev')) return 'retrieval';
  if (name.includes('rerank') || name.includes('rag_rerank')) return 'rerank';
  if (name.includes('citat') || name.includes('rag_citation')) return 'citation';
  if (name.includes('answer') || name.includes('rag_answer') || name.includes('response')) return 'answer';
  if (name === 'loading') return 'start';
  return '';
}

const activeNodeId = computed(() => {
  if (props.traces.length === 0) return props.streaming ? 'start' : null;
  const last = props.traces[props.traces.length - 1];
  return mapNodeId(last.node);
});

const completedNodes = computed(() => {
  const completed = new Set<string>();
  for (const t of props.traces) {
    if (t.status === 'completed' || t.status === 'failed') {
      completed.add(mapNodeId(t.node));
    }
  }
  return completed;
});

function nodeStatus(nodeId: string) {
  if (completedNodes.value.has(nodeId)) return 'completed';
  if (nodeId === activeNodeId.value && props.streaming) return 'running';
  return 'pending';
}

// ── Trace Collapse ──
const maxVisibleTraces = 6;
const showAllTraces = ref(false);
const visibleTraces = computed(() => {
  if (showAllTraces.value) return props.traces;
  const total = props.traces.length;
  if (total <= maxVisibleTraces) return props.traces;
  // Show latest messages, hide older
  return props.traces.slice(total - maxVisibleTraces);
});
const hiddenCount = computed(() => Math.max(0, props.traces.length - maxVisibleTraces));
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="shrink-0 px-4 py-3 border-b border-gray-100">
      <div class="flex items-center gap-2 text-sm font-semibold text-gray-700">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        工作过程
        <span v-if="streaming" class="ml-auto flex items-center gap-1 text-[10px] font-normal text-blue-500">
          <span class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
          运行中
        </span>
      </div>
    </div>

    <!-- LangGraph Node Flow -->
    <div class="shrink-0 px-4 py-3 border-b border-gray-100">
      <div class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2.5">
        LangGraph 节点流
      </div>
      <div class="flex items-center gap-1 justify-between">
        <template v-for="(node, i) in flowNodes" :key="node.id">
          <div class="flex flex-col items-center gap-1" :style="{ width: `${100/flowNodes.length}%` }">
            <div
              class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-300"
              :class="{
                'bg-blue-500 text-white shadow-sm scale-110': nodeStatus(node.id) === 'running',
                'bg-green-500 text-white': nodeStatus(node.id) === 'completed',
                'bg-red-400 text-white': nodeStatus(node.id) === 'failed',
                'bg-gray-100 text-gray-400': nodeStatus(node.id) === 'pending',
              }"
              v-html="node.icon"
            />
            <div
              class="text-[9px] font-medium text-center leading-tight"
              :class="{
                'text-blue-600': nodeStatus(node.id) === 'running',
                'text-green-600': nodeStatus(node.id) === 'completed',
                'text-gray-400': nodeStatus(node.id) === 'pending',
              }"
            >
              {{ node.label }}
            </div>
          </div>
          <!-- Connector -->
          <div
            v-if="i < flowNodes.length - 1"
            class="h-0.5 flex-1 min-w-[8px] rounded-full transition-colors duration-300"
            :class="i < completedNodes.value.size ? 'bg-green-300' : 'bg-gray-200'"
          />
        </template>
      </div>
    </div>

    <!-- Trace Log -->
    <div class="flex-1 overflow-y-auto isu-scrollbar px-4 py-3">
      <div class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2.5">
        Trace 日志
        <span v-if="traces.length > 0" class="ml-1 font-normal">({{ traces.length }})</span>
      </div>

      <!-- Collapsed older traces -->
      <button
        v-if="hiddenCount > 0 && !showAllTraces"
        class="w-full text-center text-[11px] text-gray-400 hover:text-blue-500 py-1.5 mb-2 rounded-lg hover:bg-blue-50/50 transition-all"
        @click="showAllTraces = true"
      >
        展开 {{ hiddenCount }} 条历史日志
      </button>

      <!-- Trace items -->
      <div class="space-y-1.5">
        <div
          v-for="(trace, i) in visibleTraces"
          :key="i"
          class="rounded-lg px-3 py-2 text-xs transition-all animate-isu-fade-in"
          :class="{
            'bg-blue-50 border border-blue-100': trace.status === 'running',
            'bg-white border border-gray-100': trace.status === 'completed',
            'bg-red-50 border border-red-100': trace.status === 'failed',
          }"
        >
          <div class="flex items-center gap-2 mb-0.5">
            <span
              class="w-1.5 h-1.5 rounded-full"
              :class="{
                'bg-blue-400 animate-pulse': trace.status === 'running',
                'bg-green-400': trace.status === 'completed',
                'bg-red-400': trace.status === 'failed',
              }"
            />
            <span class="font-semibold"
                  :class="{
                    'text-blue-700': trace.status === 'running',
                    'text-gray-700': trace.status === 'completed',
                    'text-red-700': trace.status === 'failed',
                  }">
              {{ trace.node }}
            </span>
            <span class="ml-auto text-[10px] text-gray-400">
              {{ new Date(trace.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }}
            </span>
          </div>
          <div class="text-gray-500 leading-relaxed">{{ trace.message }}</div>
        </div>
      </div>

      <!-- Empty -->
      <div
        v-if="traces.length === 0 && !streaming"
        class="flex flex-col items-center justify-center py-8 text-center"
      >
        <div class="text-xs text-gray-400">暂无工作日志</div>
        <div class="mt-1 text-[11px] text-gray-300">发送消息后将在此展示 Agent 工作过程</div>
      </div>

      <!-- Waiting -->
      <div
        v-if="traces.length === 0 && streaming"
        class="flex flex-col items-center justify-center py-8 text-center"
      >
        <div class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0ms" />
          <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 150ms" />
          <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 300ms" />
        </div>
        <div class="mt-2 text-xs text-gray-400">Agent 正在思考...</div>
      </div>

      <button
        v-if="traces.length > maxVisibleTraces && showAllTraces"
        class="w-full text-center text-[11px] text-gray-400 hover:text-blue-500 py-1.5 mt-1 rounded-lg hover:bg-blue-50/50 transition-all"
        @click="showAllTraces = false"
      >
        收起历史日志
      </button>
    </div>
  </div>
</template>
