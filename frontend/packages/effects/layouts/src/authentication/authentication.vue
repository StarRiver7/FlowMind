<script setup lang="ts">
import type { ToolbarType } from './types';

import { computed } from 'vue';

import { preferences, usePreferences } from '@vben/preferences';

import { Copyright } from '../basic/copyright';
import AuthenticationFormView from './form.vue';
import SloganIcon from './icons/slogan.vue';
import Toolbar from './toolbar.vue';

interface Props {
  appName?: string;
  logo?: string;
  logoDark?: string;
  pageTitle?: string;
  pageDescription?: string;
  sloganImage?: string;
  toolbar?: boolean;
  copyright?: boolean;
  toolbarList?: ToolbarType[];
  clickLogo?: () => void;
}

const props = withDefaults(defineProps<Props>(), {
  copyright: true,
  logo: '',
  logoDark: '',
  sloganImage: '',
  toolbar: true,
  toolbarList: () => ['language', 'theme'],
  clickLogo: () => {},
});

const { authPanelCenter, authPanelLeft, authPanelRight, isDark } =
  usePreferences();

/**
 * @zh_CN 根据主题选择合适的 logo 图标
 */
const logoSrc = computed(() => {
  // 如果是暗色主题且提供了 logoDark，则使用暗色主题的 logo
  if (isDark.value && props.logoDark) {
    return props.logoDark;
  }
  // 否则使用默认的 logo
  return props.logo;
});
</script>

<template>
  <div
    :class="[isDark ? 'dark' : '']"
    class="flex min-h-full flex-1 overflow-x-hidden select-none"
  >
    <template v-if="toolbar">
      <slot name="toolbar">
        <Toolbar :toolbar-list="toolbarList" />
      </slot>
    </template>
    <!-- 左侧认证面板 -->
    <AuthenticationFormView
      v-if="authPanelLeft"
      class="min-h-full w-2/5 flex-1"
      data-side="left"
    >
      <template v-if="copyright" #copyright>
        <slot name="copyright">
          <Copyright
            v-if="preferences.copyright.enable"
            v-bind="preferences.copyright"
          />
        </slot>
      </template>
    </AuthenticationFormView>

    <slot name="logo">
      <!-- 头部 Logo 和应用名称 -->
      <div
        v-if="logoSrc || appName"
        class="absolute top-0 left-0 z-10 flex flex-1"
        @click="clickLogo"
      >
        <div
          class="mt-4 ml-4 flex flex-1 items-center text-foreground sm:top-6 sm:left-6 lg:text-foreground"
        >
          <p v-if="pageTitle" class="m-0 text-xl font-medium">
            FlowMind
          </p>
        </div>
      </div>
    </slot>

    <!-- 系统介绍 -->
    <div v-if="!authPanelCenter" class="relative hidden w-0 flex-1 lg:block">
      <div
        class="absolute inset-0 size-full bg-background-deep dark:bg-[#0a1929]"
      >
        <div class="login-background absolute top-0 left-0 size-full"></div>
        <div class="absolute inset-0 overflow-hidden">
          <div class="color-orb color-orb-green"></div>
          <div class="color-orb color-orb-blue"></div>
        </div>
        <div
          :key="authPanelLeft ? 'left' : authPanelRight ? 'right' : 'center'"
          class="mr-20 flex-col-center h-full"
          :class="{
            'enter-x': authPanelLeft,
            '-enter-x': authPanelRight,
          }"
        >
          <template v-if="sloganImage">
            <img
              :alt="appName"
              :src="sloganImage"
              class="h-64 w-2/5 animate-float"
            />
          </template>
          
          <div class="text-1xl mt-6 font-sans text-foreground lg:text-2xl">
            企业的聪明大管家
          </div>
          <div class="mt-2 dark:text-muted-foreground">
            管家界的小鲜肉，AI里的老司机
          </div>
        </div>
      </div>
    </div>

    <!-- 中心认证面板 -->
    <div v-if="authPanelCenter" class="relative flex-center w-full">
      <div class="login-background absolute top-0 left-0 size-full"></div>
      <div class="absolute inset-0 overflow-hidden">
        <div class="color-orb color-orb-green"></div>
        <div class="color-orb color-orb-blue"></div>
      </div>
      <AuthenticationFormView
        class="w-full rounded-3xl pb-20 shadow-float shadow-primary/5 md:w-2/3 md:bg-background lg:w-1/2 xl:w-[36%]"
        data-side="bottom"
      >
        <template v-if="copyright" #copyright>
          <slot name="copyright">
            <Copyright
              v-if="preferences.copyright.enable"
              v-bind="preferences.copyright"
            />
          </slot>
        </template>
      </AuthenticationFormView>
    </div>

    <!-- 右侧认证面板 -->
    <AuthenticationFormView
      v-if="authPanelRight"
      class="min-h-full w-2/5 flex-1"
      data-side="right"
    >
    </AuthenticationFormView>
  </div>
</template>

<style scoped>
.login-background {
  background: rgba(14, 116, 144, 0.05);
  filter: blur(80px);
}

.color-orb {
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}

.color-orb-green {
  background: radial-gradient(circle, rgba(34, 197, 94, 0.6) 0%, rgba(34, 197, 94, 0.2) 70%, transparent 100%);
  animation: orb-float-green 12s ease-in-out infinite;
}

.color-orb-blue {
  background: radial-gradient(circle, rgba(59, 130, 246, 0.6) 0%, rgba(59, 130, 246, 0.2) 70%, transparent 100%);
  animation: orb-float-blue 15s ease-in-out infinite;
}

@keyframes orb-float-green {
  0% {
    left: 25%;
    top: 35%;
    opacity: 0.5;
  }
  15% {
    left: 40%;
    top: 25%;
    opacity: 0.7;
  }
  30% {
    left: 55%;
    top: 35%;
    opacity: 0.5;
  }
  45% {
    left: 60%;
    top: 50%;
    opacity: 0.6;
  }
  60% {
    left: 45%;
    top: 55%;
    opacity: 0.7;
  }
  75% {
    left: 30%;
    top: 50%;
    opacity: 0.5;
  }
  90% {
    left: 20%;
    top: 40%;
    opacity: 0.6;
  }
  100% {
    left: 25%;
    top: 35%;
    opacity: 0.5;
  }
}

@keyframes orb-float-blue {
  0% {
    right: 25%;
    top: 40%;
    opacity: 0.5;
  }
  20% {
    right: 40%;
    top: 50%;
    opacity: 0.6;
  }
  40% {
    right: 50%;
    top: 35%;
    opacity: 0.7;
  }
  60% {
    right: 35%;
    top: 25%;
    opacity: 0.5;
  }
  80% {
    right: 20%;
    top: 45%;
    opacity: 0.6;
  }
  100% {
    right: 25%;
    top: 40%;
    opacity: 0.5;
  }
}

.dark {
  .login-background {
    background: rgba(6, 78, 59, 0.1);
  }
  
  .color-orb-green {
    background: radial-gradient(circle, rgba(22, 163, 74, 0.5) 0%, rgba(22, 163, 74, 0.15) 70%, transparent 100%);
  }
  
  .color-orb-blue {
    background: radial-gradient(circle, rgba(37, 99, 235, 0.5) 0%, rgba(37, 99, 235, 0.15) 70%, transparent 100%);
  }
}
</style>
