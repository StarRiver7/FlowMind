<!-- ============================================================ -->
<!-- ConversationItem — single conversation row in sidebar         -->
<!-- ============================================================ -->
<script setup lang="ts">
import type { Conversation } from '@/api/types'

defineProps<{
  conversation: Conversation
  active: boolean
}>()

const emit = defineEmits<{ select: [] }>()

function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 86400000) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  if (diff < 604800000) {
    return d.toLocaleDateString([], { weekday: 'short' })
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div :class="['conv-item', { active }]" @click="emit('select')">
    <div class="conv-icon">
      <span v-if="active">&#9679;</span>
      <span v-else>&#9675;</span>
    </div>
    <div class="conv-info">
      <div class="conv-title">{{ conversation.title || 'New Conversation' }}</div>
      <div class="conv-meta">
        <span>{{ conversation.message_count || 0 }} msgs</span>
        <span class="conv-time">{{ formatTime(conversation.updated_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s;
  margin: 1px 0;
}
.conv-item:hover {
  background: var(--bg-tertiary);
}
.conv-item.active {
  background: rgba(88, 166, 255, 0.08);
}

.conv-icon {
  flex-shrink: 0;
  font-size: 10px;
  color: var(--text-muted);
}
.conv-item.active .conv-icon {
  color: var(--accent-blue);
}

.conv-info {
  flex: 1;
  min-width: 0;
}
.conv-title {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item.active .conv-title {
  color: var(--accent-blue);
}
.conv-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}
.conv-time {
  margin-left: auto;
}
</style>