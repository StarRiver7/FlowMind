import type { RouteRecordStringComponent } from '@vben/types';
import { requestClient } from '#/api/request';

/**
 * 后端暂无菜单接口，返回空数组，使用前端静态路由
 */
export async function getAllMenusApi() {
  return requestClient.get<RouteRecordStringComponent[]>('/menu/all');
}
