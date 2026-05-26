<script setup lang="ts">
import type { SourceCitation } from '#/api';

defineProps<{ sources: SourceCitation[] }>();
</script>

<template>
  <div class="source-panel">
    <div v-if="!sources.length" class="empty-state">
      <el-empty description="暂无引用来源" :image-size="60" />
    </div>
    <div v-for="(s, i) in sources" :key="i" class="source-card">
      <div class="source-header">
        <el-icon><Document /></el-icon>
        <span class="source-file">{{ s.file }}</span>
        <el-tag size="small" type="success" effect="plain">
          {{ (s.score * 100).toFixed(0) }}%
        </el-tag>
      </div>
      <p class="source-excerpt">{{ s.excerpt }}</p>
    </div>
  </div>
</template>

<style scoped>
.source-panel {
  padding: 12px;
}

.source-card {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.source-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.source-file {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-excerpt {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
