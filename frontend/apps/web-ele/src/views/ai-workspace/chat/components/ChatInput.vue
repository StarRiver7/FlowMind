<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{ disabled?: boolean }>();
const emit = defineEmits<{ send: [content: string] }>();

const input = ref('');
const textareaRef = ref<HTMLTextAreaElement>();

const canSend = computed(() => input.value.trim().length > 0 && !props.disabled);

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

function send() {
  if (!canSend.value) return;
  emit('send', input.value.trim());
  input.value = '';
  // Reset height
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
  }
}

function autoResize() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
}
</script>

<template>
  <div class="relative">
    <textarea
      ref="textareaRef"
      v-model="input"
      :disabled="disabled"
      class="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 pr-14
             text-sm text-gray-700 placeholder-gray-400 outline-none transition-all duration-150
             focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100
             disabled:opacity-50 disabled:cursor-not-allowed"
      :placeholder="disabled ? '小SU正在回复中...' : '老师，今天想让我帮您做什么？'"
      rows="1"
      @keydown="handleKeydown"
      @input="autoResize"
    />

    <!-- Send button -->
    <button
      class="absolute right-2 bottom-2 flex h-8 w-8 items-center justify-center rounded-lg
             transition-all duration-150"
      :class="canSend
        ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm'
        : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
      :disabled="!canSend"
      @click="send"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="19" x2="12" y2="5" />
        <polyline points="5 12 12 5 19 12" />
      </svg>
    </button>

    <!-- Hint -->
    <div class="mt-1.5 text-[11px] text-gray-400 text-center">
      Enter 发送 · Shift+Enter 换行
    </div>
  </div>
</template>
