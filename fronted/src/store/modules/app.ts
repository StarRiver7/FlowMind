// ============================================================
// App Store — layout state, theme, sidebar
// ============================================================
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const sidebarWidth = ref(280)
  const rightPanelVisible = ref(true)
  const rightPanelWidth = ref(320)
  const pageLoading = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  function toggleRightPanel() {
    rightPanelVisible.value = !rightPanelVisible.value
  }
  function setPageLoading(loading: boolean) {
    pageLoading.value = loading
  }

  return {
    sidebarCollapsed, sidebarWidth, rightPanelVisible, rightPanelWidth, pageLoading,
    toggleSidebar, toggleRightPanel, setPageLoading,
  }
})