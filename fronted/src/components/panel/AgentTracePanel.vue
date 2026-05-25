<!-- ============================================================ -->
<!-- AgentTracePanel — LangGraph execution trace visualization     -->
<!-- ============================================================ -->
<script setup lang="ts">
import { useChatStore } from '@/stores/chat'
import { computed } from 'vue'

const chatStore = useChatStore()
const steps = computed(() => chatStore.traceSteps)

function statusText(status: string): string {
  switch (status) {
        case 'pending': return '等待中'
        case 'running': return '执行中'
        case 'completed': return '已完成'
    case 'error': return '??'
    default: return status
  }
}
function statusIcon(status: string): string {
  switch (status) {
        case '等待中': return '\u23F8'
        case '执行中': return '\u23F3'
    case '??': return '\u274C'
    default: return '\u23F8'
  }
}
function statusColor(status: string): string {
  switch (status) {
        case '等待中': return 'var(--text-muted)'
        case '执行中': return 'var(--accent-blue)'
    case '??': return 'var(--danger)'
    default: return 'var(--text-muted)'
  }
}
</script>

<template>
  <div class="trace-panel">
    <div class="panel-header">
      <h3>Agent 执行链路</h3>
      <span class="badge">{{ steps.filter(s => s.status !== '等待中').length }}/{{ steps.length }}</span>
    </div>

    <div v-if="steps.length === 0" class="empty-state">
      <div class="empty-icon">&#x1F50D;</div>
      <p>暂无执行数据</p>
      <p class="sub">流式响应时，Agent 执行步骤将在此显示</p>
    </div>

    <div v-else class="trace-list">
      <div v-for="(step, i) in steps" :key="i" class="trace-step">
        <div class="trace-connector">
          <div class="connector-line" v-if="i < steps.length - 1"></div>
          <div class="connector-dot" :style="{ background: statusColor(step.status) }"></div>
        </div>
        <div class="trace-body">
          <div class="trace-header">
            <span class="trace-icon">{{ statusIcon(step.status) }}</span>
            <span class="trace-node">{{ step.node }}</span>
            <span class="trace-status" :style="{ color: statusColor(step.status) }">
              {{ statusText(step.status) }}
            </span>
          </div>
          <div v-if="step.output" class="trace-output">{{ step.output }}</div>
          <div v-if="step.duration_ms" class="trace-duration">{{ step.duration_ms }}ms</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trace-panel { height: 100%; }
.panel-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.panel-header h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.badge { background: var(--bg-tertiary); color: var(--text-secondary); font-size: 11px; padding: 2px 7px; border-radius: 10px; }
.empty-state { text-align: center; padding: 32px 16px; }
.empty-icon { font-size: 28px; margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); font-size: 13px; }
.empty-state .sub { font-size: 12px; margin-top: 4px; }

.trace-list { display: flex; flex-direction: column; }
.trace-step { display: flex; gap: 12px; }
.trace-connector { display: flex; flex-direction: column; align-items: center; width: 20px; flex-shrink: 0; }
.connector-line { width: 2px; flex: 1; background: var(--border-color); min-height: 20px; }
.connector-dot { width: 10px; height: 10px; border-radius: 50%; margin: 4px 0; transition: background 0.3s; }

.trace-body { flex: 1; padding-bottom: 14px; min-width: 0; }
.trace-header { display: flex; align-items: center; gap: 6px; }
.trace-icon { font-size: 12px; }
.trace-node { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.trace-status { font-size: 11px; text-transform: capitalize; }
.trace-output { font-size: 12px; color: var(--text-secondary); margin-top: 4px; padding: 4px 8px; background: var(--bg-primary); border-radius: 4px; }
.trace-duration { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
</style>