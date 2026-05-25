import { baseRequestClient, requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 登录接口返回值 - 匹配SpringBoot LoginVO */
  export interface LoginResult {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    expiresIn: number;
    userInfo: {
      id: number;
      username: string;
      nickname: string;
      email: string;
      avatarUrl: string;
    };
  }

  export interface RefreshTokenResult {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    expiresIn: number;
  }
}

/**
 * 登录 - SpringBoot /api/v1/auth/login
 */
export async function loginApi(data: AuthApi.LoginParams) {
  return requestClient.post<AuthApi.LoginResult>('/api/v1/auth/login', data);
}

/**
 * 刷新accessToken - SpringBoot /api/v1/auth/refresh
 * baseRequestClient 无拦截器, 需手动解包 SpringBoot 统一响应
 */
export async function refreshTokenApi() {
  const { useAccessStore } = await import('@vben/stores');
  const accessStore = useAccessStore();
  const refreshToken = accessStore.refreshToken;

  const resp = await baseRequestClient.post('/api/v1/auth/refresh', {
    refreshToken,
  });

  // SpringBoot 统一响应: { code: 200, data: { accessToken, refreshToken, ... } }
  const body = resp.data;
  if (body?.code === 200 && body?.data) {
    return body.data as AuthApi.RefreshTokenResult;
  }
  throw new Error('Refresh token failed');
}

/**
 * 退出登录 - SpringBoot /api/v1/auth/logout
 */
export async function logoutApi() {
  const { useAccessStore } = await import('@vben/stores');
  const accessStore = useAccessStore();
  const refreshToken = accessStore.refreshToken;

  return baseRequestClient.post('/api/v1/auth/logout', {
    refreshToken,
  });
}

/**
 * 获取用户权限码 - SpringBoot暂未实现, 返回空数组
 */
export async function getAccessCodesApi() {
  return requestClient.get<string[]>('/api/v1/auth/codes');
}