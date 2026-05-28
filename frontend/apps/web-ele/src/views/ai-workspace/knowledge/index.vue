<script setup lang="ts">import { ref, computed } from 'vue';
import { Plus, Search, Upload, MoreVertical, Eye, Trash2, Share2, Folder, FileText, Clock, CheckCircle, Loader2, AlertCircle } from 'lucide-vue-next';
interface KnowledgeSpace {
 id: string;
 name: string;
 description: string;
 visibility: 'private' | 'department' | 'public';
 documentCount: number;
 chunkCount: number;
 embeddingModel: string;
 status: 'ready' | 'processing' | 'error';
 createdAt: Date;
}
interface Document {
 id: string;
 name: string;
 spaceId: string;
 status: 'parsing' | 'chunking' | 'embedding' | 'ready' | 'error';
 chunkCount: number;
 tokenCount: number;
 uploadedAt: Date;
}
const searchQuery = ref('');
const selectedSpaceId = ref<string | null>(null);
const showUploadModal = ref(false);
const showDocumentDetail = ref(false);
const spaces = ref<KnowledgeSpace[]>([
 { id: 'space-1', name: '公司制度与规范', description: '公司级规章制度、员工手册、考勤政策等', visibility: 'public', documentCount: 12, chunkCount: 156, embeddingModel: 'BGE-M3', status: 'ready', createdAt: new Date(Date.now() - 86400000 * 7) },
 { id: 'space-2', name: '技术文档库', description: '技术架构文档、API文档、开发规范', visibility: 'department', documentCount: 8, chunkCount: 98, embeddingModel: 'BGE-M3', status: 'ready', createdAt: new Date(Date.now() - 86400000 * 3) },
 { id: 'space-3', name: '产品需求文档', description: '产品需求说明、PRD文档', visibility: 'private', documentCount: 5, chunkCount: 67, embeddingModel: 'BGE-M3', status: 'processing', createdAt: new Date(Date.now() - 86400000) },
 { id: 'space-4', name: '营销资料', description: '营销方案、活动策划、品牌资料', visibility: 'department', documentCount: 15, chunkCount: 203, embeddingModel: 'BGE-M3', status: 'ready', createdAt: new Date(Date.now() - 86400000 * 14) },
]);
const documents = ref<Document[]>([
 { id: 'doc-1', name: '企业员工手册.pdf', spaceId: 'space-1', status: 'ready', chunkCount: 45, tokenCount: 12500, uploadedAt: new Date(Date.now() - 3600000) },
 { id: 'doc-2', name: '考勤制度说明.docx', spaceId: 'space-1', status: 'ready', chunkCount: 12, tokenCount: 3200, uploadedAt: new Date(Date.now() - 7200000) },
 { id: 'doc-3', name: '新员工入职指南.pdf', spaceId: 'space-1', status: 'embedding', chunkCount: 30, tokenCount: 8500, uploadedAt: new Date(Date.now() - 1800000) },
 { id: 'doc-4', name: '薪酬福利政策.pdf', spaceId: 'space-1', status: 'chunking', chunkCount: 0, tokenCount: 0, uploadedAt: new Date(Date.now() - 900000) },
 { id: 'doc-5', name: '绩效管理制度.pdf', spaceId: 'space-1', status: 'parsing', chunkCount: 0, tokenCount: 0, uploadedAt: new Date(Date.now() - 300000) },
]);
const selectedSpaceDocuments = computed(() => {
 if (!selectedSpaceId.value)
 return documents.value;
 return documents.value.filter((d) => d.spaceId === selectedSpaceId.value);
});
const filteredSpaces = computed(() => {
 if (!searchQuery.value)
 return spaces.value;
 const query = searchQuery.value.toLowerCase();
 return spaces.value.filter((s) => s.name.toLowerCase().includes(query) || s.description.toLowerCase().includes(query));
});
function getVisibilityBadge(visibility: string) {
 const configs = {
 private: { text: '私有', class: 'bg-red-100 text-red-600' },
 department: { text: '部门共享', class: 'bg-yellow-100 text-yellow-600' },
 public: { text: '企业公开', class: 'bg-green-100 text-green-600' },
 };
 return configs[visibility as keyof typeof configs] || configs.private;
}
function getStatusIcon(status: string) {
 const icons = {
 ready: CheckCircle,
 processing: Loader2,
 parsing: Loader2,
 chunking: Loader2,
 embedding: Loader2,
 error: AlertCircle,
 };
 return icons[status as keyof typeof icons] || Loader2;
}
function getStatusText(status: string) {
 const texts = {
 ready: '已就绪',
 processing: '处理中',
 parsing: '解析中',
 chunking: '切分中',
 embedding: '向量化中',
 error: '出错',
 };
 return texts[status as keyof typeof texts] || '未知';
}
function getStatusClass(status: string) {
 const classes = {
 ready: 'text-green-600 bg-green-100',
 processing: 'text-blue-600 bg-blue-100',
 parsing: 'text-blue-600 bg-blue-100',
 chunking: 'text-blue-600 bg-blue-100',
 embedding: 'text-purple-600 bg-purple-100',
 error: 'text-red-600 bg-red-100',
 };
 return classes[status as keyof typeof classes] || 'text-gray-600 bg-gray-100';
}
function formatDate(date: Date) {
 return date.toLocaleDateString('zh-CN', {
 year: 'numeric',
 month: '2-digit',
 day: '2-digit',
 });
}
function selectSpace(spaceId: string) {
 selectedSpaceId.value = selectedSpaceId.value === spaceId ? null : spaceId;
}
</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">知识库管理</h1>
          <p class="text-sm text-gray-500">管理企业知识空间和文档</p>
        </div>
        <button
          @click="showUploadModal = true"
          class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <Plus class="w-4 h-4" />
          新建知识空间
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-hidden">
      <div class="h-full flex">
        <div class="w-80 flex-shrink-0 border-r border-gray-200 overflow-y-auto">
          <div class="p-4 border-b border-gray-200">
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索知识空间..."
                class="w-full pl-10 pr-4 py-2 bg-gray-50 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all text-sm"
              />
            </div>
          </div>

          <div class="p-2">
            <button
              @click="selectedSpaceId = null"
              class="w-full text-left p-3 rounded-xl mb-2 transition-all"
              :class="[
                !selectedSpaceId
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50 border border-transparent',
              ]"
            >
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                  <Folder class="w-5 h-5 text-white" />
                </div>
                <div>
                  <div class="font-medium text-gray-900">全部文档</div>
                  <div class="text-sm text-gray-500">{{ documents.length }} 个文档</div>
                </div>
              </div>
            </button>

            <button
              v-for="space in filteredSpaces"
              :key="space.id"
              @click="selectSpace(space.id)"
              class="w-full text-left p-3 rounded-xl mb-2 transition-all"
              :class="[
                selectedSpaceId === space.id
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50 border border-transparent',
              ]"
            >
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                  <Folder class="w-5 h-5 text-white" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-900 truncate">{{ space.name }}</div>
                  <div class="text-sm text-gray-500">{{ space.documentCount }} 个文档 · {{ space.chunkCount }} chunks</div>
                </div>
                <component
                  :is="getStatusIcon(space.status)"
                  class="w-4 h-4 flex-shrink-0"
                  :class="[
                    space.status === 'ready' ? 'text-green-500' : '',
                    space.status === 'processing' ? 'text-blue-500 animate-spin' : '',
                  ]"
                />
              </div>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">
                {{ selectedSpaceId ? spaces.find((s) => s.id === selectedSpaceId)?.name : '全部文档' }}
              </h2>
              <p class="text-sm text-gray-500">
                {{ selectedSpaceDocuments.length }} 个文档
              </p>
            </div>
            <button
              @click="showUploadModal = true"
              class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              <Upload class="w-4 h-4" />
              上传文档
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="doc in selectedSpaceDocuments"
              :key="doc.id"
              class="bg-gray-50 rounded-xl p-4 border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-lg bg-white border border-gray-200 flex items-center justify-center">
                    <FileText class="w-6 h-6 text-blue-500" />
                  </div>
                  <div>
                    <h3 class="font-medium text-gray-900">{{ doc.name }}</h3>
                    <div class="flex items-center gap-2 text-sm text-gray-500">
                      <Clock class="w-3 h-3" />
                      {{ formatDate(doc.uploadedAt) }}
                    </div>
                  </div>
                </div>
                <div class="relative group">
                  <button class="w-8 h-8 rounded-lg hover:bg-gray-200 flex items-center justify-center">
                    <MoreVertical class="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>

              <div class="flex items-center justify-between mb-3">
                <span
                  class="px-3 py-1 rounded-full text-xs font-medium"
                  :class="getStatusClass(doc.status)"
                >
                  {{ getStatusText(doc.status) }}
                </span>
              </div>

              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span>Chunks: {{ doc.chunkCount }}</span>
                <span>Tokens: {{ doc.tokenCount.toLocaleString() }}</span>
              </div>

              <div class="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200">
                <button class="flex-1 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center justify-center gap-1">
                  <Eye class="w-4 h-4" />
                  查看
                </button>
                <button class="flex-1 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center justify-center gap-1">
                  <Share2 class="w-4 h-4" />
                  分享
                </button>
                <button class="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="selectedSpaceDocuments.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
            <Folder class="w-16 h-16 mb-4 opacity-50" />
            <p class="text-lg">暂无文档</p>
            <button
              @click="showUploadModal = true"
              class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
            >
              上传文档
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>