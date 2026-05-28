import { defineOverridesPreferences } from '@vben/preferences';

export const overridesPreferences = defineOverridesPreferences({
  app: {
    defaultHomePath: '/home',
    name: 'internSU',
  },
  sidebar: {
    collapsed: true,
    hidden: true,
  },
  tabbar: {
    show: false,
  },
});
