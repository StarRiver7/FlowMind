<!-- ============================================================ -->
<!-- ChatPanel — center chat area with message list + input        -->
<!-- ============================================================ -->
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useConversationStore } from '@/stores/conversation'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'

const chatStore = useChatStore()
const convStore = useConversationStore()
const msgContainer = ref<HTMLElement | null>(null)
const userId = 'demo-user'

// Auto-scroll
watch(
  () => chatStore.messages.length,
  () => scrollToBottom(),
)
watch(
  () => chatStore.lastMessage?.content,
  () => scrollToBottom(),
)

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

async function handleSend(message: string) {
  if (!convStore.currentId) {
    await convStore.newAndSwitch(userId, chatStore)
  }
  if (!convStore.currentId) return

  await chatStore.sendMessage({
    user_id: userId,
    conversation_id: convStore.currentId,
    message,
    stream: true,
    use_rag: true,
    use_tools: true,
  })

  convStore.fetchList(userId)
}

function handleStop() {
  chatStore.stopGeneration()
}
</script>

<template>
  <div class="chat-panel">
    <div ref="msgContainer" class="msg-container">
      <!-- Welcome -->
      <div v-if="!chatStore.hasMessages" class="welcome">
        <div class="welcome-icon">&#x1F9E0;</div>
        <h2>FlowMind AI Workspace</h2>
        <p>Enterprise AI assistant with RAG-powered knowledge retrieval.</p>
        <div class="welcome-hints">
          <div class="hint-item" @click="handleSend('What is the data retention policy?')">
            <span class="hint-icon">&#x1F4CB;</span>
            <span>Policy lookup</span>
          </div>
          <div class="hint-item" @click="handleSend('Explain the API authentication flow')">
            <span class="hint-icon">&#x1F510;</span>
            <span>Auth flow</span>
          </div>
          <div class="hint-item" @click="handleSend('Summarize the deployment architecture')">
            <span class="hint-icon">&#x2601;</span>
            <span>Architecture</span>
          </div>
        </div>
      </div>

      <ChatMessage
        v-for="msg in chatStore.messages"
        :key="msg.id"
        :message="msg"
      />

      <div v-if="chatStore.error" class="error-banner">
        <span class="error-text">{{ chatStore.error }}</span>
      </div>
    </div>

    <ChatInput
      :streaming="chatStore.streaming"
      @send="handleSend"
      @stop="handleStop"
    />
  </div>
</template>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; position: relative; }
.msg-container { flex: 1; overflow-y: auto; padding: 20px 24px; }
.welcome { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; padding: 40px; }
.welcome-icon { font-size: 48px; margin-bottom: 16px; }
.welcome h2 { font-size: 22px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.welcome p { color: var(--text-secondary); font-size: 14px; max-width: 400px; margin-bottom: 24px; }
.welcome-hints { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.hint-item { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 20px; cursor: pointer; font-size: 13px; color: var(--text-secondary); transition: all 0.15s; }
.hint-item:hover { background: var(--bg-hover); color: var(--text-primary); border-color: var(--accent-blue); }
.hint-icon { font-size: 14px; }
.error-banner { display: flex; align-items: center; padding: 10px 14px; margin: 8px 0; background: rgba(248,81,73,0.1); border: 1px solid rgba(248,81,73,0.3); border-radius: var(--radius-md); }
.error-text { font-size: 13px; color: var(--danger); }
</style>