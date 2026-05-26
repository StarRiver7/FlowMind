<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getDocuments, deleteDocument, uploadDocument } from '#/api';
import type { Document } from '#/api';
import { ElMessage, ElMessageBox } from 'element-plus';

const documents = ref<Document[]>([]);
const loading = ref(false);
const uploading = ref(false);
const total = ref(0);
const pageNum = ref(1);
const pageSize = ref(10);
const uploadForm = ref({ title: '', file: null as File | null });

async function loadDocuments() {
  loading.value = true;
  try {
    const res = await getDocuments(pageNum.value, pageSize.value);
    documents.value = res.records ?? [];
    total.value = res.total ?? 0;
  } catch { ElMessage.error('加载失败'); }
  loading.value = false;
}

async function handleUpload() {
  if (!uploadForm.value.title || !uploadForm.value.file) { ElMessage.warning('请填写标题并选择文件'); return; }
  uploading.value = true;
  try {
    await uploadDocument(uploadForm.value.title, uploadForm.value.file);
    ElMessage.success('上传成功');
    uploadForm.value = { title: '', file: null };
    loadDocuments();
  } catch { ElMessage.error('上传失败'); }
  uploading.value = false;
}

function handleFileChange(file: any) { uploadForm.value.file = file.raw ?? file; }

async function handleDelete(doc: Document) {
  try {
    await ElMessageBox.confirm('确定删除 "' + doc.title + '"？', '确认删除', { type: 'warning' });
    await deleteDocument(doc.id);
    ElMessage.success('已删除');
    loadDocuments();
  } catch { /* cancelled */ }
}

function fmtSize(b: number): string {
  if (!b) return '-';
  if (b < 1024) return b + ' B';
  if (b < 1024*1024) return (b/1024).toFixed(1) + ' KB';
  return (b/1024/1024).toFixed(1) + ' MB';
}

onMounted(loadDocuments);
</script>

<template>
  <div class="page-wrap">
    <div class="page-hd"><h2>知识库管理</h2><p class="sub">企业级 RAG 知识库，支持 PDF / DOCX / TXT / MD</p></div>
    <el-card shadow="never"><template #header>上传文档</template>
      <div class="upload-row">
        <el-input v-model="uploadForm.title" placeholder="文档标题" style="width:240px" />
        <el-upload :auto-upload="false" :limit="1" :on-change="handleFileChange" accept=".pdf,.docx,.txt,.md">
          <el-button type="primary" plain>选择文件</el-button>
        </el-upload>
        <span class="tip">PDF, DOCX, TXT, MD</span>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </div>
    </el-card>
    <el-card shadow="never" style="margin-top:16px">
      <template #header><span>文档列表 ({{ total }})</span></template>
      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="fileName" label="文件名" min-width="140" />
        <el-table-column prop="fileType" label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ row.fileType?.toUpperCase() }}</el-tag></template></el-table-column>
        <el-table-column label="大小" width="90"><template #default="{row}">{{ fmtSize(row.fileSize) }}</template></el-table-column>
        <el-table-column prop="chunksProcessed" label="Chunks" width="70" />
        <el-table-column prop="tenantId" label="租户" width="90" />
        <el-table-column prop="createTime" label="创建时间" width="170" />
        <el-table-column label="操作" width="80" fixed="right"><template #default="{row}"><el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button></template></el-table-column>
      </el-table>
      <el-pagination v-if="total > pageSize" v-model:current-page="pageNum" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="loadDocuments" style="margin-top:16px;justify-content:flex-end" />
    </el-card>
  </div>
</template>

<style scoped>.page-wrap{padding:24px;max-width:1200px}.page-hd{margin-bottom:16px}.page-hd h2{margin:0;font-size:20px}.sub{color:var(--el-text-color-secondary);font-size:13px;margin-top:4px}.upload-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.tip{font-size:12px;color:var(--el-text-color-secondary)}</style>