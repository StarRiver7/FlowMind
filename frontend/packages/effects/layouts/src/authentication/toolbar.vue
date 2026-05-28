<script setup lang="ts">
import type { ToolbarType } from './types';

import { computed } from 'vue';

import { preferences } from '@vben/preferences';

import {
  AuthenticationColorToggle,
  AuthenticationLayoutToggle,
  ThemeToggle,
} from '../widgets';

interface Props {
  toolbarList?: ToolbarType[];
}

defineOptions({
  name: 'AuthenticationToolbar',
});

const props = withDefaults(defineProps<Props>(), {
  toolbarList: () => ['color', 'layout', 'theme'],
});

const showTheme = computed(() => props.toolbarList.includes('theme'));
</script>

<template>
  <div
    :class="{
      'rounded-3xl bg-accent px-3 py-1': toolbarList.length > 1,
    }"
    class="absolute top-4 right-2 z-10 flex-center"
  >
    <ThemeToggle v-if="showTheme && preferences.widget.themeToggle" />
  </div>
</template>
