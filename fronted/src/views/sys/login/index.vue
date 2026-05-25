<!-- ============================================================ -->
<!-- Login Page — JWT auth against SpringBoot /api/v1/auth/login  -->
<!-- ============================================================ -->
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { PageEnum } from '@/enums/pageEnum'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const errorMsg = ref('')

const formData = reactive({
  username: 'admin',
  password: '',
})

async function handleLogin() {
  if (!formData.username || !formData.password) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    await userStore.login({
      username: formData.username,
      password: formData.password,
    })
    const redirect = (route.query.redirect as string) || PageEnum.BASE_HOME
    router.push(redirect)
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : '登录失败，请重试'
  } finally {
    loading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') handleLogin()
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">&#x1F9E0;</div>
        <h1>FlowMind AI</h1>
        <p>企业级 AI 工作台</p>
      </div>

      <div v-if="errorMsg" class="login-error">{{ errorMsg }}</div>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            @keydown="handleKeydown"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            @keydown="handleKeydown"
          />
        </div>
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>

      <div class="login-footer">
        <span>SpringBoot JWT + Vue3 Vben Architecture</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #0d1117;
}
.login-card {
  width: 400px;
  padding: 40px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-logo { font-size: 40px; margin-bottom: 8px; }
.login-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #58a6ff;
  margin: 0 0 4px;
}
.login-header p {
  font-size: 13px;
  color: #8b949e;
  margin: 0;
}
.login-error {
  padding: 10px 14px;
  background: rgba(248,81,73,0.1);
  border: 1px solid rgba(248,81,73,0.3);
  border-radius: 6px;
  color: #f85149;
  font-size: 13px;
  margin-bottom: 16px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 13px;
  color: #e6edf3;
  margin-bottom: 6px;
  font-weight: 500;
}
.form-group input {
  width: 100%;
  padding: 10px 14px;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  color: #e6edf3;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}
.form-group input:focus {
  border-color: #58a6ff;
}
.form-group input::placeholder {
  color: #484f58;
}
.login-btn {
  width: 100%;
  padding: 12px;
  background: #58a6ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  margin-top: 8px;
}
.login-btn:hover:not(:disabled) { background: #4090e0; }
.login-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 11px;
  color: #484f58;
}
</style>