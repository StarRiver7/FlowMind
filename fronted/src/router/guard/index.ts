// ============================================================
// Guard — route guard aggregator
// ============================================================
import type { Router } from 'vue-router'
import { createPermissionGuard } from './permissionGuard'

export function setupRouterGuards(router: Router) {
  createPermissionGuard(router)
}