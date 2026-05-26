import type { RouteRecordRaw } from 'vue-router';

const DASHBOARD_ROUTES: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: 0,
      title: '工作台',
    },
    name: 'Dashboard',
    path: '/dashboard',
    redirect: '/dashboard/workspace',
    children: [
      {
        name: 'DashboardWorkspace',
        path: '/dashboard/workspace',
        component: () => import('#/views/dashboard/workspace/index.vue'),
        meta: {
          icon: 'lucide:home',
          title: '首页',
        },
      },
    ],
  },
];

export default DASHBOARD_ROUTES;
