import { requestClient } from '#/api/request';
import type { JavaUserInfo } from './types';

export async function getUserInfoApi() {
  return requestClient.get<JavaUserInfo>('/v1/admin/users/me');
}
