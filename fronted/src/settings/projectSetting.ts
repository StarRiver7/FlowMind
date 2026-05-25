// ============================================================
// FlowMind — Project Settings (vben-compatible)
// ============================================================
export const projectSetting = {
  // JWT token storage key
  tokenKey: 'FLOWMIND_TOKEN',
  refreshTokenKey: 'FLOWMIND_REFRESH_TOKEN',

  // SpringBoot backend
  authBaseUrl: '/api/v1/auth',
  aiBaseUrl: '/ai',

  // Token expiry buffer (seconds before expiry to refresh)
  tokenRefreshBuffer: 300,

  // Route white list (no auth required)
  whiteList: ['/login'],

  // Default home page after login
  homePath: '/dashboard/workspace',

  // App metadata
  appName: 'FlowMind AI Workspace',
  appVersion: '2.0.0',
  appLogo: '',
} as const