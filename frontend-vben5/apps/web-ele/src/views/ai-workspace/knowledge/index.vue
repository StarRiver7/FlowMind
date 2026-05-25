<!-- 知识库管理 -->
<script setup lang="ts">
import { ref } from 'vue';

const documents = ref<any[]>([]);
const uploadVisible = ref(false);

const columns = [
  { prop: 'name', label: '文档名称', minWidth: 200 },
  { prop: 'type', label: '类型', width: 100 },
  { prop: 'size', label: '大小', width: 100 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'created_at', label: '上传时间', width: 180 },
];
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="uploadVisible = true">上传文档</el-button>
    </div>

    <el-card>
      <el-empty v-if="documents.length === 0" description="暂无文档，请上传知识库文档" />
      <el-table v-else :data="documents" stripe>
        <el-table-column v-for="col in columns" :key="col.prop" v-bind="col" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default>
            <el-button size="small" link type="primary">查看</el-button>
            <el-button size="small" link type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="uploadVisible" title="上传文档" width="500px">
      <el-upload
        drag
        action="/api/v1/rag/documents/upload"
        :headers="{ Authorization: 'Bearer ' }"
        accept=".pdf,.docx,.txt,.md"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div>拖拽文件到此处或点击上传</div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF / DOCX / TXT / MD 格式</div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
</style>