<script setup lang="ts">
import { ref, computed } from 'vue';
import { Search, Plus, Trash2, MessageSquare, Clock } from 'lucide-vue-next';

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  unread?: number;
}

const props = defineProps<{
  currentConversationId?: string;
}>();

const emit = defineEmits<{
  select: [id: string];
  create: [];
  delete: [id: string];
}>();

const searchQuery = ref('');

const conversations = ref<Conversation[]>([
  { id: 'conv-1', title: '企业制度查询', lastMessage: '老师，我来帮您查询相关制度...', timestamp: new Date(Date.now() - 3600000), unread: 2 },
  { id: 'conv-2', title: '员工数据统计', lastMessage: '好的老师，我来帮您分析员工数据...', timestamp: new Date(Date.now() - 7200000) },
  { id: 'conv-3', title: '项目进度汇报', lastMessage: '项目A当前进度已达85%...', timestamp: new Date(Date.now() - 86400000) },
  { id: 'conv-4', title: '知识库上传', lastMessage: '文档已成功上传并处理完成', timestamp: new Date(Date.now() - 86400000 * 2) },
  { id: 'conv-5', title: 'SQL分析', lastMessage: '查询结果已生成，共返回128条记录', timestamp: new Date(Date.now() - 86400000 * 3) },
]);

const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value;
  const query = searchQuery.value.toLowerCase();
  return conversations.value.filter(c => 
    c.title.toLowerCase().includes(query) || 
    c.lastMessage.toLowerCase().includes(query)
  );
});

function formatTime(date: Date) {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / 3600000);
  
  if (hours < 1) return '刚刚';
  if (hours < 24) return `${hours}小时前`;
  if (hours < 168) return `${Math.floor(hours / 24)}天前`;
  return date.toLocaleDateString('zh-CN');
}

function handleDelete(e: Event, id: string) {
  e.stopPropagation();
  emit('delete', id);
}
</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <div class="p-3 border-b border-gray-100">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-gray-900">对话</h3>
        <button 
          @click="emit('create')"
          class="w-8 h-8 rounded-lg bg-blue-500 text-white flex items-center justify-center hover:bg-blue-600 transition-colors"
        >
          <Plus class="w-4 h-4" />
        </button>
      </div>
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索对话..."
          class="w-full pl-10 pr-4 py-2 bg-gray-50 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div 
        v-for="conv in filteredConversations"
        :key="conv.id"
        @click="emit('select', conv.id)"
        class="p-3 cursor-pointer transition-all hover:bg-gray-50 relative"
        :class="[props.currentConversationId === conv.id ? 'bg-blue-50 border-l-2 border-blue-500' : '']"
      >
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center flex-shrink-0">
            <MessageSquare class="w-5 h-5 text-white" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <h4 class="font-medium text-gray-900 truncate">{{ conv.title }}</h4>
              <span class="text-xs text-gray-400 flex-shrink-0">{{ formatTime(conv.timestamp) }}</span>
            </div>
            <p class="text-sm text-gray-500 truncate">{{ conv.lastMessage }}</p>
          </div>
          <button 
            @click="(e) => handleDelete(e, conv.id)"
            class="w-6 h-6 rounded flex items-center justify-center opacity-0 hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
        </div>
        <span 
          v-if="conv.unread" 
          class="absolute top-3 right-3 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center"
        >
          {{ conv.unread }}
        </span>
      </div>

      <div v-if="filteredConversations.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-400">
        <Clock class="w-12 h-12 mb-3 opacity-50" />
        <p class="text-sm">暂无对话</p>
        <button 
          @click="emit('create')"
          class="mt-3 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
        >
          开始新对话
        </button>
      </div>
    </div>
  </div>
</template>
