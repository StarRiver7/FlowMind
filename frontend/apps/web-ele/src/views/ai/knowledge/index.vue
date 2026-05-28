<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useKnowledgeStore, type DocStatus } from '#/store/knowledge';

const store = useKnowledgeStore();
const fileInputRef = ref<HTMLInputElement>();
const uploadingFile = ref<{ name: string; progress: number; status: string } | null>(null);

onMounted(async () => {
  await store.loadDocuments();
});

const statusLabel: Record<DocStatus, string> = {
  UPLOADING: '上传中',
  PARSING: '解析中',
  CHUNKING: '分块中',
  EMBEDDING: '向量化',
  READY: '就绪',
  FAILED: '失败',
};

const statusColor: Record<DocStatus, string> = {
  UPLOADING: 'text-blue-500',
  PARSING: 'text-amber-500',
  CHUNKING: 'text-amber-500',
  EMBEDDING: 'text-purple-500',
  READY: 'text-green-500',
  FAILED: 'text-red-500',
};

const statusBg: Record<DocStatus, string> = {
  UPLOADING: 'bg-blue-50',
  PARSING: 'bg-amber-50',
  CHUNKING: 'bg-amber-50',
  EMBEDDING: 'bg-purple-50',
  READY: 'bg-green-50',
  FAILED: 'bg-red-50',
};

const isProcessing = (status: DocStatus) =>
  ['UPLOADING', 'PARSING', 'CHUNKING', 'EMBEDDING'].includes(status);

function triggerUpload() {
  fileInputRef.value?.click();
}

async function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (!files || files.length === 0) return;
  const file = files[0];

  uploadingFile.value = { name: file.name, progress: 0, status: '上传中...' };

  try {
    const ok = await store.uploadFile(1, file);
    if (ok) {
      uploadingFile.value = { name: file.name, progress: 100, status: '上传完成' };
      // Simulate processing pipeline animation
      simulateProcessing(file.name);
    } else {
      uploadingFile.value = { name: file.name, progress: 0, status: '上传失败' };
    }
  } catch {
    uploadingFile.value = { name: file.name, progress: 0, status: '上传失败' };
  }

  if (fileInputRef.value) fileInputRef.value.value = '';
}

async function simulateProcessing(filename: string) {
  // Update the latest document status through the pipeline stages
  const stages: { status: DocStatus; delay: number; label: string }[] = [
    { status: 'PARSING', delay: 1000, label: '正在解析文档...' },
    { status: 'CHUNKING', delay: 1500, label: '正在分块处理...' },
    { status: 'EMBEDDING', delay: 1500, label: '正在生成向量...' },
    { status: 'READY', delay: 1000, label: '处理完成' },
  ];

  // Find the newly uploaded doc
  const latestDoc = store.documents[0];
  if (!latestDoc) return;

  for (const stage of stages) {
    await new Promise(r => setTimeout(r, stage.delay));
    if (uploadingFile.value) {
      uploadingFile.value.status = stage.label;
      uploadingFile.value.progress = Math.min(
        100,
        Math.floor((stages.indexOf(stage) + 1) / stages.length * 100)
      );
    }
    store.updateDocStatus(latestDoc.id, stage.status);
  }

  setTimeout(() => { uploadingFile.value = null; }, 2000);
}

// ── File size formatter ──
function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Document type icon ──
function fileIcon(ext: string): string {
  const map: Record<string, string> = {
    pdf: '&#128196;', doc: '&#128196;', docx: '&#128196;',
    xlsx: '&#128200;', csv: '&#128200;',
    txt: '&#128221;', md: '&#128221;',
  };
  return map[ext] || '&#128206;';
}
</script>

