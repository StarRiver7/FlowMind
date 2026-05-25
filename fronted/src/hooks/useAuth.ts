// ============================================================
// useAuth — composition hook for auth operations
// ============================================================
import { computed } from 'vue'
import { useUserStore } from '@/store/modules/user'

export function useAuth() {
  const userStore = useUserStore()

  return {
    isLoggedIn: computed(() => userStore.isLoggedIn),
    userInfo: computed(() => userStore.userInfo),
    token: computed(() => userStore.token),
    nickname: computed(() => userStore.nickname),
    hasRole: (role: string) => userStore.hasRole(role),
    hasPermission: (perm: string) => userStore.hasPermission(perm),
    login: userStore.login,
    logout: userStore.logout,
    refreshToken: userStore.refreshAccessToken,
  }
}