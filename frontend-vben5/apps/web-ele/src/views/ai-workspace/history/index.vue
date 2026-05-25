<!-- 会话历史 -->
<script setup lang="ts">
import { ref } from 'vue';

const sessions = ref<any[]>([]);
const searchKeyword = ref('');

const columns = [
  { prop: 'title', label: '会话标题', minWidth: 200 },
  { prop: 'model', label: '模型', width: 120 },
  { prop: 'message_count', label: '消息数', width: 100 },
  { prop: 'created_at', label: '创建时间', width: 180 },
  { prop: 'updated_at', label: '最后活跃', width: 180 },
];
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>会话历史</h2>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索会话..."
        style="width: 240px"
        clearable
      />
    </div>

    <el-card>
      <el-empty v-if="sessions.length === 0" description="暂无历史会话记录" />
      <el-table v-else :data="sessions" stripe>
        <el-table-column v-for="col in columns" :key="col.prop" v-bind="col" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default>
            <el-button size="small" link type="primary">查看</el-button>
            <el-button size="small" link type="danger">删除</el-button>
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