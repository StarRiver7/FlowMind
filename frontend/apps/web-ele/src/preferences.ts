import { defineOverridesPreferences } from '@vben/preferences';

export const overridesPreferences = defineOverridesPreferences({
  app: {
    defaultHomePath: '/home',
    name: 'InternSU',
  },
  sidebar: {
    collapsed: true,
    hidden: true,
  },
  tabbar: {
    show: false,
  },
});
