<!-- AI Chat Workspace - 3-column layout with SSE streaming -->
<script setup lang="ts">
import { onMounted, ref, watch, nextTick, computed } from 'vue';
import { useChatStore } from '#/store/chat';
import { useConversationStore } from '#/store/conversation';
import { useUserStore } from '@vben/stores';
import { ElMessage } from 'element-plus';

const chatStore = useChatStore();
const convStore = useConversationStore();
const userStore = useUserStore();
const msgContainer = ref<HTMLElement | null>(null);
const inputText = ref('');
const userId = computed(() => String(userStore.userInfo?.id || 'demo-user'));

// Auto-scroll on new messages
watch(
  () => chatStore.messages.length,
  () => scrollToBottom(),
);
watch(
  () => chatStore.lastMessage?.content,
  () => scrollToBottom(),
);

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
    }
  });
}

onMounted(async () => {
  await convStore.fetchList(userId.value);
});

async function handleSend() {
  const text = inputText.value.trim();
  if (!text) return;
  inputText.value = '';

  if (!convStore.currentId) {
    await convStore.newAndSwitch(userId.value, chatStore);
  }
  if (!convStore.currentId) {
    ElMessage.warning('请先创建会话');
    return;
  }

  await chatStore.sendMessage({
    user_id: userId.value,
    conversation_id: convStore.currentId,
    message: text,
    stream: true,
    use_rag: true,
    use_tools: true,
  });

  convStore.fetchList(userId.value);
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

function handleStop() {
  chatStore.stopGeneration();
}

async function handleSelectConversation(id: string) {
  await convStore.switchTo(id, chatStore);
}

async function handleNewConversation() {
  await convStore.newAndSwitch(userId.value, chatStore);
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

// Source score style
function scoreClass(score: number): string {
  if (score >= 0.7) return 'high';
  if (score >= 0.4) return 'mid';
  return 'low';
}

// Trace step display
function traceStatusText(status: string): string {
  const map: Record<string, string> = { pending: '等待中', running: '执行中', completed: '已完成', error: '失败' };
  return map[status] || status;
}

const sources = computed(() => chatStore.currentSources);
const traceSteps = computed(() => chatStore.traceSteps);
</script>

<template>
  <div class="ai-chat-workspace">
    <!-- Left: Conversation List -->
    <aside class="workspace-sidebar">
      <div class="sidebar-header">
        <h3 class="sidebar-title">会话列表</h3>
        <el-button type="primary" size="small" @click="handleNewConversation">
          + 新会话
        </el-button>
      </div>
      <div class="sidebar-list">
        <div
          v-for="conv in convStore.sortedConversations"
          :key="conv.conversation_id"
          :class="['conv-item', { active: conv.conversation_id === convStore.currentId }]"
          @click="handleSelectConversation(conv.conversation_id)"
        >
          <div class="conv-title">{{ conv.title || '新会话' }}</div>
          <div class="conv-meta">
            <span>{{ conv.message_count }} 条消息</span>
            <span>{{ new Date(conv.updated_at).toLocaleDateString() }}</span>
          </div>
        </div>
        <div v-if="convStore.conversations.length === 0" class="empty-list">
          暂无会话，点击上方按钮创建
        </div>
      </div>
    </aside>

    <!-- Center: Chat Area -->
    <main class="workspace-main">
      <div ref="msgContainer" class="msg-container">
        <!-- Welcome -->
        <div v-if="!chatStore.hasMessages && !chatStore.streaming" class="welcome">
          <div class="welcome-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <rect width="64" height="64" rx="16" fill="url(#grad)" />
              <path d="M20 26h24M20 32h18M20 38h14" stroke="#fff" stroke-width="2.5" stroke-linecap="round" />
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="64" y2="64">
                  <stop offset="0%" stop-color="#6366f1" />
                  <stop offset="100%" stop-color="#3b82f6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1>FlowMind AI 工作台</h1>
          <p class="welcome-desc">企业级 AI 助手，支持知识库检索与智能问答</p>
          <div class="welcome-hints">
            <span class="hint" @click="inputText = '请介绍知识库中有哪些文档'">📄 查询文档</span>
            <span class="hint" @click="inputText = '解释一下系统的认证流程'">🔐 认证流程</span>
            <span class="hint" @click="inputText = '总结一下部署架构'">☁️ 系统架构</span>
          </div>
        </div>

        <!-- Messages -->
        <div v-for="msg in chatStore.messages" :key="msg.id" :class="['msg-row', msg.role]">
          <div class="msg-avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
          <div class="msg-body">
            <div :class="['msg-bubble', msg.role, { thinking: msg.thinking }]">
              <template v-if="msg.thinking">
                <span class="thinking-text">{{ msg.content || '思考中...' }}</span>
              </template>
              <template v-else>
                <div class="msg-content" v-html="msg.content.replace(/\n/g, '<br>')" />
                <span v-if="msg.streaming" class="cursor-blink">▍</span>
              </template>
            </div>
            <!-- Source chips (inline) -->
            <div v-if="msg.sources?.length && !msg.streaming" class="msg-sources-inline">
              <span
                v-for="(src, i) in msg.sources"
                :key="i"
                class="source-chip"
              >
                📎 {{ src.file }} ({{ (src.score * 100).toFixed(0) }}%)
              </span>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="chatStore.error" class="error-banner">
          ⚠️ {{ chatStore.error }}
        </div>
      </div>

      <!-- Input -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            v-model="inputText"
            class="input-field"
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
            rows="1"
            :disabled="chatStore.streaming"
            @keydown="handleKeydown"
            @input="autoResize"
          />
          <el-button
            v-if="chatStore.streaming"
            type="danger"
            size="small"
            @click="handleStop"
          >
            停止
          </el-button>
          <el-button
            v-else
            type="primary"
            size="small"
            :disabled="!inputText.trim()"
            @click="handleSend"
          >
            发送
          </el-button>
        </div>
      </div>
    </main>

    <!-- Right: Panels (Sources + Trace) -->
    <aside class="workspace-panel">
      <!-- Sources -->
      <div class="panel-section">
        <div class="panel-header">
          <h4>引用来源</h4>
          <span class="badge">{{ sources.length }}</span>
        </div>
        <div v-if="sources.length === 0" class="panel-empty">
          暂无引用来源
        </div>
        <div v-else class="source-list">
          <div v-for="(src, i) in sources" :key="i" class="source-card">
            <div class="source-top">
              <span class="source-num">#{{ i + 1 }}</span>
              <span class="source-file">{{ src.file }}</span>
              <span :class="['source-score', scoreClass(src.score)]">
                {{ (src.score * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="source-excerpt">{{ src.excerpt }}</div>
          </div>
        </div>
      </div>

      <!-- Agent Trace -->
      <div class="panel-section">
        <div class="panel-header">
          <h4>Agent 执行链路</h4>
        </div>
        <div v-if="traceSteps.length === 0" class="panel-empty">
          暂无执行数据
        </div>
        <div v-else class="trace-list">
          <div v-for="(step, i) in traceSteps" :key="i" class="trace-step">
            <div class="trace-dot" :class="step.status" />
            <div class="trace-info">
              <div class="trace-node">{{ step.node }}</div>
              <div :class="['trace-status', step.status]">{{ traceStatusText(step.status) }}</div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.ai-chat-workspace {
  display: flex;
  height: calc(100vh - var(--vben-header-height, 48px) - var(--vben-tab-height, 0px));
  background: var(--el-bg-color);
}

/* ---- Sidebar ---- */
.workspace-sidebar {
  width: 260px;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.sidebar-title { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); margin: 0; }
.sidebar-list { flex: 1; overflow-y: auto; padding: 4px; }
.conv-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}
.conv-item:hover { background: var(--el-fill-color-light); }
.conv-item.active { background: var(--el-color-primary-light-9); }
.conv-title { font-size: 13px; color: var(--el-text-color-primary); margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-meta { font-size: 11px; color: var(--el-text-color-placeholder); display: flex; gap: 8px; }
.empty-list { text-align: center; padding: 24px 12px; font-size: 13px; color: var(--el-text-color-placeholder); }

/* ---- Main ---- */
.workspace-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.msg-container { flex: 1; overflow-y: auto; padding: 20px 24px; }
.welcome { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; }
.welcome-icon { margin-bottom: 16px; }
.welcome h1 { font-size: 24px; font-weight: 600; color: var(--el-text-color-primary); margin: 0 0 8px; }
.welcome-desc { color: var(--el-text-color-secondary); font-size: 14px; margin: 0 0 20px; }
.welcome-hints { display: flex; gap: 8px; }
.hint { padding: 8px 14px; background: var(--el-fill-color); border: 1px solid var(--el-border-color); border-radius: 20px; cursor: pointer; font-size: 13px; color: var(--el-text-color-secondary); transition: all 0.15s; }
.hint:hover { border-color: var(--el-color-primary); color: var(--el-color-primary); }

/* Messages */
.msg-row { display: flex; gap: 10px; margin-bottom: 18px; }
.msg-row.user { flex-direction: row-reverse; }
.msg-avatar {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; flex-shrink: 0;
}
.msg-row:not(.user) .msg-avatar { background: linear-gradient(135deg, #6366f1, #3b82f6); color: #fff; }
.msg-row.user .msg-avatar { background: var(--el-color-primary); color: #fff; }
.msg-body { min-width: 0; max-width: 70%; }
.msg-row.user .msg-body { max-width: 60%; }
.msg-bubble { padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-break: break-word; }
.msg-bubble:not(.user) { background: var(--el-fill-color); border-bottom-left-radius: 4px; }
.msg-bubble.user { background: var(--el-color-primary); color: #fff; border-bottom-right-radius: 4px; }
.msg-bubble.thinking { background: transparent; padding: 4px 14px; }
.thinking-text { color: var(--el-text-color-placeholder); font-style: italic; font-size: 13px; }
.msg-content { white-space: pre-wrap; }
.cursor-blink { animation: blink 1s step-end infinite; color: var(--el-color-primary); }
@keyframes blink { 50% { opacity: 0; } }

.msg-sources-inline { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.source-chip { font-size: 11px; padding: 2px 8px; background: var(--el-fill-color); border-radius: 4px; color: var(--el-color-primary); }

.error-banner { padding: 10px 14px; margin: 8px 0; background: var(--el-color-danger-light-9); border: 1px solid var(--el-color-danger-light-7); border-radius: 6px; font-size: 13px; color: var(--el-color-danger); }

/* Input */
.input-area { padding: 12px 20px 16px; background: var(--el-bg-color); border-top: 1px solid var(--el-border-color-light); }
.input-wrapper { display: flex; gap: 8px; align-items: flex-end; background: var(--el-fill-color); border: 1px solid var(--el-border-color); border-radius: 12px; padding: 6px 8px 6px 14px; }
.input-wrapper:focus-within { border-color: var(--el-color-primary); }
.input-field { flex: 1; border: none; outline: none; background: transparent; color: var(--el-text-color-primary); font-family: inherit; font-size: 14px; resize: none; padding: 4px 0; line-height: 1.5; }
.input-field::placeholder { color: var(--el-text-color-placeholder); }

/* ---- Right Panel ---- */
.workspace-panel {
  width: 280px;
  border-left: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
  padding: 12px;
}
.panel-section { margin-bottom: 16px; }
.panel-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.panel-header h4 { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); margin: 0; }
.badge { background: var(--el-fill-color); color: var(--el-text-color-secondary); font-size: 11px; padding: 1px 7px; border-radius: 10px; }
.panel-empty { text-align: center; padding: 20px 12px; font-size: 12px; color: var(--el-text-color-placeholder); }

.source-list { display: flex; flex-direction: column; gap: 8px; }
.source-card { background: var(--el-fill-color); border: 1px solid var(--el-border-color-lighter); border-radius: 6px; padding: 8px; }
.source-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.source-num { font-size: 11px; color: var(--el-text-color-placeholder); font-weight: 600; }
.source-file { flex: 1; font-size: 12px; color: var(--el-color-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-score { font-size: 12px; font-weight: 600; }
.source-score.high { color: #22c55e; }
.source-score.mid { color: #f59e0b; }
.source-score.low { color: var(--el-text-color-placeholder); }
.source-excerpt { font-size: 11px; color: var(--el-text-color-secondary); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

.trace-list { display: flex; flex-direction: column; gap: 6px; }
.trace-step { display: flex; align-items: flex-start; gap: 8px; }
.trace-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; background: var(--el-text-color-placeholder); }
.trace-dot.running { background: var(--el-color-primary); }
.trace-dot.completed { background: #22c55e; }
.trace-dot.error { background: var(--el-color-danger); }
.trace-info { flex: 1; }
.trace-node { font-size: 12px; font-weight: 500; color: var(--el-text-color-primary); }
.trace-status { font-size: 11px; }
.trace-status.running { color: var(--el-color-primary); }
.trace-status.completed { color: #22c55e; }
.trace-status.error { color: var(--el-color-danger); }
</style>