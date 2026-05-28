<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Settings, Maximize2, Minimize2 } from 'lucide-vue-next';
import ConversationSidebar from '#/components/ai/ConversationSidebar.vue';
import ChatMessageBubble from '#/components/ai/ChatMessageBubble.vue';
import ChatInput from '#/components/ai/ChatInput.vue';
import AgentPanel from '#/components/trace/AgentPanel.vue';

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  unread: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    id: string;
    documentName: string;
    pageNumber?: number;
    chunkIndex: number;
    similarity: number;
    content: string;
    kbName: string;
  }>;
  isStream?: boolean;
  thinking?: boolean;
}

interface TraceLog {
  id: string;
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  node?: string;
}

const router = useRouter();
const messagesContainerRef = ref<HTMLElement | null>(null);
const isPanelExpanded = ref(true);

const currentConversationId = ref('conv-1');
const conversations = ref<Conversation[]>([
  { id: 'conv-1', title: '企业制度查询', lastMessage: '帮我查一下员工考勤制度', timestamp: new Date(), unread: 0 },
  { id: 'conv-2', title: '员工数据分析', lastMessage: '本月新入职员工有多少人', timestamp: new Date(Date.now() - 3600000), unread: 2 },
  { id: 'conv-3', title: '知识库上传', lastMessage: '上传了新的员工手册', timestamp: new Date(Date.now() - 7200000), unread: 0 },
]);

const messages = ref<Message[]>([
  {
    id: 'msg-1',
    role: 'user',
    content: '帮我查一下企业的员工考勤制度',
  },
  {
    id: 'msg-2',
    role: 'assistant',
    content: '收到老师～我正在搜索企业知识库，帮您查找相关的考勤制度信息。',
    sources: [
      {
        id: 'src-1',
        documentName: '企业员工手册.pdf',
        pageNumber: 15,
        chunkIndex: 42,
        similarity: 0.92,
        content: '员工考勤制度规定：工作日为周一至周五，正常工作时间为上午9:00至下午6:00，中午12:00-13:30为休息时间。',
        kbName: '公司制度库',
      },
    ],
  },
  {
    id: 'msg-3',
    role: 'assistant',
    content: '根据企业知识库中的《企业员工手册》，为您整理了以下考勤制度：\n\n**工作时间**\n- 工作日：周一至周五\n- 工作时段：上午9:00 - 下午6:00\n- 午休时间：12:00 - 13:30\n\n**考勤要求**\n- 员工需每日打卡上下班\n- 迟到30分钟以内视为迟到，超过30分钟视为旷工\n- 每月允许3次迟到，超过次数将影响绩效考核\n\n**请假制度**\n- 事假需提前1天申请\n- 病假需提供医院证明\n- 年假根据工龄计算：\n  - 1-3年：5天/年\n  - 3-5年：10天/年\n  - 5年以上：15天/年',
    sources: [
      {
        id: 'src-1',
        documentName: '企业员工手册.pdf',
        pageNumber: 15,
        chunkIndex: 42,
        similarity: 0.92,
        content: '员工考勤制度规定：工作日为周一至周五，正常工作时间为上午9:00至下午6:00，中午12:00-13:30为休息时间。',
        kbName: '公司制度库',
      },
      {
        id: 'src-2',
        documentName: '企业员工手册.pdf',
        pageNumber: 16,
        chunkIndex: 45,
        similarity: 0.88,
        content: '考勤管理：员工每日需通过考勤系统打卡，迟到30分钟以内记迟到一次，超过30分钟按旷工处理。',
        kbName: '公司制度库',
      },
    ],
  },
]);

const currentNode = ref('answer');
const nodeStatuses = ref<Record<string, 'pending' | 'running' | 'completed' | 'error'>>({
  start: 'completed',
  intent: 'completed',
  clarify: 'completed',
  retrieval: 'completed',
  rerank: 'completed',
  citation: 'completed',
  answer: 'completed',
  end: 'pending',
});

const traceLogs = ref<TraceLog[]>([
  { id: 'log-1', timestamp: new Date(Date.now() - 5000), level: 'info', message: '开始处理用户请求', node: 'START' },
  { id: 'log-2', timestamp: new Date(Date.now() - 4500), level: 'info', message: '识别用户意图：查询考勤制度', node: 'Intent' },
  { id: 'log-3', timestamp: new Date(Date.now() - 4000), level: 'info', message: '无需澄清，直接进入检索', node: 'Clarify' },
  { id: 'log-4', timestamp: new Date(Date.now() - 3500), level: 'info', message: '检索知识库，找到5个相关文档', node: 'Retrieval' },
  { id: 'log-5', timestamp: new Date(Date.now() - 3000), level: 'info', message: 'Rerank完成，筛选出2个最相关文档', node: 'Rerank' },
  { id: 'log-6', timestamp: new Date(Date.now() - 2500), level: 'info', message: '生成引用来源', node: 'Citation' },
  { id: 'log-7', timestamp: new Date(Date.now() - 1000), level: 'success', message: '回答生成完成', node: 'Answer' },
]);

