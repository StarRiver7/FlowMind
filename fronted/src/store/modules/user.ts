// ============================================================
// User Store — JWT auth, permissions, token management
// ============================================================
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, LoginReq, LoginVO, Result } from '@/api/types'
import { projectSetting } from '@/settings/projectSetting'
import { PageEnum } from '@/enums/pageEnum'

export const useUserStore = defineStore('user', () => {
  // ---- State ----
  const token = ref<string>(getPersistedToken())
  const refreshToken = ref<string>(getPersistedRefreshToken())
  const userInfo = ref<UserInfo | null>(null)
  const roles = ref<string[]>([])
  const permissions = ref<string[]>([])
  const sessionExpired = ref(false)

  // ---- Getters ----
  const isLoggedIn = computed(() => !!token.value)
  const avatar = computed(() => userInfo.value?.avatarUrl || '')
  const nickname = computed(() => userInfo.value?.nickname || userInfo.value?.username || 'User')

  // ---- Token persistence ----
  function getPersistedToken(): string | null {
    return localStorage.getItem(projectSetting.tokenKey)
  }
  function getPersistedRefreshToken(): string | null {
    return localStorage.getItem(projectSetting.refreshTokenKey)
  }
  function persistTokens(access: string, refresh: string) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem(projectSetting.tokenKey, access)
    localStorage.setItem(projectSetting.refreshTokenKey, refresh)
  }
  function clearTokens() {
    token.value = null
    refreshToken.value = null
    localStorage.removeItem(projectSetting.tokenKey)
    localStorage.removeItem(projectSetting.refreshTokenKey)
  }

  // ---- Auth actions ----
  async function login(params: LoginReq): Promise<UserInfo> {
    const resp = await fetch(projectSetting.authBaseUrl + '/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    if (!resp.ok) throw new Error('Login failed: ' + resp.status)
    const result: Result<LoginVO> = await resp.json()
    if (result.code !== 200) throw new Error(result.message || 'Login failed')

    const { accessToken, refreshToken: refToken, userInfo: info } = result.data
    persistTokens(accessToken, refToken)
    userInfo.value = info
    sessionExpired.value = false
    return info
  }

  async function refreshAccessToken(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const resp = await fetch(projectSetting.authBaseUrl + '/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: refreshToken.value }),
      })
      if (!resp.ok) return false
      const result: Result<LoginVO> = await resp.json()
      if (result.code !== 200) return false
      persistTokens(result.data.accessToken, result.data.refreshToken)
      return true
    } catch {
      return false
    }
  }

  async function logout(silent = false) {
    try {
      if (token.value && refreshToken.value) {
        await fetch(projectSetting.authBaseUrl + '/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer ' + token.value,
          },
          body: JSON.stringify({ refreshToken: refreshToken.value }),
        })
      }
    } catch {
      // silent
    }
    clearTokens()
    userInfo.value = null
    roles.value = []
    permissions.value = []
    if (!silent) {
      window.location.href = PageEnum.BASE_LOGIN
    }
  }

  function setSessionExpired(expired: boolean) {
    sessionExpired.value = expired
  }

  // ---- Permission helpers ----
  function hasRole(role: string): boolean {
    return roles.value.includes(role)
  }
  function hasPermission(perm: string): boolean {
    return permissions.value.includes(perm)
  }

  return {
    token, refreshToken, userInfo, roles, permissions, sessionExpired,
    isLoggedIn, avatar, nickname,
    login, logout, refreshAccessToken, setSessionExpired,
    hasRole, hasPermission, clearTokens,
  }
})