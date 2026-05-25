<!-- ============================================================ -->
<!-- AI Workspace — route view mounted at /dashboard/workspace     -->
<!-- Three-column: sidebar | chat | panel (inside layout)          -->
<!-- ============================================================ -->
<script setup lang="ts">
import ConversationSidebar from '@/components/sidebar/ConversationSidebar.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import SourcePanel from '@/components/panel/SourcePanel.vue'
import AgentTracePanel from '@/components/panel/AgentTracePanel.vue'
import { useAppStore } from '@/store/modules/app'
import { ref, computed } from 'vue'

const appStore = useAppStore()
const rightPanelTab = ref<'sources' | 'trace'>('sources')
</script>

<template>
  <div class="ai-workspace">
    <!-- Left: Conversation Sidebar -->
    <aside v-show="!appStore.sidebarCollapsed" class="workspace-sidebar" :style="{ width: appStore.sidebarWidth + 'px' }">
      <ConversationSidebar />
    </aside>

    <!-- Center: Chat Area -->
    <main class="workspace-main">
      <ChatPanel />
    </main>

    <!-- Right: Sources / Trace Panel -->
    <aside v-show="appStore.rightPanelVisible" class="workspace-panel" :style="{ width: appStore.rightPanelWidth + 'px' }">
      <div class="panel-tabs">
        <button
          :class="['panel-tab', { active: rightPanelTab === 'sources' }]"
          @click="rightPanelTab = 'sources'"
        >
          引用来源
        </button>
        <button
          :class="['panel-tab', { active: rightPanelTab === 'trace' }]"
          @click="rightPanelTab = 'trace'"
        >
          执行链路
        </button>
      </div>
      <div class="panel-content">
        <SourcePanel v-if="rightPanelTab === 'sources'" />
        <AgentTracePanel v-if="rightPanelTab === 'trace'" />
      </div>
    </aside>
  </div>
</template>

<style scoped>
.ai-workspace {
  display: flex;
  height: 100%;
  background: #0d1117;
}
.workspace-sidebar {
  flex-shrink: 0;
  background: #161b22;
  border-right: 1px solid #30363d;
  overflow-y: auto;
}
.workspace-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.workspace-panel {
  flex-shrink: 0;
  background: #161b22;
  border-left: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.panel-tabs {
  display: flex;
  border-bottom: 1px solid #30363d;
  padding: 0 8px;
  flex-shrink: 0;
}
.panel-tab {
  flex: 1;
  background: none;
  border: none;
  color: #8b949e;
  padding: 12px 8px;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}
.panel-tab:hover { color: #e6edf3; }
.panel-tab.active {
  color: #58a6ff;
  border-bottom-color: #58a6ff;
}
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
</style>