<script setup lang="ts">
defineProps<{ trace: string[] }>();
</script>

<template>
  <div class="trace-panel">
    <div v-if="!trace.length" class="empty-state">
      <el-empty description="暂无执行链路" :image-size="60" />
    </div>
    <el-timeline v-else>
      <el-timeline-item
        v-for="(step, i) in trace"
        :key="i"
        :timestamp="`步骤 ${i + 1}`"
        placement="top"
      >
        <el-text size="small">{{ step }}</el-text>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<style scoped>
.trace-panel {
  padding: 12px;
}
</style>
