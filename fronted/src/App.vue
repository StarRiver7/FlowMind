<!-- ============================================================ -->
<!-- FlowMind AI Workspace — Root Layout                          -->
<!-- Three-column: Sidebar | Chat | Source Panel                  -->
<!-- ============================================================ -->
<script setup lang="ts">
import ConversationSidebar from './components/sidebar/ConversationSidebar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import SourcePanel from './components/panel/SourcePanel.vue'
import AgentTracePanel from './components/panel/AgentTracePanel.vue'
import { ref } from 'vue'

const rightPanelTab = ref<'sources' | 'trace'>('sources')
</script>

<template>
  <div class="workspace-layout">
    <!-- Left: Conversation Sidebar -->
    <aside class="workspace-sidebar">
      <ConversationSidebar />
    </aside>

    <!-- Center: Chat Area -->
    <main class="workspace-main">
      <ChatPanel />
    </main>

    <!-- Right: Sources / Trace Panel -->
    <aside class="workspace-panel">
      <div class="panel-tabs">
        <button
          :class="['panel-tab', { active: rightPanelTab === 'sources' }]"
          @click="rightPanelTab = 'sources'"
        >
          Sources
        </button>
        <button
          :class="['panel-tab', { active: rightPanelTab === 'trace' }]"
          @click="rightPanelTab = 'trace'"
        >
          Trace
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
.workspace-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: var(--bg-primary);
}

.workspace-sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.workspace-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.workspace-panel {
  width: 320px;
  min-width: 320px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.panel-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  padding: 0 8px;
}
.panel-tab {
  flex: 1;
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 12px 8px;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}
.panel-tab:hover {
  color: var(--text-primary);
}
.panel-tab.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
</style>