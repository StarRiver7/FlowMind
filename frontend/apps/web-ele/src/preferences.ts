import { defineOverridesPreferences } from '@vben/preferences';

export const overridesPreferences = defineOverridesPreferences({
  app: {
    defaultHomePath: '/ai-workspace/chat',
    name: import.meta.env.VITE_APP_TITLE,
  },
});
