<script setup lang="ts">
import type { ToolbarType } from './types';

import { computed, onMounted, onUnmounted, ref } from 'vue';

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
  if (isDark.value && props.logoDark) {
    return props.logoDark;
  }
  return props.logo;
});

function getTimeBasedGreeting() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) {
    return 'Good morning, 老师~';
  } else if (hour >= 12 && hour < 14) {
    return 'Good noon, 老师~';
  } else if (hour >= 14 && hour < 18) {
    return 'Good afternoon, 老师~';
  } else if (hour >= 18 && hour < 22) {
    return 'Good evening, 老师~';
  } else {
    return 'Good night, 老师~';
  }
}

const baseSlogans = [
  'Hi 老师，欢迎回家~',
  '老师，需要 "认证" 才可以进入系统哦',
  '老师，上班快要迟到了！',
  '老师，今天也要加油鸭~',
  '小 Su 在这里等老师呢',
  '老师，咖啡已备好~',
  'Have a nice day, 老师~',
  '老师，工作要劳逸结合哦',
  '小 Su 提醒老师：该充电了~',
  '老师，一起探索 AI 吧',
  'Welcome back, 老师~',
  '老师，今天想做什么呢？',
  '小 Su 已经迫不及待啦',
  '老师，准备好了吗？',
  'Let\'s get started, 老师~',
  '老师，喝杯茶休息一下',
  '小 Su 为老师服务~',
  '老师，我们开始吧！',
  '老师，美好的一天从登录开始~',
];

const slogans = computed(() => {
  const greeting = getTimeBasedGreeting();
  return [greeting, ...baseSlogans];
});

const currentSloganIndex = ref(0);
const isAnimating = ref(false);
let intervalId: ReturnType<typeof setInterval> | null = null;

function nextSlogan() {
  if (isAnimating.value) return;
  isAnimating.value = true;
  
  setTimeout(() => {
    currentSloganIndex.value = (currentSloganIndex.value + 1) % slogans.value.length;
    isAnimating.value = false;
  }, 600);
}

onMounted(() => {
  intervalId = setInterval(nextSlogan, 5000);
});

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
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

    <slot name="logo"></slot>

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
          
          <div class="slogan-container text-1xl mt-6 font-sans text-foreground lg:text-2xl">
            <Transition name="slogan-fade" mode="out-in">
              <span :key="currentSloganIndex">
                {{ slogans[currentSloganIndex] }}
              </span>
            </Transition>
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
</template>

<style scoped>
.login-background {
  background: rgba(14, 116, 144, 0.05);
  filter: blur(80px);
}

.slogan-container {
  height: 1.5em;
  overflow: hidden;
  position: relative;
}

.slogan-fade-enter-active {
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.slogan-fade-leave-active {
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.slogan-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slogan-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
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
