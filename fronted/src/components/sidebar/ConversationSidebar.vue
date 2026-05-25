<!-- ============================================================ -->
<!-- ConversationSidebar — left sidebar with session list          -->
<!-- ============================================================ -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'
import ConversationItem from './ConversationItem.vue'

const convStore = useConversationStore()
const chatStore = useChatStore()
const userId = ref('demo-user')

onMounted(async () => {
  await convStore.fetchList(userId.value)
})

async function handleNew() {
  await convStore.newAndSwitch(userId.value, chatStore)
}

async function handleSelect(id: string) {
  await convStore.switchTo(id, chatStore)
}
</script>

<template>
  <div class="sidebar-container">
    <!-- Header -->
    <div class="sidebar-header">
      <div class="sidebar-brand">
        <span class="brand-icon">&#x1F9E0;</span>
        <span class="brand-text">FlowMind AI</span>
      </div>
      <button class="new-chat-btn" @click="handleNew">
        <span class="btn-icon">+</span>
        New Chat
      </button>
    </div>

    <!-- Search -->
    <div class="sidebar-search">
      <input
        type="text"
        class="search-input"
        placeholder="Search conversations..."
      />
    </div>

    <!-- Conversation List -->
    <div class="sidebar-list">
      <ConversationItem
        v-for="conv in convStore.sortedConversations"
        :key="conv.conversation_id"
        :conversation="conv"
        :active="conv.conversation_id === convStore.currentId"
        @select="handleSelect(conv.conversation_id)"
      />
      <div v-if="convStore.conversations.length === 0" class="empty-list">
        <p>No conversations yet</p>
        <p class="hint">Start a new chat to begin</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.brand-icon {
  font-size: 20px;
}
.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent-blue);
  letter-spacing: -0.3px;
}
.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: var(--accent-blue);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.new-chat-btn:hover {
  background: #4090e0;
}
.btn-icon {
  font-size: 18px;
  font-weight: 300;
}

.sidebar-search {
  padding: 10px 12px;
}
.search-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}
.search-input:focus {
  border-color: var(--accent-blue);
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}
.empty-list {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 13px;
}
.empty-list .hint {
  margin-top: 4px;
  font-size: 12px;
}
</style>