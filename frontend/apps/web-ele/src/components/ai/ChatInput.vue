<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';

const props = defineProps<{
  disabled?: boolean;
  ragEnabled?: boolean;
}>();

const emit = defineEmits<{
  send: [content: string];
  'update:ragEnabled': [value: boolean];
  upload: [files: FileList];
}>();

const input = ref('');
const textareaRef = ref<HTMLTextAreaElement>();
const fileInputRef = ref<HTMLInputElement>();
const showToolbar = ref(false);
const ragOn = ref(props.ragEnabled ?? true);

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

function toggleRag() {
  ragOn.value = !ragOn.value;
  emit('update:ragEnabled', ragOn.value);
}

function triggerUpload() {
  fileInputRef.value?.click();
}

function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (files && files.length > 0) {
    emit('upload', files);
  }
  // Reset input
  if (fileInputRef.value) fileInputRef.value.value = '';
}

defineExpose({ focus: () => textareaRef.value?.focus() });
</script>

<template>
  <div class="relative w-full">
    <!-- Toolbar row -->
    <div class="flex items-center gap-1 mb-2 px-1">
      <button
        class="flex items-center justify-center w-8 h-8 rounded-lg transition-colors
               hover:bg-gray-100 text-gray-400 hover:text-gray-600"
        title="上传文件"
        @click="triggerUpload"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </button>
      <button
        class="flex items-center gap-1.5 px-2.5 h-8 rounded-lg text-xs font-medium transition-all
               border"
        :class="ragOn
          ? 'bg-blue-50 border-blue-200 text-blue-600'
          : 'bg-white border-gray-200 text-gray-400 hover:text-gray-600'"
        title="企业知识库检索增强 (RAG)"
        @click="toggleRag"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        RAG
      </button>
      <span v-if="disabled" class="ml-auto text-xs text-blue-500 flex items-center gap-1 animate-isu-pulse-dot">
        <span class="w-1.5 h-1.5 bg-blue-500 rounded-full" />
        处理中...
      </span>
    </div>

    <input
      ref="fileInputRef"
      type="file"
      class="hidden"
      multiple
      accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx"
      @change="onFileChange"
    />

    <!-- Input area -->
    <div class="relative rounded-2xl border bg-white transition-all duration-200"
         :class="[
           disabled ? 'border-gray-200 opacity-60' : 'border-gray-200 focus-within:border-blue-300 focus-within:shadow-[0_0_0_3px_rgba(59,130,246,0.08)]',
         ]">
      <textarea
        ref="textareaRef"
        v-model="input"
        :disabled="disabled"
        class="w-full resize-none bg-transparent px-4 py-3.5 pr-12 text-[15px] text-gray-800
               placeholder-gray-400 outline-none leading-relaxed
               disabled:cursor-not-allowed"
        :placeholder="disabled ? '正在处理中...' : '老师，今天想让我帮您做什么？'"
        rows="1"
        @keydown="handleKeydown"
        @input="autoResize"
        @focus="showToolbar = true"
        @blur="showToolbar = false"
      />

      <!-- Send button -->
      <button
        class="absolute right-3 bottom-3 flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-200"
        :class="canSend
          ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm'
          : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
        :disabled="!canSend"
        @click="send"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
        </svg>
      </button>
    </div>

    <!-- Hint -->
    <div class="mt-2 text-[11px] text-gray-400 text-center select-none">
      Enter 发送 · Shift + Enter 换行
    </div>
  </div>
</template>
