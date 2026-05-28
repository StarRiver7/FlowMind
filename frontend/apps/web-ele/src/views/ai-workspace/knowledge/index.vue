<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { KnowledgeBase, Document } from '#/api/core/types';
import { requestClient } from '#/api/request';

const spaces = ref<KnowledgeBase[]>([]);
const documents = ref<Document[]>([]);
const selectedSpace = ref<number | null>(null);
const uploadLoading = ref(false);
const uploadFileName = ref('');

onMounted(async () => {
  await loadSpaces();
});

async function loadSpaces() {
  try {
    const res = await requestClient.get<{ data: KnowledgeBase[] }>('/api/kb/list');
    spaces.value = res.data || [];
  } catch { /* graceful */ }
}

async function selectSpace(spaceId: number) {
  selectedSpace.value = spaceId;
  await loadDocuments(spaceId);
}

async function loadDocuments(spaceId: number) {
  try {
    const res = await requestClient.get<{ data: { documents: Document[] } }>(
      `/api/kb/${spaceId}/documents`,
    );
    documents.value = res.data?.documents || [];
  } catch { /* graceful */ }
}

async function handleUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file || !selectedSpace.value) return;

  uploadLoading.value = true;
  uploadFileName.value = file.name;

  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('knowledge_base_id', String(selectedSpace.value));

    const token = localStorage.getItem('flowmind_token') || '';
    await fetch('/api/kb/upload', {
      method: 'POST',
      headers: { Authorization: token ? `Bearer ${token}` : '' },
      body: formData,
    });

    await loadDocuments(selectedSpace.value);
  } catch (err) {
    console.error('Upload failed:', err);
  } finally {
    uploadLoading.value = false;
    uploadFileName.value = '';
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    UPLOADED: '已上传',
    PARSING: '解析中...',
    PARSED: '已解析',
    CHUNKING: '切分中...',
    CHUNKED: '已切分',
    EMBEDDING: '向量化中...',
    INDEXING: '索引中...',
    READY: '就绪',
    FAILED: '失败',
  };
  return map[status] || status;
}

function statusClass(status: string): string {
  if (status === 'READY') return 'bg-green-100 text-green-700';
  if (status === 'FAILED') return 'bg-red-100 text-red-700';
  if (status.endsWith('ING')) return 'bg-blue-100 text-blue-700 animate-pulse';
  return 'bg-gray-100 text-gray-600';
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
</script>

<template>
  <div class="flex h-full">
    <!-- Left: Knowledge spaces -->
    <aside class="w-56 shrink-0 border-r border-gray-200/80 bg-white p-3">
      <div class="mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
        知识空间
      </div>
      <div class="space-y-0.5">
        <div
          v-for="space in spaces"
          :key="space.id"
          class="cursor-pointer rounded-lg px-3 py-2 text-sm transition-all"
          :class="selectedSpace === space.id
            ? 'bg-blue-50 text-blue-700 font-medium'
            : 'text-gray-600 hover:bg-gray-50'"
          @click="selectSpace(space.id)"
        >
          <div class="flex items-center gap-2">
            <span class="text-base">📁</span>
            <span class="truncate">{{ space.name }}</span>
          </div>
          <div class="mt-0.5 ml-7 text-[11px] text-gray-400">
            {{ space.document_count || 0 }} 文档 · {{ space.chunk_count || 0 }} Chunk
          </div>
        </div>

        <div
          v-if="spaces.length === 0"
          class="py-6 text-center text-xs text-gray-400"
        >
          暂无知识空间
        </div>
      </div>
    </aside>

    <!-- Right: Document list -->
    <div class="flex-1 overflow-y-auto p-6">
      <!-- Upload area -->
      <div
        v-if="selectedSpace"
        class="mb-6 rounded-xl border-2 border-dashed border-gray-200 p-8 text-center
               hover:border-blue-300 hover:bg-blue-50/20 transition-all cursor-pointer"
        @click="($refs.fileInput as HTMLInputElement)?.click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.docx,.md,.txt"
          class="hidden"
          @change="handleUpload"
        />
        <div v-if="!uploadLoading" class="text-gray-500">
          <div class="mb-2 text-3xl">📤</div>
          <div class="text-sm font-medium">上传文档到知识空间</div>
          <div class="mt-1 text-xs text-gray-400">支持 PDF · DOCX · MD · TXT</div>
        </div>
        <div v-else class="text-blue-600">
          <div class="mb-2 text-3xl animate-bounce">⏳</div>
          <div class="text-sm font-medium">正在上传 {{ uploadFileName }}...</div>
        </div>
      </div>

      <div v-if="!selectedSpace && spaces.length > 0" class="flex flex-col items-center justify-center h-64">
        <div class="text-4xl mb-3">📚</div>
        <div class="text-sm text-gray-500">选择左侧知识空间查看文档</div>
      </div>

      <!-- Document cards -->
      <div v-if="selectedSpace" class="space-y-2">
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="rounded-xl border border-gray-100 bg-white p-4 hover:border-blue-200 hover:shadow-sm
                 transition-all duration-200"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <!-- File icon -->
              <span class="text-xl">
                {{ doc.file_type === 'pdf' ? '📕' : doc.file_type === 'docx' ? '📘' : doc.file_type === 'md' ? '📝' : '📄' }}
              </span>
              <div>
                <div class="text-sm font-medium text-gray-700">{{ doc.filename }}</div>
                <div class="mt-0.5 flex items-center gap-3 text-[11px] text-gray-400">
                  <span>{{ formatSize(doc.file_size) }}</span>
                  <span>{{ doc.file_type?.toUpperCase() }}</span>
                  <span v-if="doc.chunk_count > 0">{{ doc.chunk_count }} Chunks</span>
                  <span v-if="doc.token_count > 0">{{ doc.token_count }} Tokens</span>
                </div>
              </div>
            </div>

            <!-- Status badge -->
            <div class="flex items-center gap-3">
              <!-- Processing animation -->
              <div
                v-if="doc.parse_status?.endsWith('ING')"
                class="flex items-center gap-1.5"
              >
                <div class="flex gap-0.5">
                  <span class="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 0ms" />
                  <span class="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 150ms" />
                  <span class="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 300ms" />
                </div>
              </div>

              <span
                class="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium"
                :class="statusClass(doc.parse_status)"
              >
                {{ statusLabel(doc.parse_status) }}
              </span>
            </div>
          </div>

          <!-- Progress bar for processing -->
          <div
            v-if="doc.parse_status?.endsWith('ING')"
            class="mt-3 h-1 rounded-full bg-gray-100 overflow-hidden"
          >
            <div class="h-full rounded-full bg-gradient-to-r from-blue-400 to-purple-400 animate-pulse w-3/4" />
          </div>
        </div>

        <div
          v-if="documents.length === 0 && !uploadLoading"
          class="py-12 text-center text-sm text-gray-400"
        >
          暂无文档，拖拽或点击上方区域上传
        </div>
      </div>
    </div>
  </div>
</template>
