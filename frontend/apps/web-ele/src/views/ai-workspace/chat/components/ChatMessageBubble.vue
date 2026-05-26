<script setup lang="ts">
import type { ChatMessageUI } from '#/store/chat';

defineProps<{ message: ChatMessageUI }>();
</script>

<template>
  <div class="msg-bubble" :class="message.role">
    <div class="msg-avatar">
      <el-avatar :size="32" v-if="message.role === 'assistant'">
        <el-icon :size="18"><Cpu /></el-icon>
      </el-avatar>
      <el-avatar :size="32" v-else>
        <el-icon :size="18"><User /></el-icon>
      </el-avatar>
    </div>
    <div class="msg-content">
      <div class="msg-text" v-html="message.content || (message.streaming ? '思考中...' : '')">
      </div>
      <div v-if="message.sources?.length" class="msg-sources">
        <span class="source-label">引用来源:</span>
        <el-tag
          v-for="(s, i) in message.sources.slice(0, 3)"
          :key="i"
          size="small"
          type="info"
          effect="plain"
        >
          {{ s.file }} ({{ (s.score * 100).toFixed(0) }}%)
        </el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.msg-bubble {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  max-width: 85%;
}

.msg-bubble.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.msg-content {
  flex: 1;
  min-width: 0;
}

.msg-text {
  line-height: 1.7;
  font-size: 14px;
  padding: 12px 16px;
  border-radius: 12px;
  word-break: break-word;
}

.user .msg-text {
  background: var(--el-color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant .msg-text {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  border-bottom-left-radius: 4px;
}

.msg-sources {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
}

.source-label {
  color: var(--el-text-color-secondary);
}
</style>
