import { defineConfig } from '@vben/vite-config';

import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      plugins: [
        ElementPlus({
          format: 'esm',
        }),
      ],
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            // 代理到 SpringBoot 后端 (SpringBoot 自带 /api 前缀)
            target: 'http://localhost:8080',
            ws: true,
          },
        },
      },
    },
  };
});