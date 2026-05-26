import type { RouteRecordRaw } from 'vue-router';

const AI_ROUTES: RouteRecordRaw[] = [
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
        component: () => import('#/views/ai-workspace/chat/index.vue'),
        meta: {
          icon: 'lucide:message-square',
          title: 'AI 聊天',
        },
      },
      {
        name: 'AiKnowledge',
        path: '/ai-workspace/knowledge',
        component: () => import('#/views/ai-workspace/knowledge/index.vue'),
        meta: {
          icon: 'lucide:database',
          title: '知识库管理',
        },
      },
      {
        name: 'AiPrompt',
        path: '/ai-workspace/prompt',
        component: () => import('#/views/ai-workspace/prompt/index.vue'),
        meta: {
          icon: 'lucide:file-text',
          title: 'Prompt 管理',
        },
      },
      {
        name: 'AiModel',
        path: '/ai-workspace/model',
        component: () => import('#/views/ai-workspace/model/index.vue'),
        meta: {
          icon: 'lucide:cpu',
          title: '模型管理',
        },
      },
      {
        name: 'AiAgent',
        path: '/ai-workspace/agent',
        component: () => import('#/views/ai-workspace/agent/index.vue'),
        meta: {
          icon: 'lucide:workflow',
          title: 'Agent Router',
        },
      },
      {
        name: 'AiHistory',
        path: '/ai-workspace/history',
        component: () => import('#/views/ai-workspace/history/index.vue'),
        meta: {
          icon: 'lucide:clock',
          title: '会话历史',
        },
      },
    ],
  },
];

export default AI_ROUTES;
