<script setup lang="ts">
import { ref, computed } from 'vue';

export interface SessionItem {
  id: string;
  title: string;
  updatedAt: string;
  group?: string;
}

const props = defineProps<{
  sessions: SessionItem[];
  currentId: string | null;
  loading?: boolean;
}>();

const emit = defineEmits<{
  select: [session: SessionItem];
  new: [];
  delete: [id: string];
}>();

const searchQuery = ref('');

const todaySessions = computed(() => {
  const today = new Date().toISOString().slice(0, 10);
  return filteredSessions.value.filter(s => s.updatedAt?.startsWith(today));
});

const olderSessions = computed(() => {
  const today = new Date().toISOString().slice(0, 10);
  return filteredSessions.value.filter(s => !s.updatedAt?.startsWith(today));
});

const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) return props.sessions;
  const q = searchQuery.value.toLowerCase();
  return props.sessions.filter(s => s.title.toLowerCase().includes(q));
});
</script>

<template>
  <div class="flex flex-col h-full bg-[#f9fafb] border-r border-[#e5e7eb]">
    <!-- Header -->
    <div class="shrink-0 p-4 pb-3">
      <button
        class="w-full flex items-center gap-2.5 rounded-xl border border-gray-200 bg-white px-4 py-2.5
               text-sm text-gray-700 hover:border-blue-200 hover:shadow-sm
               transition-all duration-150 font-medium"
        @click="emit('new')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>新建对话</span>
      </button>
    </div>

    <!-- Search -->
    <div class="shrink-0 px-4 pb-2">
      <div class="relative">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="w-full rounded-lg border border-gray-200 bg-white py-1.5 pl-8 pr-3
                 text-xs text-gray-700 placeholder-gray-400 outline-none
                 focus:border-blue-200 focus:ring-1 focus:ring-blue-100 transition-all"
          placeholder="搜索会话..."
        />
      </div>
    </div>

    <!-- Session list -->
    <div class="flex-1 overflow-y-auto isu-scrollbar px-3 pb-4">
      <!-- Today -->
      <div v-if="todaySessions.length > 0" class="mb-4">
        <div class="px-2 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">今天</div>
        <div
          v-for="session in todaySessions"
          :key="session.id"
          class="group mb-0.5 cursor-pointer rounded-lg px-3 py-2.5 text-sm transition-all duration-100"
          :class="currentId === session.id
            ? 'bg-white border border-gray-200 shadow-sm text-gray-800'
            : 'text-gray-600 hover:bg-white/60 hover:text-gray-800'"
          @click="emit('select', session)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="truncate text-[13px] leading-snug">{{ session.title || '新对话' }}</div>
            <button
              class="shrink-0 opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all mt-0.5"
              @click.stop="emit('delete', session.id)"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="mt-0.5 text-[10px] text-gray-400">
            {{ session.updatedAt?.slice(11, 16) || '' }}
          </div>
        </div>
      </div>

      <!-- Older -->
      <div v-if="olderSessions.length > 0">
        <div class="px-2 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">更早</div>
        <div
          v-for="session in olderSessions"
          :key="session.id"
          class="group mb-0.5 cursor-pointer rounded-lg px-3 py-2.5 text-sm transition-all duration-100"
          :class="currentId === session.id
            ? 'bg-white border border-gray-200 shadow-sm text-gray-800'
            : 'text-gray-600 hover:bg-white/60 hover:text-gray-800'"
          @click="emit('select', session)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="truncate text-[13px] leading-snug">{{ session.title || '新对话' }}</div>
            <button
              class="shrink-0 opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all mt-0.5"
              @click.stop="emit('delete', session.id)"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="mt-0.5 text-[10px] text-gray-400">
            {{ session.updatedAt?.slice(0, 10) || '' }}
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div
        v-if="filteredSessions.length === 0"
        class="flex flex-col items-center justify-center py-12 text-center"
      >
        <svg class="mb-3 text-gray-300" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <div class="text-xs text-gray-400">
          {{ searchQuery ? '没有匹配的会话' : '还没有会话记录' }}
        </div>
      </div>
    </div>
  </div>
</template>
