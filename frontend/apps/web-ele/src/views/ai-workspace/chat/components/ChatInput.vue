<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{ streaming: boolean }>();
const emit = defineEmits<{ send: [text: string]; stop: [] }>();

const inputText = ref('');

function handleSend() {
  if (!inputText.value.trim() || props.streaming) return;
  emit('send', inputText.value);
  inputText.value = '';
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}
</script>

<template>
  <div class="chat-input-wrapper">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
      :disabled="streaming"
      @keydown="handleKeydown"
      resize="none"
    />
    <div class="input-actions">
      <span class="input-hint">{{ streaming ? 'AI 正在生成...' : 'Enter 发送' }}</span>
      <el-button
        v-if="streaming"
        type="danger"
        size="small"
        @click="emit('stop')"
      >
        停止生成
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
</template>

<style scoped>
.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.input-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
</style>
