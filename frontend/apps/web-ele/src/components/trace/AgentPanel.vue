<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ChevronRight, CheckCircle, Loader2, AlertCircle, Circle, Code, Database, GitBranch, FileText, Brain, TrendingUp, Zap } from 'lucide-vue-next';

interface TraceLog {
  id: string;
  timestamp: Date;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
  node?: string;
}

interface Node {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  icon: typeof ChevronRight;
  duration?: number;
}

const props = defineProps<{
  isActive?: boolean;
}>();

const nodes = ref<Node[]>([
  { id: 'start', name: 'START', status: 'completed', icon: Circle, duration: 120 },
  { id: 'intent', name: 'Intent', status: 'completed', icon: Brain, duration: 450 },
  { id: 'clarify', name: 'Clarify', status: 'completed', icon: GitBranch, duration: 320 },
  { id: 'retrieval', name: 'Retrieval', status: 'running', icon: Database, duration: 890 },
  { id: 'rerank', name: 'Rerank', status: 'pending', icon: TrendingUp },
  { id: 'citation', name: 'Citation', status: 'pending', icon: FileText },
  { id: 'answer', name: 'Answer', status: 'pending', icon: CheckCircle },
  { id: 'end', name: 'END', status: 'pending', icon: Circle },
]);

const currentNodeId = ref('retrieval');

const traceLogs = ref<TraceLog[]>([
  { id: 'log-1', timestamp: new Date(Date.now() - 2000), level: 'info', message: '开始处理用户请求...', node: 'start' },
  { id: 'log-2', timestamp: new Date(Date.now() - 1800), level: 'success', message: '意图识别完成：用户查询企业制度', node: 'intent' },
  { id: 'log-3', timestamp: new Date(Date.now() - 1500), level: 'info', message: '检查是否需要澄清...', node: 'clarify' },
  { id: 'log-4', timestamp: new Date(Date.now() - 1200), level: 'success', message: '意图明确，无需澄清', node: 'clarify' },
  { id: 'log-5', timestamp: new Date(Date.now() - 800), level: 'info', message: '开始检索知识库...', node: 'retrieval' },
  { id: 'log-6', timestamp: new Date(Date.now() - 500), level: 'info', message: '查询向量数据库，检索相关文档', node: 'retrieval' },
  { id: 'log-7', timestamp: new Date(Date.now() - 200), level: 'info', message: '找到 12 个相关文档片段', node: 'retrieval' },
]);

const tokenUsage = ref({
  prompt: 245,
  completion: 89,
  total: 334,
  limit: 4096,
});

const citations = ref([
  { id: 'c1', source: '企业员工手册.pdf', page: 15, chunk: 42, similarity: 0.92 },
  { id: 'c2', source: '公司规章制度.pdf', page: 8, chunk: 17, similarity: 0.87 },
  { id: 'c3', source: 'HR政策汇编.pdf', page: 23, chunk: 56, similarity: 0.81 },
]);

const expandedLogs = ref(true);
const expandedCitations = ref(true);

const progress = computed(() => {
  const completed = nodes.value.filter(n => n.status === 'completed').length;
  return (completed / nodes.value.length) * 100;
});

const tokenProgress = computed(() => {
  return (tokenUsage.value.total / tokenUsage.value.limit) * 100;
});

function getNodeStatusClass(status: string) {
  const classes = {
    completed: 'bg-green-100 text-green-600',
    running: 'bg-blue-500 text-white animate-pulse',
    error: 'bg-red-100 text-red-600',
    pending: 'bg-gray-100 text-gray-400',
  };
  return classes[status as keyof typeof classes] || classes.pending;
}

function getLogLevelClass(level: string) {
  const classes = {
    info: 'text-blue-600',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
  };
  return classes[level as keyof typeof classes] || classes.info;
}

function formatTime(date: Date) {
  return date.toLocaleTimeString('zh-CN', { hour12: false });
}

watch(() => props.isActive, (active) => {
  if (active) {
    simulateProcess();
  }
});

