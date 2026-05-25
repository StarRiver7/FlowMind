import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:bot',
      order: 10,
      title: $t('page.ai-workspace.title'),
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
          title: $t('page.ai-workspace.chat'),
        },
      },
      {
        name: 'AiKnowledge',
        path: '/ai-workspace/knowledge',
        component: () => import('#/views/ai-workspace/knowledge/index.vue'),
        meta: {
          icon: 'lucide:database',
          title: $t('page.ai-workspace.knowledge'),
        },
      },
      {
        name: 'AiPrompt',
        path: '/ai-workspace/prompt',
        component: () => import('#/views/ai-workspace/prompt/index.vue'),
        meta: {
          icon: 'lucide:file-text',
          title: $t('page.ai-workspace.prompt'),
        },
      },
      {
        name: 'AiModel',
        path: '/ai-workspace/model',
        component: () => import('#/views/ai-workspace/model/index.vue'),
        meta: {
          icon: 'lucide:cpu',
          title: $t('page.ai-workspace.model'),
        },
      },
      {
        name: 'AiHistory',
        path: '/ai-workspace/history',
        component: () => import('#/views/ai-workspace/history/index.vue'),
        meta: {
          icon: 'lucide:clock',
          title: $t('page.ai-workspace.history'),
        },
      },
    ],
  },
];

export default routes;