<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ChatInput from './components/ChatInput.vue';
import ChatMessageBubble from './components/ChatMessageBubble.vue';
import AgentTracePanel from './components/AgentTracePanel.vue';
import SourcePanel from './components/SourcePanel.vue';
import { chatStreamSSE, listConversations, createConversation, getMessages } from '#/api/core/chat';
import type { ChatMessage, AgentTrace, CitationSource } from '#/api/core/types';

const route = useRoute();
const router = useRouter();

// ── State ──
const messages = ref<ChatMessage[]>([]);
const isStreaming = ref(false);
const currentTrace = ref<AgentTrace[]>([]);
const currentSources = ref<CitationSource[]>([]);
const currentAnswer = ref('');
const convId = ref(route.query.conv as string || '');
const sessions = ref<{ id: string; title: string; updatedAt: string }[]>([]);
const showSessions = ref(true);
const showAgentPanel = ref(true);

// ── Lifecycle ──
onMounted(async () => {
  await loadSessions();
  if (convId.value) await loadMessages(convId.value);
});

// ── Session Management ──
async function loadSessions() {
  try {
    const res = await listConversations('1');
    sessions.value = (res.conversations || []).map((c: any) => ({
      id: c.conversation_id || c.id,
      title: c.title || '新对话',
      updatedAt: c.updated_at || c.create_time || '',
    }));
  } catch { /* graceful */ }
}

async function loadMessages(id: string) {
  try {
    const res = await getMessages(id);
    messages.value = (res.messages || []).map((m: any) => ({
      role: m.role,
      content: m.content,
      sources: m.sources || [],
      trace: m.trace || [],
    }));
  } catch { /* graceful */ }
}

async function newConversation() {
  messages.value = [];
  currentSources.value = [];
  currentTrace.value = [];
  currentAnswer.value = '';
  convId.value = '';
  router.replace({ query: {} });
}

async function selectSession(session: { id: string }) {
  convId.value = session.id;
  router.replace({ query: { conv: session.id } });
  await loadMessages(session.id);
}

// ── Send Message ──
async function sendMessage(content: string) {
  if (!content.trim() || isStreaming.value) return;

  // Add user message
  messages.value.push({ role: 'user', content });

  // Create conversation if needed
  if (!convId.value) {
    try {
      const res = await createConversation('1', content.slice(0, 30));
      convId.value = res.conversation_id;
      router.replace({ query: { conv: convId.value } });
      await loadSessions();
    } catch { /* use temp id */ }
  }

  // Start streaming
  isStreaming.value = true;
  currentAnswer.value = '';
  currentSources.value = [];
  currentTrace.value = [];

  try {
    const response = await chatStreamSSE({
      user_id: '1',
      conversation_id: convId.value,
      message: content,
      model: 'deepseek-chat',
    });

    if (!response.ok || !response.body) throw new Error('Stream failed');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data) continue;

          try {
            const event = JSON.parse(data);
            handleSSEEvent(event);
          } catch { /* skip malformed */ }
        }
      }
    }
  } catch (err: any) {
    currentAnswer.value = currentAnswer.value || '收到老师～连接暂时中断，请稍后再试～';
  } finally {
    // Finalize assistant message
    if (currentAnswer.value) {
      messages.value.push({
        role: 'assistant',
        content: currentAnswer.value,
        sources: [...currentSources.value],
        trace: [...currentTrace.value],
      });
    }
    isStreaming.value = false;
    currentAnswer.value = '';
    await loadSessions();
  }
}

function handleSSEEvent(event: any) {
  const type = event.type || event.event || '';

  switch (type) {
    case 'token':
    case 'delta':
      currentAnswer.value += event.content || event.data || '';
      break;
    case 'trace':
    case 'step':
      currentTrace.value.push({
        node: event.node || event.step || '',
        message: event.message || '',
        status: event.status || 'running',
        timestamp: Date.now(),
      });
      break;
    case 'source':
    case 'citation':
      if (event.sources) {
        currentSources.value = event.sources;
      } else if (event.document_name) {
        currentSources.value.push({
          document_name: event.document_name,
          page_number: event.page_number,
          relevance_score: event.score || event.relevance_score,
          knowledge_base: event.knowledge_base || '',
          excerpt: event.excerpt || '',
        });
      }
      break;
    case 'done':
    case 'complete':
      // Stream complete
      break;
    default:
      // Try to extract content from any event
      if (event.content && !currentAnswer.value) {
        currentAnswer.value = event.content;
      }
  }
}
</script>

