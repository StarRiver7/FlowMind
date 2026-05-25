// ============================================================
// AI Workspace Route Module — mounted under /dashboard/workspace
// ============================================================
import type { RouteRecordRaw } from 'vue-router'

const aiWorkspaceRoutes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/layouts/default/index.vue'),
    meta: { title: '控制台', icon: 'dashboard' },
    redirect: '/dashboard/workspace',
    children: [
      {
        path: 'workspace',
        name: 'AIWorkspace',
        component: () => import('@/views/dashboard/workspace/index.vue'),
        meta: { title: 'AI 工作台', icon: 'cpu', affix: true },
      },
    ],
  },
]

export default aiWorkspaceRoutes