<!-- ============================================================ -->
<!-- SourcePanel — displays RAG source citations                   -->
<!-- ============================================================ -->
<script setup lang="ts">
import { useChatStore } from '@/stores/chat'
import { computed } from 'vue'

const chatStore = useChatStore()
const sources = computed(() => chatStore.currentSources)

function scoreClass(score: number): string {
  if (score >= 0.7) return 'high'
  if (score >= 0.4) return 'mid'
  return 'low'
}
</script>

<template>
  <div class="source-panel">
    <div class="panel-header">
      <h3>引用来源</h3>
      <span class="badge">{{ sources.length }}</span>
    </div>

    <div v-if="sources.length === 0" class="empty-state">
      <div class="empty-icon">&#x1F4C4;</div>
      <p>暂无引用来源</p>
      <p class="sub">当 AI 使用知识库回答时，引用来源将在此显示</p>
    </div>

    <div v-else class="source-list">
      <div v-for="(src, i) in sources" :key="i" class="source-card">
        <div class="source-header">
          <span class="source-index">#{{ i + 1 }}</span>
          <span class="source-filename">{{ src.file }}</span>
          <span class="source-score" :class="scoreClass(src.score)">
            {{ (src.score * 100).toFixed(0) }}%
          </span>
        </div>
        <div class="source-excerpt">{{ src.excerpt }}</div>
        <div class="source-score-bar">
          <div
            class="score-fill"
            :style="{ width: (src.score * 100) + '%' }"
            :class="scoreClass(src.score)"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.source-panel { height: 100%; }
.panel-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.panel-header h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.badge { background: var(--bg-tertiary); color: var(--text-secondary); font-size: 11px; padding: 2px 7px; border-radius: 10px; }
.empty-state { text-align: center; padding: 32px 16px; }
.empty-icon { font-size: 28px; margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); font-size: 13px; }
.empty-state .sub { font-size: 12px; margin-top: 4px; }
.source-list { display: flex; flex-direction: column; gap: 10px; }
.source-card { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 10px; }
.source-header { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.source-index { font-size: 11px; color: var(--text-muted); font-weight: 600; }
.source-filename { flex: 1; font-size: 12px; color: var(--accent-blue); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.source-score { font-size: 12px; font-weight: 600; }
.source-score.high { color: var(--accent-green); }
.source-score.mid { color: var(--accent-orange); }
.source-score.low { color: var(--text-muted); }
.source-excerpt { font-size: 12px; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.source-score-bar { height: 3px; background: var(--bg-tertiary); border-radius: 2px; margin-top: 6px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }
.score-fill.high { background: var(--accent-green); }
.score-fill.mid { background: var(--accent-orange); }
.score-fill.low { background: var(--text-muted); }
</style>