const ragEnabled = ref(true);
const isLoading = ref(false);
const tokenCount = ref(1256);
const elapsedTime = ref(5000);

function selectConversation(id: string) {
  currentConversationId.value = id;
}

function createConversation() {
  const newId = `conv-${Date.now()}`;
  conversations.value.unshift({
    id: newId,
    title: '新对话',
    lastMessage: '',
    timestamp: new Date(),
    unread: 0,
  });
  currentConversationId.value = newId;
  messages.value = [];
}

function deleteConversation(id: string) {
  conversations.value = conversations.value.filter((c) => c.id !== id);
  if (currentConversationId.value === id) {
    currentConversationId.value = conversations.value[0]?.id || '';
  }
}

async function sendMessage(content: string) {
  isLoading.value = true;
  
  messages.value.push({
    id: `msg-${Date.now()}`,
    role: 'user',
    content,
  });

  await simulateResponse();
  
  isLoading.value = false;
}

async function simulateResponse() {
  const thinkingMsg: Message = {
    id: `msg-${Date.now()}`,
    role: 'assistant',
    content: '',
    thinking: true,
  };
  messages.value.push(thinkingMsg);

  await new Promise((resolve) => setTimeout(resolve, 2000));

  const thinkingIndex = messages.value.findIndex((m) => m.id === thinkingMsg.id);
  if (thinkingIndex !== -1) {
    messages.value[thinkingIndex] = {
      id: thinkingMsg.id,
      role: 'assistant',
      content: '好的老师，我来帮您分析这个问题...\n\n根据分析，您的问题涉及到企业的日常运营管理。以下是相关信息：\n\n**分析结果**\n\n1. **核心要点**：您提出的问题涉及到企业管理的多个方面\n2. **建议方向**：建议从以下几个维度考虑\n\n如果您需要更详细的信息，请告诉我！',
      sources: [
        {
          id: 'src-sim',
          documentName: '企业管理指南.pdf',
          chunkIndex: 15,
          similarity: 0.85,
          content: '企业管理涉及多个维度，包括人力资源、财务管理、运营管理等。',
          kbName: '企业知识库',
        },
      ],
    };
  }
}

function toggleRag() {
  ragEnabled.value = !ragEnabled.value;
}

function scrollToBottom() {
  if (messagesContainerRef.value) {
    messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight;
  }
}

onMounted(() => {
  scrollToBottom();
});
</script>

<template>
  <div class="h-screen flex bg-gray-100">
    <div class="w-80 flex-shrink-0">
      <ConversationSidebar
        :current-conversation-id="currentConversationId"
        :conversations="conversations"
        @select="selectConversation"
        @create="createConversation"
        @delete="deleteConversation"
      />
    </div>

    <div class="flex-1 flex flex-col min-w-0">
      <div class="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">
            {{ conversations.find((c) => c.id === currentConversationId)?.title || '新对话' }}
          </h2>
          <p class="text-sm text-gray-500">与 internSU AI 的对话</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="isPanelExpanded = !isPanelExpanded"
            class="w-8 h-8 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
            :title="isPanelExpanded ? '隐藏面板' : '显示面板'"
          >
            <component :is="isPanelExpanded ? Minimize2 : Maximize2" class="w-4 h-4 text-gray-600" />
          </button>
          <button class="w-8 h-8 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors">
            <Settings class="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      <div
        ref="messagesContainerRef"
        class="flex-1 overflow-y-auto p-6"
      >
        <ChatMessageBubble
          v-for="message in messages"
          :key="message.id"
          :message="message"
        />
      </div>

      <ChatInput
        :disabled="isLoading"
        :rag-enabled="ragEnabled"
        :tool-status="isLoading ? '正在思考中...' : undefined"
        :token-count="tokenCount"
        @send="sendMessage"
        @toggle-rag="toggleRag"
      />
    </div>

    <div v-show="isPanelExpanded" class="w-80 flex-shrink-0 border-l border-gray-200">
      <AgentPanel
        :current-node="currentNode"
        :node-statuses="nodeStatuses"
        :trace-logs="traceLogs"
        :sources="messages[messages.length - 1]?.sources"
        :token-count="tokenCount"
        :elapsed-time="elapsedTime"
      />
    </div>
  </div>
</template>