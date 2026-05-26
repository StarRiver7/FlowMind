<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { listModels, updateModel } from '#/api';
import type { ModelConfig } from '#/api';
import { ElMessage } from 'element-plus';

const models = ref<ModelConfig[]>([]);
const loading = ref(false);
const activeModel = ref<string>('');
const dialog = ref(false);
const form = ref<Partial<ModelConfig>>({});

async function load() {
  loading.value = true;
  try { const r = await listModels(); models.value = Array.isArray(r) ? r : (r as any)?.data ?? []; }
  catch { /* API pending */ }
  loading.value = false;
}

function edit(m: ModelConfig) { form.value = { ...m }; dialog.value = true; }

async function save() {
  try { if (form.value.id) await updateModel(form.value.id, form.value); dialog.value = false; ElMessage.success('已保存'); load(); }
  catch { ElMessage.error('保存失败'); }
}

onMounted(load);
</script>

<template>
  <div class="page-wrap">
    <div class="page-hd"><h2>模型管理</h2><p class="sub">配置 AI 模型 Provider，支持 DeepSeek / OpenAI 兼容</p></div>
    <el-card shadow="never">
      <template #header><span>模型列表</span></template>
      <el-table :data="models" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="provider" label="Provider" width="120"><template #default="{row}"><el-tag :type="row.provider==='deepseek'?'success':''" size="small">{{ row.provider }}</el-tag></template></el-table-column>
        <el-table-column prop="modelName" label="模型" width="200" />
        <el-table-column prop="temperature" label="温度" width="80" />
        <el-table-column prop="maxTokens" label="Max Tokens" width="110" />
        <el-table-column label="启用" width="70"><template #default="{row}"><el-switch :model-value="row.enabled" size="small" disabled /></template></el-table-column>
        <el-table-column label="操作" width="70"><template #default="{row}"><el-button type="primary" link size="small" @click="edit(row)">配置</el-button></template></el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="dialog" title="模型配置" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="Provider"><el-select v-model="form.provider"><el-option label="DeepSeek" value="deepseek" /><el-option label="OpenAI" value="openai" /></el-select></el-form-item>
        <el-form-item label="模型名"><el-input v-model="form.modelName" placeholder="如: deepseek-chat" /></el-form-item>
        <el-form-item label="API Key"><el-input v-model="form.apiKey" type="password" show-password /></el-form-item>
        <el-form-item label="温度"><el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input /></el-form-item>
        <el-form-item label="Max Tokens"><el-input-number v-model="form.maxTokens" :min="1" :max="128000" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>.page-wrap{padding:24px;max-width:1200px}.page-hd{margin-bottom:16px}.page-hd h2{margin:0;font-size:20px}.sub{color:var(--el-text-color-secondary);font-size:13px;margin-top:4px}</style>