function simulateProcess() {
  setTimeout(() => {
    const idx = nodes.value.findIndex(n => n.status === 'running');
    if (idx >= 0 && idx < nodes.value.length - 1) {
      nodes.value[idx].status = 'completed';
      nodes.value[idx + 1].status = 'running';
      currentNodeId.value = nodes.value[idx + 1].id;
      
      traceLogs.value.push({
        id: `log-${Date.now()}`,
        timestamp: new Date(),
        level: 'success',
        message: `${nodes.value[idx].name} 节点处理完成`,
        node: nodes.value[idx].id,
      });

      if (nodes.value[idx + 1].id === 'retrieval') {
        citations.value = [
          { id: 'c1', source: '企业员工手册.pdf', page: 15, chunk: 42, similarity: 0.92 },
          { id: 'c2', source: '公司规章制度.pdf', page: 8, chunk: 17, similarity: 0.87 },
        ];
      }
    }
  }, 2000);
}
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50">
    <div class="p-4 border-b border-gray-200">
      <h3 class="font-semibold text-gray-900">Agent 工作流</h3>
      <div class="mt-3">
        <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>处理进度</span>
          <span>{{ Math.round(progress) }}%</span>
        </div>
        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>
    </div>

    <div class="p-4 border-b border-gray-200">
      <div class="flex items-center gap-2">
        <div 
          v-for="(node, index) in nodes" 
          :key="node.id"
          class="flex items-center"
        >
          <div 
            class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-medium transition-all"
            :class="[getNodeStatusClass(node.status)]"
          >
            <component :is="node.icon" class="w-4 h-4" />
          </div>
          <ChevronRight 
            v-if="index < nodes.length - 1" 
            class="w-4 h-4 text-gray-300 mx-1" 
          />
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div class="border-b border-gray-200">
        <button 
          @click="expandedLogs = !expandedLogs"
          class="w-full p-4 flex items-center justify-between hover:bg-gray-100 transition-colors"
        >
          <div class="flex items-center gap-2">
            <Code class="w-4 h-4 text-gray-500" />
            <span class="font-medium text-gray-700">Trace 日志</span>
          </div>
          <ChevronRight 
            class="w-4 h-4 text-gray-400 transition-transform"
            :class="{ 'rotate-90': expandedLogs }"
          />
        </button>
        <div v-if="expandedLogs" class="px-4 pb-4 space-y-2 max-h-[200px] overflow-y-auto">
          <div 
            v-for="log in traceLogs" 
            :key="log.id"
            class="flex items-start gap-2 text-sm"
          >
            <span class="text-xs text-gray-400 flex-shrink-0">{{ formatTime(log.timestamp) }}</span>
            <span :class="getLogLevelClass(log.level)">{{ log.message }}</span>
          </div>
        </div>
      </div>

      <div class="border-b border-gray-200">
        <button 
          @click="expandedCitations = !expandedCitations"
          class="w-full p-4 flex items-center justify-between hover:bg-gray-100 transition-colors"
        >
          <div class="flex items-center gap-2">
            <Database class="w-4 h-4 text-gray-500" />
            <span class="font-medium text-gray-700">引用来源</span>
            <span class="px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full text-xs">
              {{ citations.length }}
            </span>
          </div>
          <ChevronRight 
            class="w-4 h-4 text-gray-400 transition-transform"
            :class="{ 'rotate-90': expandedCitations }"
          />
        </button>
        <div v-if="expandedCitations" class="px-4 pb-4 space-y-2">
          <div 
            v-for="citation in citations" 
            :key="citation.id"
            class="p-2 bg-white rounded-lg text-sm"
          >
            <div class="font-medium text-gray-900">{{ citation.source }}</div>
            <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
              <span>页码: {{ citation.page }}</span>
              <span>Chunk: {{ citation.chunk }}</span>
              <span class="text-blue-500">相似度: {{ (citation.similarity * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4">
        <div class="flex items-center gap-2 mb-3">
          <Zap class="w-4 h-4 text-yellow-500" />
          <span class="font-medium text-gray-700">Token 统计</span>
        </div>
        <div class="space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-500">Prompt</span>
            <span class="font-medium text-gray-900">{{ tokenUsage.prompt }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-500">Completion</span>
            <span class="font-medium text-gray-900">{{ tokenUsage.completion }}</span>
          </div>
          <div class="pt-2 border-t border-gray-200">
            <div class="flex items-center justify-between text-sm mb-1">
              <span class="text-gray-700 font-medium">Total</span>
              <span class="font-medium text-gray-900">{{ tokenUsage.total }} / {{ tokenUsage.limit }}</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full transition-all"
                :style="{ width: `${tokenProgress}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
