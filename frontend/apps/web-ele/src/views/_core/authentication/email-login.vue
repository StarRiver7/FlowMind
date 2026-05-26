<script lang="ts" setup>
import type { VbenFormSchema } from '@vben/common-ui';
import type { Recordable } from '@vben/types';

import { computed } from 'vue';

import { AuthenticationCodeLogin, z } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { useAuthStore } from '#/store';

defineOptions({ name: 'EmailLogin' });

const authStore = useAuthStore();

const formSchema = computed((): VbenFormSchema[] => {
  return [
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: $t('authentication.emailTip'),
      },
      fieldName: 'email',
      label: $t('authentication.email'),
      rules: z
        .string()
        .min(1, { message: $t('authentication.emailTip') })
        .email({ message: $t('authentication.emailValidErrorTip') }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: $t('authentication.password'),
      },
      fieldName: 'password',
      label: $t('authentication.password'),
      rules: z
        .string()
        .min(6, { message: $t('authentication.passwordTip') }),
    },
  ];
});

async function handleSubmit(value: Recordable<any>) {
  const { email, password } = value;
  await authStore.authLogin({ email, password });
}
</script>

<template>
  <AuthenticationCodeLogin
    :form-schema="formSchema"
    :loading="authStore.loginLoading"
    :login-path="'/auth/login'"
    :show-back="true"
    :sub-title="$t('authentication.emailLoginSubtitle')"
    :title="$t('authentication.emailLogin')"
    :submit-button-text="$t('authentication.emailPasswordLogin')"
    @submit="handleSubmit"
  />
</template>