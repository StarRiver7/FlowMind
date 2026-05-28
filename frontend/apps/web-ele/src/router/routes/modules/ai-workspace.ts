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
      icon: 'lucide:bot',
      order: 10,
      title: 'AI 工作台',
    },
    name: 'AiWorkspace',
    path: '/ai-workspace',
    redirect: '/ai-workspace/chat',
    children: [
      {
        name: 'AiChat',
        path: '/ai-workspace/chat',
        component: () => import('#/views/ai/chat/index.vue'),
        meta: {
          icon: 'lucide:message-square',
          title: 'AI 对话',
        },
      },
      {
        name: 'AiKnowledge',
        path: '/ai-workspace/knowledge',
        component: () => import('#/views/ai/knowledge/index.vue'),
        meta: {
          icon: 'lucide:database',
          title: '知识库',
        },
      },
    ],
  },
];

export default AI_ROUTES;
