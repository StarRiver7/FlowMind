<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { listConversations, getMessages } from '#/api';
import type { Conversation, Message } from '#/api';
import { ElMessage } from 'element-plus';

const conversations = ref<Conversation[]>([]);
const messages = ref<Message[]>([]);
const loading = ref(false);
const activeConvId = ref<string | null>(null);
const msgLoading = ref(false);

async function loadConvs() {
  loading.value = true;
  try {
    const userId = (() => { try { return JSON.parse(localStorage.getItem('flowmind_user')??'{}').userId } catch { return '0' } })();
    const r = await listConversations(userId);
    conversations.value = r.conversations ?? [];
  } catch { /* ignore */ }
  loading.value = false;
}

async function showMessages(convId: string) {
  activeConvId.value = convId;
  msgLoading.value = true;
  try {
    const r = await getMessages(convId);
    messages.value = r.messages ?? [];
  } catch { ElMessage.error('加载消息失败'); }
  msgLoading.value = false;
}

onMounted(loadConvs);
</script>

<template>
  <div class="page-wrap">
    <div class="page-hd"><h2>会话历史</h2><p class="sub">查看历史会话和对话记录</p></div>
    <div class="history-layout">
      <div class="conv-list">
        <el-card shadow="never">
          <template #header><span>会话列表 ({{ conversations.length }})</span></template>
          <div v-for="c in conversations" :key="c.id" class="conv-row" :class="{active: String(c.id)===activeConvId}" @click="showMessages(String(c.id))">
            <div class="conv-name">{{ c.title || '未命名' }}</div>
            <div class="conv-meta">{{ c.modelName || '-' }} · {{ c.messageCount ?? 0 }} 条消息</div>
            <div class="conv-time">{{ c.lastMessageAt?.slice(0,16) || c.createTime?.slice(0,16) || '-' }}</div>
          </div>
          <el-empty v-if="!loading && !conversations.length" description="暂无会话" :image-size="48" />
        </el-card>
      </div>
      <div class="msg-area">
        <el-card shadow="never" v-loading="msgLoading">
          <template #header><span>{{ activeConvId ? '对话记录' : '请选择会话' }}</span></template>
          <div v-if="activeConvId && messages.length" class="msg-list">
            <div v-for="m in messages" :key="m.id" class="msg-item" :class="m.role">
              <span class="msg-role">{{ m.role === 'user' ? '用户' : m.role === 'assistant' ? 'AI' : m.role }}</span>
              <div class="msg-text">{{ m.content?.slice(0, 500) }}{{ (m.content??'').length>500?'...':'' }}</div>
              <span class="msg-meta">{{ m.tokensUsed ?? 0 }} tokens · {{ m.intent || 'chat' }}</span>
            </div>
          </div>
          <el-empty v-else-if="activeConvId" description="暂无消息" :image-size="48" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap{padding:24px;max-width:1400px}.page-hd{margin-bottom:16px}.page-hd h2{margin:0;font-size:20px}.sub{color:var(--el-text-color-secondary);font-size:13px;margin-top:4px}
.history-layout{display:flex;gap:16px}.conv-list{width:320px;flex-shrink:0}.msg-area{flex:1}
.conv-row{padding:10px 12px;cursor:pointer;border-radius:6px;margin-bottom:4px;transition:background .15s}
.conv-row:hover{background:var(--el-fill-color-light)}.conv-row.active{background:var(--el-color-primary-light-9)}
.conv-name{font-size:13px;font-weight:500}.conv-meta{font-size:11px;color:var(--el-text-color-secondary);margin-top:2px}.conv-time{font-size:11px;color:var(--el-text-color-placeholder)}
.msg-list{max-height:calc(100vh - 260px);overflow-y:auto}.msg-item{padding:10px 12px;border-radius:6px;margin-bottom:8px;background:var(--el-fill-color-lighter)}
.msg-item.user{background:var(--el-color-primary-light-9)}.msg-role{font-size:11px;font-weight:600;text-transform:uppercase}.msg-text{font-size:13px;line-height:1.6;margin:4px 0;word-break:break-word}.msg-meta{font-size:11px;color:var(--el-text-color-placeholder)}
</style>