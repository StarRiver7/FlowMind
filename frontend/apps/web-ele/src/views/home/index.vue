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
  { icon: Search, label: '查询企业制度', route: '/ai-workspace/chat', color: 'from-sky-200 to-indigo-200' },
  { icon: Database, label: '查询员工数据', route: '/ai-workspace/chat', color: 'from-teal-200 to-emerald-200' },
  { icon: Upload, label: '上传知识库', route: '/ai-workspace/knowledge', color: 'from-violet-200 to-pink-200' },
  { icon: MessageSquare, label: 'AI问答', route: '/ai-workspace/chat', color: 'from-amber-200 to-orange-200' },
  { icon: BarChart3, label: 'SQL分析', route: '/ai-workspace/chat', color: 'from-cyan-200 to-blue-200' },
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
  <div class="relative h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-white to-slate-100">
    <div class="login-background absolute top-0 left-0 size-full"></div>
    <div class="absolute inset-0 overflow-hidden">
      <div class="color-orb color-orb-green"></div>
      <div class="color-orb color-orb-blue"></div>
    </div>
    <div class="relative max-w-6xl mx-auto px-6 py-12">
      <div class="text-center mb-12">
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
        <div
          class="mx-auto flex items-center gap-3 glass-card"
          style="max-width: 640px; width: 100%; height: 60px; padding: 16px 28px; -webkit-border-radius: 30px; -moz-border-radius: 30px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.5); background: rgba(255, 255, 255, 0.35); -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px); box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);"
        >
          <Search class="w-5 h-5 text-gray-400 shrink-0" />
          <input
            v-model="searchQuery"
            @keydown.enter.exact.prevent="handleSearch"
            type="text"
            placeholder="老师，今天想让我帮您做什么？"
            class="flex-1 h-full bg-transparent outline-none text-base text-gray-700 placeholder-gray-400"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-12">
        <button
          v-for="action in quickActions"
          :key="action.label"
          @click="router.push(action.route)"
          class="group glass-card relative bg-white/30 rounded-xl p-6 border border-white/40 hover:border-white/60 hover:shadow-xl transition-all duration-300 overflow-hidden"
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
          class="glass-card bg-white/30 rounded-xl p-6 border border-white/40 hover:shadow-xl transition-all duration-300"
        >
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-center justify-center">
              <component :is="stat.icon" class="w-5 h-5 text-blue-600" />
            </div>
            <span class="text-gray-600 text-sm">{{ stat.label }}</span>
          </div>
          <div class="text-2xl font-bold text-gray-900">{{ stat.value }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-background {
  background: rgba(14, 116, 144, 0.05);
  filter: blur(80px);
}

.color-orb {
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}

.color-orb-green {
  background: radial-gradient(circle, rgba(34, 197, 94, 0.6) 0%, rgba(34, 197, 94, 0.2) 70%, transparent 100%);
  animation: orb-float-green 12s ease-in-out infinite;
}

.color-orb-blue {
  background: radial-gradient(circle, rgba(59, 130, 246, 0.6) 0%, rgba(59, 130, 246, 0.2) 70%, transparent 100%);
  animation: orb-float-blue 15s ease-in-out infinite;
}

@keyframes orb-float-green {
  0% {
    left: 25%;
    top: 35%;
    opacity: 0.5;
  }
  15% {
    left: 40%;
    top: 25%;
    opacity: 0.7;
  }
  30% {
    left: 55%;
    top: 35%;
    opacity: 0.5;
  }
  45% {
    left: 60%;
    top: 50%;
    opacity: 0.6;
  }
  60% {
    left: 45%;
    top: 55%;
    opacity: 0.7;
  }
  75% {
    left: 30%;
    top: 50%;
    opacity: 0.5;
  }
  90% {
    left: 20%;
    top: 40%;
    opacity: 0.6;
  }
  100% {
    left: 25%;
    top: 35%;
    opacity: 0.5;
  }
}

@keyframes orb-float-blue {
  0% {
    right: 25%;
    top: 40%;
    opacity: 0.5;
  }
  20% {
    right: 40%;
    top: 50%;
    opacity: 0.6;
  }
  40% {
    right: 50%;
    top: 35%;
    opacity: 0.7;
  }
  60% {
    right: 35%;
    top: 25%;
    opacity: 0.5;
  }
  80% {
    right: 20%;
    top: 45%;
    opacity: 0.6;
  }
  100% {
    right: 25%;
    top: 40%;
    opacity: 0.5;
  }
}

.glass-card {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.dark {
  .login-background {
    background: rgba(6, 78, 59, 0.1);
  }

  .color-orb-green {
    background: radial-gradient(circle, rgba(22, 163, 74, 0.5) 0%, rgba(22, 163, 74, 0.15) 70%, transparent 100%);
  }

  .color-orb-blue {
    background: radial-gradient(circle, rgba(37, 99, 235, 0.5) 0%, rgba(37, 99, 235, 0.15) 70%, transparent 100%);
  }

  .glass-card {
    background: rgba(30, 41, 59, 0.4);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
}
</style>