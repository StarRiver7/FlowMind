<!-- ============================================================ -->
<!-- ChatInput — message composer with send/stop                   -->
<!-- ============================================================ -->
<script setup lang="ts">
import { ref, nextTick } from 'vue'

defineProps<{ streaming: boolean }>()
const emit = defineEmits<{ send: [message: string]; stop: [] }>()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  emit('send', text)
  inputText.value = ''
  nextTick(() => textareaRef.value?.focus())
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function autoResize() {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }
}
</script>

<template>
  <div class="input-container">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="input-field"
        placeholder="输入消息...（Enter 发送，Shift+Enter 换行）"
        rows="1"
        :disabled="streaming"
        @keydown="handleKeydown"
        @input="autoResize"
      ></textarea>

      <div class="input-actions">
        <button
          v-if="streaming"
          class="stop-btn"
          @click="emit('stop')"
        >
          <span class="stop-icon">&#9632;</span>
          停止
        </button>
        <button
          v-else
          class="send-btn"
          :disabled="!inputText.trim()"
          @click="handleSend"
        >
          <span class="send-icon">&#10148;</span>
        </button>
      </div>
    </div>

    <div class="input-footer">
      <span class="footer-hint">FlowMind v2.0 — 知识库 + 工具已启用</span>
    </div>
  </div>
</template>

<style scoped>
.input-container {
  padding: 12px 20px 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 6px 8px 6px 14px;
  transition: border-color 0.15s;
}
.input-wrapper:focus-within {
  border-color: var(--accent-blue);
}

.input-field {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  padding: 4px 0;
  max-height: 160px;
}
.input-field::placeholder {
  color: var(--text-muted);
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--accent-blue);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.send-btn:hover:not(:disabled) {
  background: #4090e0;
  transform: scale(1.05);
}
.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.send-icon {
  font-size: 16px;
}

.stop-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--danger);
  background: rgba(248, 81, 73, 0.1);
  color: var(--danger);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.stop-btn:hover {
  background: rgba(248, 81, 73, 0.2);
}
.stop-icon {
  font-size: 10px;
}

.input-footer {
  text-align: center;
  margin-top: 6px;
}
.footer-hint {
  font-size: 11px;
  color: var(--text-muted);
}
</style>