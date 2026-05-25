import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户信息 - SpringBoot /api/v1/user/info
 */
export async function getUserInfoApi() {
  return requestClient.get<UserInfo>('/api/v1/user/info');
}