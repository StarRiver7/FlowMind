<script setup lang="ts">
import { useUserStore } from '@vben/stores';
const userStore = useUserStore();
</script>

<template>
  <div class="dashboard-home">
    <div class="welcome-card">
      <h1>欢迎使用</h1>
      <p v-if="userStore.userInfo?.realName">你好，{{ userStore.userInfo.realName }}</p>
      <p class="desc">企业级 AI Agent 平台 — RAG 检索增强生成 · LangGraph Agent 路由 · 知识库管理</p>
      <div class="quick-links">
        <el-card shadow="hover" class="link-card" @click="$router.push('/ai-workspace/chat')">
          <el-icon :size="28"><ChatDotRound /></el-icon>
          <span>AI 聊天</span>
        </el-card>
        <el-card shadow="hover" class="link-card" @click="$router.push('/ai-workspace/knowledge')">
          <el-icon :size="28"><FolderOpened /></el-icon>
          <span>知识库</span>
        </el-card>
        <el-card shadow="hover" class="link-card" @click="$router.push('/ai-workspace/prompt')">
          <el-icon :size="28"><Document /></el-icon>
          <span>Prompt</span>
        </el-card>
        <el-card shadow="hover" class="link-card" @click="$router.push('/ai-workspace/agent')">
          <el-icon :size="28"><Connection /></el-icon>
          <span>Agent</span>
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-home { padding: 32px; max-width: 900px; margin: 0 auto; }
.welcome-card { text-align: center; }
.welcome-card h1 { font-size: 26px; margin-bottom: 8px; }
.desc { color: var(--el-text-color-secondary); font-size: 14px; margin-bottom: 32px; }
.quick-links { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.link-card { cursor: pointer; text-align: center; padding: 20px 0; transition: transform .2s; }
.link-card:hover { transform: translateY(-2px); }
.link-card span { display: block; margin-top: 8px; font-size: 14px; font-weight: 500; }
</style>
