// ============================================================
// Router — instance with history mode
// ============================================================
import { createRouter, createWebHistory } from 'vue-router'
import { allRoutes } from './routes'
import { setupRouterGuards } from './guard'

const router = createRouter({
  history: createWebHistory(),
  routes: allRoutes,
  scrollBehavior: () => ({ top: 0 }),
})

// Setup guards (permission, auth, etc.)
setupRouterGuards(router)

export default router