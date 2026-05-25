// ============================================================
// Routes — aggregator for all route modules
// ============================================================
import type { RouteRecordRaw } from 'vue-router'
import { PageEnum } from '@/enums/pageEnum'
import aiWorkspaceRoutes from './modules/aiWorkspace'

// Public routes (no layout wrapper)
export const publicRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/sys/login/index.vue'),
    meta: { title: '登录' },
  },
]

// Business routes (wrapped in layout)
export const businessRoutes: RouteRecordRaw[] = [
  ...aiWorkspaceRoutes,
]

// Catch-all
export const errorRoutes: RouteRecordRaw[] = [
  {
    path: '/:pathMatch(.*)*',
    redirect: PageEnum.BASE_HOME,
  },
]

// All routes in order
export const allRoutes: RouteRecordRaw[] = [
  ...publicRoutes,
  ...businessRoutes,
  ...errorRoutes,
]