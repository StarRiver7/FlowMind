<!-- Prompt管理 -->
<script setup lang="ts">
import { ref } from 'vue';

const prompts = ref<any[]>([]);
const editing = ref(false);
const form = ref({ name: '', content: '', category: '' });
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>Prompt 管理</h2>
      <el-button type="primary" @click="editing = true; form = { name: '', content: '', category: '' }">
        新建 Prompt
      </el-button>
    </div>

    <el-card>
      <el-empty v-if="prompts.length === 0" description="暂无 Prompt 模板" />
      <div v-else class="prompt-grid">
        <el-card v-for="p in prompts" :key="p.id" class="prompt-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ p.name }}</span>
              <el-tag size="small">{{ p.category }}</el-tag>
            </div>
          </template>
          <p class="prompt-preview">{{ p.content?.slice(0, 120) }}...</p>
          <div class="card-actions">
            <el-button size="small" link type="primary">编辑</el-button>
            <el-button size="small" link type="danger">删除</el-button>
          </div>
        </el-card>
      </div>
    </el-card>

    <el-dialog v-model="editing" title="编辑 Prompt" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="通用" value="general" />
            <el-option label="RAG" value="rag" />
            <el-option label="工具" value="tool" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="8" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editing = false">取消</el-button>
        <el-button type="primary" @click="editing = false">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
.prompt-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.prompt-card .card-header { display: flex; justify-content: space-between; align-items: center; }
.prompt-preview { color: var(--el-text-color-secondary); font-size: 13px; line-height: 1.5; margin-bottom: 8px; }
.card-actions { display: flex; gap: 8px; }
</style>