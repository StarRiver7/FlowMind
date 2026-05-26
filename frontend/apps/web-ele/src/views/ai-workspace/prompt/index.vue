<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { listPrompts, updatePrompt, togglePrompt } from '#/api';
import type { PromptTemplate } from '#/api';
import { ElMessage } from 'element-plus';

const prompts = ref<PromptTemplate[]>([]);
const loading = ref(false);
const dialog = ref(false);
const form = ref<Partial<PromptTemplate>>({ name: '', content: '', enabled: true });
const editId = ref<string | null>(null);

async function load() {
  loading.value = true;
  try { const r = await listPrompts(); prompts.value = Array.isArray(r) ? r : (r as any)?.data ?? []; }
  catch { /* API pending */ }
  loading.value = false;
}

function create() { form.value = { name: '', content: '', variables: [], enabled: true }; editId.value = null; dialog.value = true; }
function edit(p: PromptTemplate) { form.value = { ...p }; editId.value = p.id; dialog.value = true; }

async function save() {
  try {
    if (editId.value) await updatePrompt(editId.value, form.value);
    dialog.value = false; ElMessage.success('已保存'); load();
  } catch { ElMessage.error('保存失败'); }
}

async function toggle(p: PromptTemplate) {
  try { await togglePrompt(p.id, !p.enabled); p.enabled = !p.enabled; }
  catch { ElMessage.error('操作失败'); }
}

onMounted(load);
</script>

<template>
  <div class="page-wrap">
    <div class="page-hd"><h2>Prompt 管理</h2><p class="sub">管理 AI 提示词模板，支持 Jinja2 变量注入</p></div>
    <el-card shadow="never">
      <template #header><div style="display:flex;justify-content:space-between;align-items:center"><span>Prompt 列表</span><el-button type="primary" size="small" @click="create">新建</el-button></div></template>
      <el-table :data="prompts" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column label="内容预览" min-width="260"><template #default="{row}">{{ (row.content??'').slice(0,100) }}{{ (row.content??'').length>100?'...':'' }}</template></el-table-column>
        <el-table-column prop="version" label="版本" width="70" />
        <el-table-column label="变量" width="200"><template #default="{row}"><el-tag v-for="v in (row.variables??[])" :key="v" size="small" style="margin:1px">{{ v }}</el-tag></template></el-table-column>
        <el-table-column label="启用" width="70"><template #default="{row}"><el-switch :model-value="row.enabled" size="small" @change="toggle(row)" /></template></el-table-column>
        <el-table-column label="操作" width="70"><template #default="{row}"><el-button type="primary" link size="small" @click="edit(row)">编辑</el-button></template></el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="dialog" :title="editId?'编辑':'新建'" width="560px">
      <el-form :model="form" label-width="60px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="8" placeholder="使用 {{ variable }} 语法" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>.page-wrap{padding:24px;max-width:1200px}.page-hd{margin-bottom:16px}.page-hd h2{margin:0;font-size:20px}.sub{color:var(--el-text-color-secondary);font-size:13px;margin-top:4px}</style>