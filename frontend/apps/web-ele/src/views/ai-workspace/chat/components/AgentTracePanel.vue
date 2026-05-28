<script setup lang="ts">
import { computed } from 'vue';
import type { AgentTrace } from '#/api/core/types';

const props = defineProps<{
  traces: AgentTrace[];
  streaming: boolean;
}>();

const visibleTraces = computed(() => {
  // Show last 8 traces when not streaming, all when streaming
  return props.streaming ? props.traces : props.traces.slice(-8);
});

const graphNodes = [
  { id: 'intent', label: '意图识别', icon: '🔍' },
  { id: 'clarify', label: '信息确认', icon: '❓' },
  { id: 'retrieval', label: '知识检索', icon: '📚' },
  { id: 'rerank', label: '结果重排', icon: '📊' },
  { id: 'citation', label: '引用构建', icon: '📎' },
  { id: 'answer', label: '回答生成', icon: '✨' },
];

function isNodeActive(nodeId: string): boolean {
  return props.traces.some(
    (t) => t.node?.toLowerCase().includes(nodeId) || t.message?.includes(nodeId),
  );
}

function nodeStatus(nodeId: string): 'done' | 'running' | 'pending' {
  const nodeTraces = props.traces.filter(
    (t) => t.node?.toLowerCase().includes(nodeId) || t.message?.includes(nodeId),
  );
  if (nodeTraces.length === 0) return 'pending';
  if (nodeTraces.some((t) => t.status === 'completed')) return 'done';
  return 'running';
}
</script>

<template>
  <div class="px-3 py-4">
    <!-- Graph flow visualization -->
    <div class="mb-4">
      <div class="mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Agent 工作流
      </div>
      <div class="flex flex-col gap-1">
        <div
          v-for="(node, i) in graphNodes"
          :key="node.id"
          class="flex items-center gap-2"
        >
          <!-- Connector line -->
          <div
            v-if="i > 0"
            class="ml-2.5 h-4 w-px"
            :class="nodeStatus(graphNodes[i-1].id) === 'done' ? 'bg-blue-300' : 'bg-gray-200'"
          />

          <!-- Node circle -->
          <div
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] transition-all duration-300"
            :class="{
              'bg-blue-500 text-white shadow-sm shadow-blue-200': nodeStatus(node.id) === 'running',
              'bg-green-100 text-green-700': nodeStatus(node.id) === 'done',
              'bg-gray-100 text-gray-400': nodeStatus(node.id) === 'pending',
            }"
          >
            <span v-if="nodeStatus(node.id) === 'running'" class="animate-pulse">●</span>
            <span v-else-if="nodeStatus(node.id) === 'done'">✓</span>
            <span v-else>○</span>
          </div>

          <span
            class="text-xs transition-colors duration-300"
            :class="{
              'text-blue-700 font-medium': nodeStatus(node.id) === 'running',
              'text-gray-700': nodeStatus(node.id) === 'done',
              'text-gray-400': nodeStatus(node.id) === 'pending',
            }"
          >
            {{ node.label }}
          </span>
        </div>
      </div>
    </div>

    <!-- Trace log -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          执行日志
        </span>
        <span
          v-if="streaming"
          class="text-[11px] text-blue-500 animate-pulse"
        >
          处理中...
        </span>
      </div>

      <div class="space-y-1 max-h-64 overflow-y-auto">
        <div
          v-for="(trace, i) in visibleTraces"
          :key="i"
          class="flex items-start gap-2 rounded-md px-2 py-1.5 text-xs transition-all"
          :class="{
            'bg-blue-50 text-blue-700': trace.status === 'running',
            'text-gray-600': trace.status !== 'running',
          }"
        >
          <span class="mt-0.5 shrink-0">
            {{ trace.status === 'running' ? '⏳' : trace.status === 'completed' ? '✅' : '·' }}
          </span>
          <span class="leading-relaxed">{{ trace.message }}</span>
        </div>

        <div
          v-if="traces.length === 0 && !streaming"
          class="py-4 text-center text-xs text-gray-400"
        >
          暂无执行日志
        </div>
      </div>
    </div>
  </div>
</template>
