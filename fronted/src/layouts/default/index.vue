<!-- ============================================================ -->
<!-- Default Layout — vben-style: sidebar + header + router-view   -->
<!-- ============================================================ -->
<script setup lang="ts">
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { useRouter } from 'vue-router'

const appStore = useAppStore()
const userStore = useUserStore()
const router = useRouter()

function handleLogout() {
  userStore.logout(false)
}
function goHome() {
  router.push('/dashboard/workspace')
}
</script>

<template>
  <div class="vben-layout">
    <!-- Header -->
    <header class="vben-header">
      <div class="header-left">
        <button class="header-collapse-btn" @click="appStore.toggleSidebar()">
          <span v-if="appStore.sidebarCollapsed">&#9776;</span>
          <span v-else>&#10005;</span>
        </button>
        <span class="header-brand" @click="goHome">&#x1F9E0; FlowMind AI</span>
      </div>
      <div class="header-right">
        <button
          class="header-panel-btn"
          :class="{ active: appStore.rightPanelVisible }"
          @click="appStore.toggleRightPanel()"
        >
          &#9776;
        </button>
        <div class="header-user">
          <span class="user-name">{{ userStore.nickname }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>

    <div class="vben-body">
      <!-- Sidebar -->
      <aside v-show="!appStore.sidebarCollapsed" class="vben-sidebar" :style="{ width: appStore.sidebarWidth + 'px' }">
        <slot name="sidebar">
          <div class="sidebar-placeholder">Sidebar slot</div>
        </slot>
      </aside>

      <!-- Main content -->
      <main class="vben-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.vben-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0d1117;
  color: #e6edf3;
}
.vben-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-collapse-btn {
  background: none;
  border: none;
  color: #8b949e;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.header-collapse-btn:hover { background: #21262d; }
.header-brand {
  font-size: 15px;
  font-weight: 600;
  color: #58a6ff;
  cursor: pointer;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-panel-btn {
  background: none;
  border: 1px solid #30363d;
  color: #8b949e;
  font-size: 16px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 4px;
}
.header-panel-btn.active { color: #58a6ff; border-color: #58a6ff; }
.header-user { display: flex; align-items: center; gap: 10px; }
.user-name { font-size: 13px; color: #e6edf3; }
.logout-btn {
  background: none;
  border: 1px solid #30363d;
  color: #8b949e;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
}
.logout-btn:hover { color: #f85149; border-color: #f85149; }
.vben-body { display: flex; flex: 1; overflow: hidden; }
.vben-sidebar {
  flex-shrink: 0;
  background: #161b22;
  border-right: 1px solid #30363d;
  overflow-y: auto;
}
.sidebar-placeholder {
  padding: 20px;
  color: #484f58;
  text-align: center;
  font-size: 13px;
}
.vben-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>