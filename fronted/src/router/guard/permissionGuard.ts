// ============================================================
// Permission Guard — vben-style route guard
// ============================================================
import type { Router, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { projectSetting } from '@/settings/projectSetting'
import { PageEnum } from '@/enums/pageEnum'

const whiteList = projectSetting.whiteList

export function createPermissionGuard(router: Router) {
  router.beforeEach(async (to: RouteLocationNormalized, _from, next) => {
    const userStore = useUserStore()

    // 1. White list — allow directly
    if (whiteList.includes(to.path)) {
      if (to.path === PageEnum.BASE_LOGIN && userStore.isLoggedIn) {
        next(PageEnum.BASE_HOME)
        return
      }
      next()
      return
    }

    // 2. Not logged in — redirect to login
    if (!userStore.isLoggedIn) {
      next({ path: PageEnum.BASE_LOGIN, query: { redirect: to.fullPath } })
      return
    }

    // 3. Session expired — try refresh
    if (userStore.sessionExpired) {
      const refreshed = await userStore.refreshAccessToken()
      if (!refreshed) {
        userStore.setSessionExpired(true)
        next({ path: PageEnum.BASE_LOGIN, query: { redirect: to.fullPath } })
        return
      }
      userStore.setSessionExpired(false)
    }

    // 4. Allowed
    next()
  })

  // After each navigation — set page title
  router.afterEach((to) => {
    document.title = (to.meta?.title as string) || projectSetting.appName
  })
}