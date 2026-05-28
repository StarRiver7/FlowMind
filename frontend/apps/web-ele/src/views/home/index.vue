<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNow } from '@vueuse/core';
import {
  Search,
  Upload,
  MessageSquare,
  Database,
  BarChart3,
  Clock,
  FileText,
  Sparkles,
} from 'lucide-vue-next';

const router = useRouter();
const now = useNow();

const greeting = computed(() => {
  const hour = now.value.getHours();
  if (hour < 6) return '夜深了';
  if (hour < 12) return '早上好';
  if (hour < 14) return '中午好';
  if (hour < 18) return '下午好';
  return '晚上好';
});

const currentTime = computed(() => {
  const date = now.value;
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const weekday = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][date.getDay()];
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return {
    date: `${year}年${month}月${day}日 ${weekday}`,
    time: `${hours}:${minutes}:${seconds}`,
  };
});

const quickActions = [
  { icon: Search, label: '查询企业制度', route: '/ai-workspace/chat', color: 'from-blue-500 to-indigo-500' },
  { icon: Database, label: '查询员工数据', route: '/ai-workspace/chat', color: 'from-emerald-500 to-teal-500' },
  { icon: Upload, label: '上传知识库', route: '/ai-workspace/knowledge', color: 'from-purple-500 to-pink-500' },
  { icon: MessageSquare, label: 'AI问答', route: '/ai-workspace/chat', color: 'from-orange-500 to-amber-500' },
  { icon: BarChart3, label: 'SQL分析', route: '/ai-workspace/chat', color: 'from-cyan-500 to-blue-500' },
];

const recentStats = ref([
  { label: '今日新增文档', value: '12', icon: FileText },
  { label: 'Agent运行', value: '86', icon: Sparkles },
  { label: 'Token使用', value: '12.5K', icon: Clock },
]);

const searchQuery = ref('');

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push('/ai-workspace/chat');
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
    <div class="max-w-6xl mx-auto px-6 py-16">
      <div class="text-center mb-12">
        <div class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-4 py-2 rounded-full text-sm font-medium mb-6">
          <Sparkles class="w-4 h-4" />
          <span>企业AI助手已就绪</span>
        </div>
        <h1 class="text-5xl font-bold text-gray-900 mb-4">
          {{ greeting }}，老师
        </h1>
        <div class="flex items-center justify-center gap-2 text-gray-500">
          <Clock class="w-5 h-5" />
          <span class="text-lg">{{ currentTime.date }}</span>
          <span class="font-mono text-xl font-semibold text-blue-600">{{ currentTime.time }}</span>
        </div>
      </div>

      <div class="max-w-3xl mx-auto mb-12">
        <div class="relative">
          <div class="absolute inset-0 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-2xl blur-lg opacity-20"></div>
          <div class="relative bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
            <div class="flex items-center px-6 py-4 border-b border-gray-100">
              <div class="flex gap-2">
                <span class="w-3 h-3 rounded-full bg-red-400"></span>
                <span class="w-3 h-3 rounded-full bg-yellow-400"></span>
                <span class="w-3 h-3 rounded-full bg-green-400"></span>
              </div>
              <span class="ml-4 text-sm text-gray-400">internSU AI</span>
            </div>
            <div class="p-6">
              <textarea
                v-model="searchQuery"
                @keydown.enter.exact.prevent="handleSearch"
                placeholder="老师，今天想让我帮您做什么？"
                class="w-full h-20 bg-transparent resize-none outline-none text-lg text-gray-700 placeholder-gray-400"
              ></textarea>
            </div>
            <div class="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-100">
              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                  在线
                </span>
                <span>|</span>
                <span>Enter 发送</span>
                <span>Shift+Enter 换行</span>
              </div>
              <button
                @click="handleSearch"
                class="px-6 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
              >
                <Search class="w-4 h-4" />
                开始对话
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-12">
        <button
          v-for="action in quickActions"
          :key="action.label"
          @click="router.push(action.route)"
          class="group relative bg-white rounded-xl p-6 border border-gray-100 hover:border-transparent hover:shadow-xl transition-all duration-300 overflow-hidden"
        >
          <div class="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300" :class="action.color"></div>
          <div class="relative">
            <div class="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-white/20 transition-colors">
              <component :is="action.icon" class="w-6 h-6 text-gray-600 group-hover:text-white transition-colors" />
            </div>
            <span class="text-gray-700 font-medium group-hover:text-white transition-colors">{{ action.label }}</span>
          </div>
        </button>
      </div>

      <div class="grid grid-cols-3 gap-6">
        <div
          v-for="stat in recentStats"
          :key="stat.label"
          class="bg-white rounded-xl p-6 border border-gray-100 hover:shadow-lg transition-shadow"
        >
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-center justify-center">
              <component :is="stat.icon" class="w-5 h-5 text-blue-600" />
            </div>
            <span class="text-gray-500 text-sm">{{ stat.label }}</span>
          </div>
          <div class="text-2xl font-bold text-gray-900">{{ stat.value }}</div>
        </div>
      </div>
    </div>
  </div>
</template>