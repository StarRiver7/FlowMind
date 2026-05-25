<!-- ============================================================ -->
<!-- ChatMessage — single message bubble                          -->
<!-- ============================================================ -->
<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage as ChatMessageType } from '@/api/types'
import MessageContent from './MessageContent.vue'

const props = defineProps<{ message: ChatMessageType }>()


const isUser = computed(() => props.message.role === 'user')
const hasSources = computed(() => (props.message.sources?.length || 0) > 0)
</script>

<template>
  <div :class="['msg-wrapper', { user: isUser }]">
    <!-- Avatar -->
    <div :class="['msg-avatar', { user: isUser }]">
      {{ isUser ? 'U' : 'AI' }}
    </div>

    <!-- Bubble -->
    <div class="msg-body">
      <div :class="['msg-bubble', { user: isUser, thinking: message.thinking }]">
        <!-- Thinking state -->
        <div v-if="message.thinking" class="thinking-text">
          <span class="thinking-dots">{{ message.content || 'Thinking...' }}</span>
        </div>

        <!-- Content -->
        <div v-else class="msg-content">
          <MessageContent
            :content="message.content"
            :is-user="isUser"
          />
          <!-- Streaming cursor -->
          <span v-if="message.streaming" class="cursor-blink"></span>
        </div>
      </div>

      <!-- Sources -->
      <div v-if="hasSources && !message.streaming" class="msg-sources">
        <div class="sources-label">Sources</div>
        <div
          v-for="(src, i) in message.sources"
          :key="i"
          class="source-chip"
        >
          <span class="source-file">{{ src.file }}</span>
          <span class="source-score">{{ (src.score * 100).toFixed(0) }}%</span>
        </div>
      </div>

      <!-- Time -->
      <div class="msg-time">{{ new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</div>
    </div>
  </div>
</template>

<style scoped>
.msg-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 85%;
}
.msg-wrapper.user {
  flex-direction: row-reverse;
  margin-left: auto;
  max-width: 75%;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}
.msg-avatar:not(.user) {
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
  color: #fff;
}
.msg-avatar.user {
  background: var(--accent-blue);
  color: #fff;
}

.msg-body {
  min-width: 0;
}

.msg-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.65;
}
.msg-bubble:not(.user) {
  background: var(--bg-tertiary);
  border-bottom-left-radius: 4px;
}
.msg-bubble.user {
  background: var(--accent-blue);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg-bubble.thinking {
  background: transparent;
  padding: 4px 14px;
}

.thinking-text {
  color: var(--text-muted);
  font-style: italic;
  font-size: 13px;
}

.msg-content {
  word-break: break-word;
}

/* Sources */
.msg-sources {
  margin-top: 6px;
  padding: 8px 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}
.sources-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}
.source-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  margin: 2px 4px 2px 0;
  font-size: 12px;
}
.source-file {
  color: var(--accent-blue);
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.source-score {
  color: var(--text-muted);
  font-size: 11px;
}

.msg-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  padding: 0 4px;
}
</style>