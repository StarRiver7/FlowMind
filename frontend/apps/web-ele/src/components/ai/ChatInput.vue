<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { Send, Upload, Database, DatabaseOff, Paperclip, X } from 'lucide-vue-next';

const props = defineProps<{
  disabled?: boolean;
  ragEnabled?: boolean;
}>();

const emit = defineEmits<{
  send: [content: string, files: File[]];
  toggleRag: [];
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const message = ref('');
const files = ref<File[]>([]);
const isExpanded = ref(false);

const maxHeight = 200;

function handleInput() {
  if (!textareaRef.value) return;
  
  const scrollHeight = textareaRef.value.scrollHeight;
  if (scrollHeight > maxHeight) {
    textareaRef.value.style.height = `${maxHeight}px`;
    textareaRef.value.style.overflowY = 'auto';
    isExpanded.value = true;
  } else {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    textareaRef.value.style.overflowY = 'hidden';
    isExpanded.value = scrollHeight > 40;
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function sendMessage() {
  if (!message.value.trim() && files.value.length === 0) return;
  emit('send', message.value.trim(), [...files.value]);
  message.value = '';
  files.value = [];
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto';
    }
  });
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  const selectedFiles = target.files;
  if (selectedFiles) {
    files.value = [...files.value, ...Array.from(selectedFiles)];
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1);
}

function clearAllFiles() {
  files.value = [];
}

watch(() => message.value, handleInput);
</script>

<template>
  <div class="bg-white border-t border-gray-100 p-4">
    <div v-if="files.length > 0" class="mb-3 flex flex-wrap gap-2">
      <div 
        v-for="(file, index) in files" 
        :key="index"
        class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg"
      >
        <Paperclip class="w-4 h-4 text-gray-500" />
        <span class="text-sm text-gray-700 max-w-[200px] truncate">{{ file.name }}</span>
        <button 
          @click="removeFile(index)"
          class="w-5 h-5 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center"
        >
          <X class="w-3 h-3 text-gray-600" />
        </button>
      </div>
      <button 
        v-if="files.length > 1"
        @click="clearAllFiles"
        class="text-sm text-blue-500 hover:text-blue-600"
      >
        清除全部
      </button>
    </div>

    <div class="flex items-end gap-3">
      <button 
        @click="emit('toggleRag')"
        class="w-10 h-10 rounded-lg flex items-center justify-center transition-all"
        :class="[
          props.ragEnabled 
            ? 'bg-blue-100 text-blue-600' 
            : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
        ]"
      >
        <Database v-if="props.ragEnabled" class="w-5 h-5" />
        <DatabaseOff v-else class="w-5 h-5" />
      </button>

      <div class="flex-1 relative">
        <textarea
          ref="textareaRef"
          v-model="message"
          placeholder="老师，今天想让我帮您做什么？"
          rows="1"
          :disabled="props.disabled"
          @keydown="handleKeyDown"
          @input="handleInput"
          class="w-full px-4 py-3 bg-gray-50 rounded-xl border-none resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-gray-900 placeholder-gray-400 transition-all"
          style="min-height: 48px;"
        ></textarea>
      </div>

      <label class="w-10 h-10 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center cursor-pointer transition-colors">
        <Upload class="w-5 h-5 text-gray-500" />
        <input 
          type="file" 
          multiple 
          accept=".pdf,.doc,.docx,.txt,.md"
          class="hidden" 
          @change="handleFileSelect"
        />
      </label>

      <button 
        @click="sendMessage"
        :disabled="!message.trim() && files.length === 0 || props.disabled"
        class="w-10 h-10 rounded-lg flex items-center justify-center transition-all"
        :class="[
          (message.trim() || files.length > 0) && !props.disabled
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        ]"
      >
        <Send class="w-5 h-5" />
      </button>
    </div>

    <div class="flex items-center justify-between mt-2 text-xs text-gray-400">
      <span>{{ props.ragEnabled ? 'RAG已启用' : 'RAG已关闭' }}</span>
      <span>按 Enter 发送，Shift+Enter 换行</span>
    </div>
  </div>
</template>
