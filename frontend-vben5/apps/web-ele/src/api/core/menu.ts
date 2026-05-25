import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户所有菜单 - 当前由前端路由模块自动生成,无需后端菜单API
 */
export async function getAllMenusApi() {
  return requestClient.get<RouteRecordStringComponent[]>('/api/v1/menu/all');
}