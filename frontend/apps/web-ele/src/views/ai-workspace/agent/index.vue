<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { aiRequestClient } from '#/api/request';

const tools = ref<any[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try { const r = await aiRequestClient.get('/tools'); tools.value = r.tools ?? []; }
  catch { /* pending */ }
  loading.value = false;
}

onMounted(load);
</script>

<template>
  <div class="page-wrap">
    <div class="page-hd"><h2>Agent Router</h2><p class="sub">LangGraph Agent 执行链路可视化与工具管理</p></div>

    <!-- 流程图占位 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <template #header>执行流程</template>
      <div class="flow-diagram">
        <div class="flow-node start">用户问题</div>
        <div class="flow-arrow">→</div>
        <div class="flow-node router">Router</div>
        <div class="flow-arrow">→</div>
        <div class="flow-node chat">Chat 节点</div>
        <div class="flow-arrow">→</div>
        <div class="flow-node rag">RAG 检索</div>
        <div class="flow-arrow">→</div>
        <div class="flow-node tool">Tool 调用</div>
        <div class="flow-arrow">→</div>
        <div class="flow-node end">生成回答</div>
      </div>
    </el-card>

    <!-- 工具列表 -->
    <el-card shadow="never">
      <template #header><span>可用工具 ({{ tools.length }})</span></template>
      <el-table :data="tools" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column label="状态" width="80"><template #default><el-tag type="success" size="small">就绪</el-tag></template></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.page-wrap{padding:24px;max-width:1200px}.page-hd{margin-bottom:16px}.page-hd h2{margin:0;font-size:20px}.sub{color:var(--el-text-color-secondary);font-size:13px;margin-top:4px}
.flow-diagram{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:16px 0}
.flow-node{padding:10px 20px;border-radius:8px;font-size:13px;font-weight:500;text-align:center;min-width:80px}
.flow-node.start{background:var(--el-color-primary-light-9);color:var(--el-color-primary)}
.flow-node.router{background:var(--el-color-warning-light-9);color:var(--el-color-warning)}
.flow-node.chat{background:var(--el-color-success-light-9);color:var(--el-color-success)}
.flow-node.rag{background:var(--el-color-info-light-9);color:var(--el-color-info)}
.flow-node.tool{background:var(--el-color-danger-light-9);color:var(--el-color-danger)}
.flow-node.end{background:var(--el-fill-color);color:var(--el-text-color-primary)}
.flow-arrow{font-size:18px;color:var(--el-text-color-placeholder)}
</style>