<template>
  <div class="h-full overflow-y-auto isu-scrollbar">
    <div class="max-w-4xl mx-auto px-8 py-8">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-xl font-bold text-gray-800">知识库</h1>
          <p class="mt-1 text-sm text-gray-500">管理企业知识空间与文档</p>
        </div>
        <button
          class="flex items-center gap-2 rounded-xl bg-blue-500 px-5 py-2.5 text-sm font-medium text-white
                 hover:bg-blue-600 shadow-sm shadow-blue-200 transition-all duration-150"
          @click="triggerUpload"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          上传文档
        </button>
        <input
          ref="fileInputRef"
          type="file"
          class="hidden"
          accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx"
          @change="onFileChange"
        />
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-3 gap-4 mb-8">
        <div class="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-sm transition-shadow">
          <div class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1">文档总数</div>
          <div class="text-2xl font-bold text-gray-800">{{ store.totalDocs }}</div>
        </div>
        <div class="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-sm transition-shadow">
          <div class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1">总 Chunk</div>
          <div class="text-2xl font-bold text-gray-800">
            {{ store.documents.reduce((s, d) => s + d.chunkCount, 0) }}
          </div>
        </div>
        <div class="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-sm transition-shadow">
          <div class="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1">总 Token</div>
          <div class="text-2xl font-bold text-gray-800">
            {{ store.documents.reduce((s, d) => s + d.tokenCount, 0).toLocaleString() }}
          </div>
        </div>
      </div>

      <!-- Upload progress (inline) -->
      <Transition name="fade">
        <div v-if="uploadingFile" class="mb-6 rounded-xl border border-blue-100 bg-blue-50/50 p-5 animate-isu-fade-in">
          <div class="flex items-center gap-3">
            <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-100 text-blue-600">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-700 truncate">{{ uploadingFile.name }}</div>
              <div class="flex items-center gap-2 mt-1">
                <div class="flex-1 h-1.5 rounded-full bg-blue-100 overflow-hidden">
                  <div
                    class="h-full rounded-full bg-blue-500 transition-all duration-500"
                    :style="{ width: `${uploadingFile.progress}%` }"
                  />
                </div>
                <span class="text-[11px] font-medium"
                      :class="{
                        'text-blue-500': uploadingFile.status.includes('中'),
                        'text-green-500': uploadingFile.status.includes('完成'),
                        'text-red-500': uploadingFile.status.includes('失败'),
                      }">
                  {{ uploadingFile.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Document list -->
      <div class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
        文档列表
      </div>

      <div v-if="store.documents.length === 0" class="rounded-xl border border-dashed border-gray-200 p-12 text-center">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gray-100 mb-4">
          <svg class="text-gray-400" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <div class="text-sm text-gray-500 mb-1">还没有上传文档</div>
        <div class="text-xs text-gray-400 mb-4">将 PDF、Word、TXT 等文档上传到企业知识库</div>
        <button
          class="inline-flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white
                 hover:bg-blue-600 transition-colors"
          @click="triggerUpload"
        >
          上传第一份文档
        </button>
      </div>

      <div class="space-y-2">
        <div
          v-for="doc in store.documents"
          :key="doc.id"
          class="group rounded-xl border border-gray-100 bg-white p-4 hover:border-gray-200 hover:shadow-sm
                 transition-all duration-150"
        >
          <div class="flex items-center gap-4">
            <!-- Icon -->
            <div class="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                 :class="statusBg(doc.parseStatus)">
              <span class="text-lg" v-html="fileIcon(doc.fileType?.toLowerCase() || '')" />
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <div class="text-sm font-medium text-gray-800 truncate">{{ doc.filename }}</div>
                <span
                  class="isu-badge shrink-0"
                  :class="{
                    'isu-badge-running': isProcessing(doc.parseStatus),
                    'isu-badge-completed': doc.parseStatus === 'READY',
                    'isu-badge-failed': doc.parseStatus === 'FAILED',
                    'isu-badge-pending': doc.parseStatus === 'UPLOADING',
                  }"
                >
                  <span
                    v-if="isProcessing(doc.parseStatus)"
                    class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"
                  />
                  {{ statusLabel[doc.parseStatus] }}
                </span>
              </div>
              <div class="flex items-center gap-4 mt-1 text-[11px] text-gray-400">
                <span>{{ formatSize(doc.fileSize) }}</span>
                <span v-if="doc.chunkCount > 0">{{ doc.chunkCount }} 个 Chunk</span>
                <span v-if="doc.tokenCount > 0">{{ doc.tokenCount.toLocaleString() }} Token</span>
                <span>{{ doc.uploadTime?.slice(0, 10) }}</span>
              </div>
            </div>

            <!-- Processing animation for active docs -->
            <div v-if="isProcessing(doc.parseStatus)" class="flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full animate-isu-pulse-dot"
                    :class="{
                      'bg-blue-500': doc.parseStatus === 'UPLOADING',
                      'bg-amber-500': doc.parseStatus === 'PARSING' || doc.parseStatus === 'CHUNKING',
                      'bg-purple-500': doc.parseStatus === 'EMBEDDING',
                    }"
              />
              <span class="w-1.5 h-1.5 rounded-full animate-isu-pulse-dot"
                    :class="{
                      'bg-blue-500': doc.parseStatus === 'UPLOADING',
                      'bg-amber-500': doc.parseStatus === 'PARSING' || doc.parseStatus === 'CHUNKING',
                      'bg-purple-500': doc.parseStatus === 'EMBEDDING',
                    }"
                    style="animation-delay: 0.3s"
              />
              <span class="w-1.5 h-1.5 rounded-full animate-isu-pulse-dot"
                    :class="{
                      'bg-blue-500': doc.parseStatus === 'UPLOADING',
                      'bg-amber-500': doc.parseStatus === 'PARSING' || doc.parseStatus === 'CHUNKING',
                      'bg-purple-500': doc.parseStatus === 'EMBEDDING',
                    }"
                    style="animation-delay: 0.6s"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
