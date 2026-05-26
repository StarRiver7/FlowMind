<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';
import { useChatStore } from '#/store';
import type { SourceCitation } from '#/api';
import { chatStreamSSE, createConversation, listConversations, getMessages, listDocuments } from '#/api';
import ChatMessageBubble from './components/ChatMessageBubble.vue';
import ChatInput from './components/ChatInput.vue';
import SourcePanel from './components/SourcePanel.vue';
import AgentTracePanel from './components/AgentTracePanel.vue';

const store = useChatStore();
const inputRef = ref<InstanceType<typeof ChatInput> | null>(null);
const chatContainer = ref<HTMLElement | null>(null);
const loadingConvs = ref(false);
const showRightPanel = ref(true);

// 加载会话列表
async function loadConversations() {
  loadingConvs.value = true;
  try {
    const userId = localStorage.getItem('flowmind_user');
    if (!userId) return;
    const u = JSON.parse(userId);
    const res = await listConversations(u.userId);
    store.setConversations(res.conversations ?? []);
  } catch { /* ignore */ }
  loadingConvs.value = false;
}

// 切换会话
async function switchConversation(id: string | null) {
  store.setCurrentConversation(id);
  if (id) {
    try {
      const res = await getMessages(id);
      const msgs = (res.messages ?? []).map((m: any) => ({
        id: m.id ?? String(Date.now()),
        role: m.role,
        content: m.content,
        timestamp: Date.now(),
      }));
      store.messages = msgs;
    } catch { /* ignore */ }
  }
  await nextTick();
  scrollToBottom();
}

// 新建会话
async function newConversation() {
  const userId = (() => {
    try { return JSON.parse(localStorage.getItem('flowmind_user') ?? '{}').userId; } catch { return '0'; }
  })();
  try {
    const res = await createConversation(userId, '新对话');
    const convId = res.conversation_id;
    await loadConversations();
    await switchConversation(convId);
  } catch {
    store.setCurrentConversation(null);
    store.clearMessages();
  }
}

// 发送消息
async function handleSend(text: string) {
  if (!text.trim() || store.isStreaming) return;

  let convId = store.currentConversationId;
  if (!convId) {
    const userId = (() => {
      try { return JSON.parse(localStorage.getItem('flowmind_user') ?? '{}').userId; } catch { return '0'; }
    })();
    const res = await createConversation(userId, text.slice(0, 30));
    convId = res.conversation_id;
    store.setCurrentConversation(convId);
    loadConversations();
  }

  // 添加用户消息
  store.addMessage({
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: Date.now(),
  });

  // 添加 AI 占位消息
  store.addMessage({
    id: `ai-${Date.now()}`,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    streaming: true,
  });
  store.isStreaming = true;
  store.selectedSources = [];
  store.agentTrace = [];

  await nextTick();
  scrollToBottom();

  // SSE 流式请求
  try {
    const response = await chatStreamSSE({
      conversation_id: convId,
      user_id: (() => {
        try { return JSON.parse(localStorage.getItem('flowmind_user') ?? '{}').userId; } catch { return '0'; }
      })(),
      message: text,
      stream: true,
      use_rag: true,
      use_tools: true,
    });

    const reader = response.body?.getReader();
    if (!reader) return;
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'token') {
              store.appendToLastMessage(event.content ?? '');
            } else if (event.type === 'error') {
              store.appendToLastMessage(`\n\n> 错误: ${event.content}`);
            } else if (event.type === 'done') {
              store.setSources(event.sources ?? []);
              store.finishStreaming();
            } else if (event.type === 'thinking') {
              store.addAgentTrace(event.content ?? '');
            }
          } catch { /* ignore parse errors */ }
        }
      }
      await nextTick();
      scrollToBottom();
    }
  } catch (e: any) {
    store.appendToLastMessage(`\n\n> 连接失败: ${e.message}`);
  }
  store.finishStreaming();
}

function handleStop() {
  store.finishStreaming();
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
}

// 监听新消息时滚动
watch(() => store.messages.length, () => {
  nextTick(() => scrollToBottom());
});

// 初始化
loadConversations();
</script>

<template>
  <div class="ai-chat-workspace">
    <!-- 左侧：会话列表 -->
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <h3>会话</h3>
        <el-button type="primary" size="small" :icon="'Plus'" @click="newConversation">
          新建
        </el-button>
      </div>
      <div class="conversation-list" v-loading="loadingConvs">
        <div
          v-for="conv in store.conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: String(conv.id) === store.currentConversationId }"
          @click="switchConversation(String(conv.id))"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span class="conv-title">{{ conv.title || '未命名会话' }}</span>
          <span class="conv-count">{{ conv.messageCount ?? 0 }}</span>
        </div>
        <el-empty v-if="!loadingConvs && store.conversations.length === 0" description="暂无会话" />
      </div>
    </aside>

    <!-- 中间：聊天区域 -->
    <main class="chat-main">
      <div class="chat-messages" ref="chatContainer">
        <div v-if="store.messages.length === 0" class="chat-welcome">
          <h1>FlowMind AI</h1>
          <p>企业级 AI 知识工作台。开始对话，探索你的知识库。</p>
        </div>
        <ChatMessageBubble
          v-for="msg in store.messages"
          :key="msg.id"
          :message="msg"
        />
      </div>
      <div class="chat-input-area">
        <ChatInput
          ref="inputRef"
          :streaming="store.isStreaming"
          @send="handleSend"
          @stop="handleStop"
        />
      </div>
    </main>

    <!-- 右侧：引用来源 + Agent 链路 -->
    <aside v-if="showRightPanel" class="chat-right-panel">
      <el-tabs model-value="sources">
        <el-tab-pane label="引用来源" name="sources">
          <SourcePanel :sources="store.selectedSources" />
        </el-tab-pane>
        <el-tab-pane label="Agent 链路" name="agent">
          <AgentTracePanel :trace="store.agentTrace" />
        </el-tab-pane>
      </el-tabs>
    </aside>
  </div>
</template>

<style scoped>
.ai-chat-workspace {
  display: flex;
  height: calc(100vh - var(--vben-header-height, 48px) - 2px);
  overflow: hidden;
  background: var(--el-bg-color-page);
}

.chat-sidebar {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;
}

.conv-item:hover {
  background: var(--el-fill-color-light);
}

.conv-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-count {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
}

.chat-welcome h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.chat-input-area {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 16px 32px 24px;
  background: var(--el-bg-color);
}

.chat-right-panel {
  width: 300px;
  flex-shrink: 0;
  border-left: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  overflow-y: auto;
}
</style>
