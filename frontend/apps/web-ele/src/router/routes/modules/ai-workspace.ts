import type { RouteRecordRaw } from 'vue-router';

const AI_ROUTES: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:home',
      order: 1,
      title: '首页',
      hideInTab: true,
    },
    name: 'Home',
    path: '/home',
    component: () => import('#/views/home/index.vue'),
  },
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: 10,
      title: '工作台',
    },
    name: 'Workspace',
    path: '/workspace',
    redirect: '/workspace/intern',
    children: [
      {
        name: 'InternChat',
        path: '/workspace/intern',
        component: () => import('#/views/ai-workspace/chat/index.vue'),
        meta: {
          icon: 'lucide:bot',
          title: '实习生',
        },
      },
      {
        name: 'Knowledge',
        path: '/workspace/knowledge',
        component: () => import('#/views/ai-workspace/knowledge/index.vue'),
        meta: {
          icon: 'lucide:database',
          title: '知识库',
        },
      },
      {
        name: 'Documents',
        path: '/workspace/documents',
        component: () => import('#/views/ai-workspace/document/index.vue'),
        meta: {
          icon: 'lucide:file-text',
          title: '文档中心',
        },
      },
    ],
  },
  {
    meta: {
      icon: 'lucide:settings-2',
      order: 20,
      title: 'AI配置',
    },
    name: 'AIConfig',
    path: '/ai-config',
    redirect: '/ai-config/prompt',
    children: [
      {
        name: 'PromptManagement',
        path: '/ai-config/prompt',
        component: () => import('#/views/ai-workspace/prompt/index.vue'),
        meta: {
          icon: 'lucide:file-code',
          title: 'Prompt管理',
        },
      },
      {
        name: 'ModelManagement',
        path: '/ai-config/model',
        component: () => import('#/views/ai-workspace/model/index.vue'),
        meta: {
          icon: 'lucide:cpu',
          title: '模型管理',
        },
      },
    ],
  },
  {
    meta: {
      icon: 'lucide:gear',
      order: 30,
      title: '系统管理',
    },
    name: 'System',
    path: '/system',
    redirect: '/system/settings',
    children: [
      {
        name: 'SystemSettings',
        path: '/system/settings',
        component: () => import('#/views/ai-workspace/settings/index.vue'),
        meta: {
          icon: 'lucide:settings',
          title: '系统设置',
        },
      },
    ],
  },
];

export default AI_ROUTES;