<template>
  <div class="flex h-full">
    <!-- Left: Session sidebar -->
    <aside
      v-show="showSessions"
      class="w-64 shrink-0 border-r border-gray-200/80 bg-white flex flex-col"
    >
      <div class="p-3">
        <button
          class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-left text-sm text-gray-600
                 hover:border-blue-200 hover:bg-blue-50/50 transition-all duration-150 flex items-center gap-2"
          @click="newConversation"
        >
          <span class="text-lg">+</span>
          <span>新建对话</span>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto px-2">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="mb-0.5 cursor-pointer rounded-lg px-3 py-2 text-sm transition-all duration-150"
          :class="convId === session.id
            ? 'bg-blue-50 text-blue-700 font-medium'
            : 'text-gray-600 hover:bg-gray-50'"
          @click="selectSession(session)"
        >
          <div class="truncate">{{ session.title }}</div>
          <div class="mt-0.5 text-[11px] text-gray-400">
            {{ session.updatedAt?.slice(0, 10) }}
          </div>
        </div>

        <div
          v-if="sessions.length === 0"
          class="p-4 text-center text-xs text-gray-400"
        >
          暂无历史会话
        </div>
      </div>
    </aside>

    <!-- Center: Chat area -->
    <div class="flex flex-1 flex-col min-w-0">
      <!-- Toggle sidebar button -->
      <button
        class="absolute left-0 top-1/2 z-10 -translate-y-1/2 rounded-r-lg border border-l-0
               border-gray-200 bg-white px-1 py-4 text-gray-400 hover:text-gray-600 transition-colors"
        :class="{ 'left-64': showSessions }"
        @click="showSessions = !showSessions"
      >
        {{ showSessions ? '◂' : '▸' }}
      </button>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto px-6 py-4" ref="messagesContainer">
        <!-- Welcome when empty -->
        <div
          v-if="messages.length === 0 && !isStreaming"
          class="flex flex-col items-center justify-center h-full text-center"
        >
          <div class="mb-4 text-4xl">👋</div>
          <h1 class="mb-2 text-xl font-semibold text-gray-800">
            老师，今天想让我帮您做什么？
          </h1>
          <p class="mb-8 text-sm text-gray-500">
            我是小SU，您的AI实习生。可以帮您查询制度、分析数据、整理知识。
          </p>

          <!-- Quick actions -->
          <div class="grid grid-cols-2 gap-3 max-w-md">
            <button
              v-for="action in quickActions"
              :key="action.label"
              class="rounded-xl border border-gray-200 bg-white px-4 py-3 text-left
                     hover:border-blue-200 hover:bg-blue-50/30 transition-all duration-150"
              @click="sendMessage(action.prompt)"
            >
              <div class="text-sm font-medium text-gray-700">{{ action.label }}</div>
              <div class="mt-0.5 text-xs text-gray-400">{{ action.desc }}</div>
            </button>
          </div>
        </div>

        <!-- Message bubbles -->
        <ChatMessageBubble
          v-for="(msg, i) in messages"
          :key="i"
          :message="msg"
          @cite-click="(src: CitationSource) => currentSources = [src]"
        />

        <!-- Streaming answer -->
        <div
          v-if="isStreaming && currentAnswer"
          class="mb-4 rounded-2xl bg-blue-50/50 px-5 py-3"
        >
          <div class="mb-1 text-xs font-medium text-blue-600">小SU 正在回复...</div>
          <div class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {{ currentAnswer }}
            <span class="inline-block w-1.5 h-4 bg-blue-500 animate-pulse align-middle ml-0.5" />
          </div>
        </div>
      </div>

      <!-- Chat Input -->
      <div class="shrink-0 border-t border-gray-200/80 bg-white px-6 py-4">
        <ChatInput
          :disabled="isStreaming"
          @send="sendMessage"
        />
      </div>
    </div>

    <!-- Right: Agent panel -->
    <aside
      v-show="showAgentPanel"
      class="w-80 shrink-0 border-l border-gray-200/80 bg-white overflow-y-auto"
    >
      <div class="p-1">
        <AgentTracePanel :traces="currentTrace" :streaming="isStreaming" />
        <SourcePanel :sources="currentSources" />
      </div>
    </aside>

    <!-- Toggle agent panel -->
    <button
      class="absolute right-0 top-1/2 z-10 -translate-y-1/2 rounded-l-lg border border-r-0
             border-gray-200 bg-white px-1 py-4 text-gray-400 hover:text-gray-600 transition-colors"
      :class="{ 'right-80': showAgentPanel }"
      @click="showAgentPanel = !showAgentPanel"
    >
      {{ showAgentPanel ? '▸' : '◂' }}
    </button>
  </div>
</template>

<script lang="ts">
const quickActions = [
  { label: '查询企业制度', desc: '搜索公司规章制度', prompt: '帮我查询公司请假制度' },
  { label: '查询企业数据', desc: '分析数据库数据', prompt: '统计本月各部门人数' },
  { label: '上传知识库', desc: '添加企业文档', prompt: '我想上传一份文档到知识库' },
  { label: 'AI问答', desc: '问任何企业相关的问题', prompt: '员工手册中关于年假的规定是什么？' },
];
</script>
