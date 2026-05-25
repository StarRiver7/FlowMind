<!-- 模型管理 -->
<script setup lang="ts">
import { ref } from 'vue';

const models = ref([
  { id: 1, name: 'DeepSeek-V3', provider: 'DeepSeek', type: 'chat', status: 'active' },
  { id: 2, name: 'DeepSeek-R1', provider: 'DeepSeek', type: 'reasoning', status: 'active' },
  { id: 3, name: 'BGE-M3', provider: 'BAAI', type: 'embedding', status: 'active' },
]);
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary">添加模型</el-button>
    </div>

    <el-card>
      <el-table :data="models" stripe>
        <el-table-column prop="name" label="模型名称" minWidth="180" />
        <el-table-column prop="provider" label="提供商" width="120" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type === 'chat' ? '对话' : row.type === 'reasoning' ? '推理' : '嵌入' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default>
            <el-button size="small" link type="primary">配置</el-button>
            <el-button size="small" link type="warning">停用</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
</style>