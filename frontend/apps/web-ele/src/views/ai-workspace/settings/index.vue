<script setup lang="ts">import { ref } from 'vue';
import { User, Palette, Bot, Server, Settings2, Bell, Shield, Save, Check } from 'lucide-vue-next';
const activeTab = ref('profile');
const tabs = [
 { id: 'profile', label: '用户信息', icon: User },
 { id: 'theme', label: '系统主题', icon: Palette },
 { id: 'persona', label: 'AI人格', icon: Bot },
 { id: 'system', label: '系统配置', icon: Server },
];
const userInfo = ref({
 name: '张三',
 email: 'zhangsan@example.com',
 phone: '138****8888',
 department: '技术部',
 position: '高级工程师',
 avatar: '',
});
const themeMode = ref('light');
const accentColor = ref('blue');
const aiPersona = ref('intern');
const aiPersonas = [
 { id: 'intern', name: '实习生', description: '活泼可爱的实习生风格' },
 { id: 'professional', name: '专业助手', description: '正式专业的商务风格' },
 { id: 'friendly', name: '友好伙伴', description: '亲切友好的聊天风格' },
];
const sseEnabled = ref(true);
const sseTimeout = ref(30);
const maxTokens = ref(4096);
const autoSave = ref(true);
const notifications = ref({
 message: true,
 alert: true,
 marketing: false,
});
const saved = ref(false);
function saveSettings() {
 saved.value = true;
 setTimeout(() => {
 saved.value = false;
 }, 2000);
}
</script>

