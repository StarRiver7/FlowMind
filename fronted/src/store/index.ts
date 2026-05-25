// ============================================================
// Store — Pinia instance and module re-exports
// ============================================================
import { createPinia } from 'pinia'

export const pinia = createPinia()

// Module exports
export { useUserStore } from './modules/user'
export { useAppStore } from './modules/app'
export { useChatStore } from './chat'
export { useConversationStore } from './conversation'

// Default export for app.use()
export default pinia