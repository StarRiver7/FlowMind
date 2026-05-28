<script setup lang="ts">import { ref, computed } from 'vue';
import { Search, FileText, FolderOpen, Tag, ExternalLink, ChevronRight, Clock, User } from 'lucide-vue-next';
interface Document {
 id: string;
 title: string;
 category: string;
 tags: string[];
 author: string;
 updatedAt: Date;
 size: string;
 views: number;
}
const searchQuery = ref('');
const selectedCategory = ref('all');
const categories = ['all', '企业制度', '部门文档', 'Wiki', '公开知识'];
const documents = ref<Document[]>([
 { id: 'doc-1', title: '企业员工手册', category: '企业制度', tags: ['HR', '制度', '员工'], author: 'HR部门', updatedAt: new Date(Date.now() - 86400000), size: '2.3 MB', views: 1256 },
 { id: 'doc-2', title: '考勤管理制度', category: '企业制度', tags: ['HR', '考勤', '制度'], author: 'HR部门', updatedAt: new Date(Date.now() - 86400000 * 2), size: '512 KB', views: 892 },
 { id: 'doc-3', title: '技术架构文档', category: '部门文档', tags: ['技术', '架构', '设计'], author: '技术部', updatedAt: new Date(Date.now() - 86400000 * 3), size: '4.1 MB', views: 445 },
 { id: 'doc-4', title: '产品需求说明', category: '部门文档', tags: ['产品', '需求', '设计'], author: '产品部', updatedAt: new Date(Date.now() - 86400000 * 5), size: '1.2 MB', views: 623 },
 { id: 'doc-5', title: '公司Wiki首页', category: 'Wiki', tags: ['Wiki', '指南'], author: '管理员', updatedAt: new Date(Date.now() - 86400000 * 7), size: '256 KB', views: 2156 },
 { id: 'doc-6', title: '新员工入职指南', category: 'Wiki', tags: ['入职', '指南', '新人'], author: 'HR部门', updatedAt: new Date(Date.now() - 86400000 * 10), size: '768 KB', views: 1890 },
 { id: 'doc-7', title: '企业文化手册', category: '公开知识', tags: ['文化', '企业'], author: '行政部', updatedAt: new Date(Date.now() - 86400000 * 14), size: '1.8 MB', views: 1567 },
 { id: 'doc-8', title: '办公设备使用规范', category: '公开知识', tags: ['设备', '规范'], author: '行政部', updatedAt: new Date(Date.now() - 86400000 * 21), size: '384 KB', views: 789 },
]);
const filteredDocuments = computed(() => {
 let result = documents.value;
 if (searchQuery.value) {
 const query = searchQuery.value.toLowerCase();
 result = result.filter((d) => d.title.toLowerCase().includes(query) || d.tags.some((t) => t.toLowerCase().includes(query)));
 }
 if (selectedCategory.value !== 'all') {
 result = result.filter((d) => d.category === selectedCategory.value);
 }
 return result;
});
function formatDate(date: Date) {
 const now = new Date();
 const diff = now.getTime() - date.getTime();
 const days = Math.floor(diff / 86400000);
 if (days === 0)
 return '今天';
 if (days === 1)
 return '昨天';
 if (days < 7)
 return `${days}天前`;
 if (days < 30)
 return `${Math.floor(days / 7)}周前`;
 return date.toLocaleDateString('zh-CN');
}
</script>

<template>
  <div class="h-full bg-white overflow-y-auto">
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">文档中心</h1>
          <p class="text-sm text-gray-500">企业公开知识中心</p>
        </div>
      </div>

      <div class="flex items-center gap-4 mb-6">
        <div class="relative flex-1 max-w-md">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索文档..."
            class="w-full pl-10 pr-4 py-2 bg-gray-50 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
          />
        </div>
        <div class="flex items-center gap-2">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            class="px-3 py-1.5 rounded-lg text-sm transition-all"
            :class="[
              selectedCategory === cat
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
            ]"
          >
            {{ cat === 'all' ? '全部' : cat }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="doc in filteredDocuments"
          :key="doc.id"
          class="p-4 bg-gray-50 rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all cursor-pointer group"
        >
          <div class="flex items-start gap-3">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center flex-shrink-0">
              <FileText class="w-6 h-6 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">{{ doc.category }}</span>
              </div>
              <h3 class="font-medium text-gray-900 truncate group-hover:text-blue-600 transition-colors">{{ doc.title }}</h3>
              <div class="flex flex-wrap gap-1 mt-2">
                <span
                  v-for="tag in doc.tags"
                  :key="tag"
                  class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
                >
                  {{ tag }}
                </span>
              </div>
              <div class="flex items-center justify-between mt-3 text-xs text-gray-500">
                <div class="flex items-center gap-3">
                  <span class="flex items-center gap-1">
                    <User class="w-3 h-3" />
                    {{ doc.author }}
                  </span>
                  <span class="flex items-center gap-1">
                    <Clock class="w-3 h-3" />
                    {{ formatDate(doc.updatedAt) }}
                  </span>
                </div>
                <ChevronRight class="w-4 h-4 text-gray-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredDocuments.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
        <FolderOpen class="w-16 h-16 mb-4 opacity-50" />
        <p class="text-lg">暂无文档</p>
      </div>
    </div>
  </div>
</template>