<template>
  <div class="h-full bg-white">
    <div class="flex">
      <div class="w-56 flex-shrink-0 border-r border-gray-200 bg-gray-50">
        <div class="p-4 border-b border-gray-200">
          <h3 class="font-semibold text-gray-900 flex items-center gap-2">
            <Settings2 class="w-5 h-5" />
            系统设置
          </h3>
        </div>
        <nav class="p-2">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all"
            :class="[
              activeTab === tab.id
                ? 'bg-blue-50 text-blue-600'
                : 'text-gray-600 hover:bg-gray-100',
            ]"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        <div v-if="activeTab === 'profile'" class="max-w-2xl">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h1 class="text-xl font-semibold text-gray-900">用户信息</h1>
              <p class="text-sm text-gray-500">管理您的个人资料</p>
            </div>
            <button
              @click="saveSettings"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Save class="w-4 h-4" />
              {{ saved ? '已保存' : '保存修改' }}
            </button>
          </div>

          <div class="space-y-6">
            <div class="flex items-center gap-6">
              <div class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                <User class="w-12 h-12 text-white" />
              </div>
              <button class="px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
                更换头像
              </button>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">姓名</label>
                <input
                  v-model="userInfo.name"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">职位</label>
                <input
                  v-model="userInfo.position"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
                <input
                  v-model="userInfo.email"
                  type="email"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">电话</label>
                <input
                  v-model="userInfo.phone"
                  type="tel"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">部门</label>
                <input
                  v-model="userInfo.department"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'theme'" class="max-w-2xl">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h1 class="text-xl font-semibold text-gray-900">系统主题</h1>
              <p class="text-sm text-gray-500">自定义界面外观</p>
            </div>
            <button
              @click="saveSettings"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Save class="w-4 h-4" />
              {{ saved ? '已保存' : '保存修改' }}
            </button>
          </div>

          <div class="space-y-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-3">主题模式</label>
              <div class="grid grid-cols-3 gap-4">
                <button
                  @click="themeMode = 'light'"
                  class="p-4 rounded-xl border-2 transition-all"
                  :class="[
                    themeMode === 'light'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300',
                  ]"
                >
                  <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
                    <Palette class="w-6 h-6 text-gray-600" />
                  </div>
                  <div class="font-medium text-gray-900">浅色模式</div>
                </button>
                <button
                  @click="themeMode = 'dark'"
                  class="p-4 rounded-xl border-2 transition-all"
                  :class="[
                    themeMode === 'dark'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300',
                  ]"
                >
                  <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-800 flex items-center justify-center">
                    <Palette class="w-6 h-6 text-gray-300" />
                  </div>
                  <div class="font-medium text-gray-900">深色模式</div>
                </button>
                <button
                  @click="themeMode = 'auto'"
                  class="p-4 rounded-xl border-2 transition-all"
                  :class="[
                    themeMode === 'auto'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300',
                  ]"
                >
                  <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-r from-gray-100 to-gray-800 flex items-center justify-center">
                    <Palette class="w-6 h-6 text-gray-600" />
                  </div>
                  <div class="font-medium text-gray-900">跟随系统</div>
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-3">主题色</label>
              <div class="flex gap-4">
                <button
                  v-for="color in ['blue', 'purple', 'green', 'orange', 'red']"
                  :key="color"
                  @click="accentColor = color"
                  class="w-12 h-12 rounded-full transition-all ring-2"
                  :class="[
                    `bg-${color}-500`,
                    accentColor === color ? 'ring-offset-2 ring-blue-500 scale-110' : '',
                  ]"
                ></button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'persona'" class="max-w-2xl">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h1 class="text-xl font-semibold text-gray-900">AI人格设置</h1>
              <p class="text-sm text-gray-500">选择AI助手的性格风格</p>
            </div>
            <button
              @click="saveSettings"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Save class="w-4 h-4" />
              {{ saved ? '已保存' : '保存修改' }}
            </button>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <button
              v-for="persona in aiPersonas"
              :key="persona.id"
              @click="aiPersona = persona.id"
              class="p-4 rounded-xl border-2 text-left transition-all"
              :class="[
                aiPersona === persona.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300',
              ]"
            >
              <div class="w-12 h-12 mb-3 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                <Bot class="w-6 h-6 text-white" />
              </div>
              <div class="font-medium text-gray-900 mb-1">{{ persona.name }}</div>
              <div class="text-sm text-gray-500">{{ persona.description }}</div>
            </button>
          </div>
        </div>

        <div v-if="activeTab === 'system'" class="max-w-2xl">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h1 class="text-xl font-semibold text-gray-900">系统配置</h1>
              <p class="text-sm text-gray-500">管理系统参数和通知设置</p>
            </div>
            <button
              @click="saveSettings"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Save class="w-4 h-4" />
              {{ saved ? '已保存' : '保存修改' }}
            </button>
          </div>

          <div class="space-y-6">
            <div class="bg-gray-50 rounded-xl p-5">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Server class="w-5 h-5 text-blue-500" />
                SSE 设置
              </h3>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-900">启用 SSE</div>
                    <div class="text-sm text-gray-500">实时流式响应</div>
                  </div>
                  <button
                    @click="sseEnabled = !sseEnabled"
                    class="relative w-12 h-6 rounded-full transition-colors"
                    :class="[sseEnabled ? 'bg-blue-500' : 'bg-gray-300']"
                  >
                    <span
                      class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                      :class="[sseEnabled ? 'translate-x-7' : 'translate-x-1']"
                    ></span>
                  </button>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">超时时间 (秒)</label>
                  <input
                    v-model.number="sseTimeout"
                    type="number"
                    min="10"
                    max="120"
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

            <div class="bg-gray-50 rounded-xl p-5">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Shield class="w-5 h-5 text-blue-500" />
                AI 设置
              </h3>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">最大 Token 数</label>
                  <input
                    v-model.number="maxTokens"
                    type="number"
                    min="1024"
                    max="16384"
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-900">自动保存会话</div>
                    <div class="text-sm text-gray-500">自动保存聊天记录</div>
                  </div>
                  <button
                    @click="autoSave = !autoSave"
                    class="relative w-12 h-6 rounded-full transition-colors"
                    :class="[autoSave ? 'bg-blue-500' : 'bg-gray-300']"
                  >
                    <span
                      class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                      :class="[autoSave ? 'translate-x-7' : 'translate-x-1']"
                    ></span>
                  </button>
                </div>
              </div>
            </div>

            <div class="bg-gray-50 rounded-xl p-5">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Bell class="w-5 h-5 text-blue-500" />
                通知设置
              </h3>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-900">消息通知</div>
                    <div class="text-sm text-gray-500">接收新消息通知</div>
                  </div>
                  <button
                    @click="notifications.message = !notifications.message"
                    class="relative w-12 h-6 rounded-full transition-colors"
                    :class="[notifications.message ? 'bg-blue-500' : 'bg-gray-300']"
                  >
                    <span
                      class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                      :class="[notifications.message ? 'translate-x-7' : 'translate-x-1']"
                    ></span>
                  </button>
                </div>
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-900">系统告警</div>
                    <div class="text-sm text-gray-500">接收系统异常通知</div>
                  </div>
                  <button
                    @click="notifications.alert = !notifications.alert"
                    class="relative w-12 h-6 rounded-full transition-colors"
                    :class="[notifications.alert ? 'bg-blue-500' : 'bg-gray-300']"
                  >
                    <span
                      class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                      :class="[notifications.alert ? 'translate-x-7' : 'translate-x-1']"
                    ></span>
                  </button>
                </div>
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-900">营销通知</div>
                    <div class="text-sm text-gray-500">接收产品更新和活动通知</div>
                  </div>
                  <button
                    @click="notifications.marketing = !notifications.marketing"
                    class="relative w-12 h-6 rounded-full transition-colors"
                    :class="[notifications.marketing ? 'bg-blue-500' : 'bg-gray-300']"
                  >
                    <span
                      class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                      :class="[notifications.marketing ? 'translate-x-7' : 'translate-x-1']"
                    ></span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>