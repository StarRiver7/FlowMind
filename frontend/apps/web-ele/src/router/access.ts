import type { ComponentRecordType, GenerateMenuAndRoutesOptions } from '@vben/types';
import { generateAccessible } from '@vben/access';
import { preferences } from '@vben/preferences';
import { ElMessage } from 'element-plus';
import { getAllMenusApi } from '#/api';
import { BasicLayout, IFrameView } from '#/layouts';
import { $t } from '#/locales';

const forbiddenComponent = () => import('#/views/_core/fallback/forbidden.vue');

async function generateAccess(options: GenerateMenuAndRoutesOptions) {
  const pageMap: ComponentRecordType = import.meta.glob('../views/**/*.vue');
  const layoutMap: ComponentRecordType = { BasicLayout, IFrameView };

  return await generateAccessible(preferences.app.accessMode, {
    ...options,
    fetchMenuListAsync: async () => {
      ElMessage({ duration: 1500, message: `${$t('common.loadingMenu')}...` });
      try {
        return await getAllMenusApi();
      } catch {
        // 后端无菜单接口，使用前端静态路由
        return [];
      }
    },
    forbiddenComponent,
    layoutMap,
    pageMap,
  });
}

export { generateAccess };