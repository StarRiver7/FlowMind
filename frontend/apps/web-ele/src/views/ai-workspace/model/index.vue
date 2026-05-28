<script setup lang="ts">import { ref, computed } from 'vue';
import { Plus, Settings, CheckCircle, Loader2, AlertCircle, Trash2, Copy, Check, ChevronRight } from 'lucide-vue-next';
interface Model {
 id: string;
 name: string;
 provider: 'deepseek' | 'openai' | 'qwen';
 model: string;
 temperature: number;
 maxTokens: number;
 contextWindow: number;
 status: 'active' | 'inactive' | 'error';
 apiKey: string;
 createdAt: Date;
}
const models = ref<Model[]>([
 { id: 'model-1', name: 'DeepSeek Chat', provider: 'deepseek', model: 'deepseek-chat', temperature: 0.7, maxTokens: 4096, contextWindow: 8192, status: 'active', apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxx', createdAt: new Date(Date.now() - 86400000) },
 { id: 'model-2', name: 'DeepSeek R1', provider: 'deepseek', model: 'deepseek-r1', temperature: 0.5, maxTokens: 8192, contextWindow: 128000, status: 'active', apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxx', createdAt: new Date(Date.now() - 86400000 * 2) },
 { id: 'model-3', name: 'GPT-4o', provider: 'openai', model: 'gpt-4o', temperature: 0.7, maxTokens: 4096, contextWindow: 128000, status: 'inactive', apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxx', createdAt: new Date(Date.now() - 86400000 * 3) },
 { id: 'model-4', name: 'GPT-4 Turbo', provider: 'openai', model: 'gpt-4-turbo', temperature: 0.9, maxTokens: 8192, contextWindow: 128000, status: 'active', apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxx', createdAt: new Date(Date.now() - 86400000 * 7) },
 { id: 'model-5', name: 'Qwen 2.5', provider: 'qwen', model: 'qwen-2.5-7b', temperature: 0.7, maxTokens: 4096, contextWindow: 32768, status: 'inactive', apiKey: '', createdAt: new Date(Date.now() - 86400000 * 14) },
]);
const selectedModelId = ref<string | null>(null);
const copiedId = ref<string | null>(null);
const currentModel = computed(() => {
 return models.value.find((m) => m.id === selectedModelId.value);
});
const activeModels = computed(() => models.value.filter((m) => m.status === 'active'));
function getProviderConfig(provider: string) {
 const configs = {
 deepseek: { name: 'DeepSeek', color: 'bg-purple-100 text-purple-600', icon: 'DeepSeek' },
 openai: { name: 'OpenAI', color: 'bg-green-100 text-green-600', icon: 'OpenAI' },
 qwen: { name: 'Qwen', color: 'bg-orange-100 text-orange-600', icon: 'Qwen' },
 };
 return configs[provider as keyof typeof configs] || configs.openai;
}
function getStatusIcon(status: string) {
 const icons = {
 active: CheckCircle,
 inactive: AlertCircle,
 error: AlertCircle,
 };
 return icons[status as keyof typeof icons] || AlertCircle;
}
function getStatusClass(status: string) {
 const classes = {
 active: 'text-green-500',
 inactive: 'text-gray-400',
 error: 'text-red-500',
 };
 return classes[status as keyof typeof classes] || 'text-gray-400';
}
function getStatusText(status: string) {
 const texts = {
 active: '已启用',
 inactive: '已停用',
 error: '配置错误',
 };
 return texts[status as keyof typeof texts] || '未知';
}
async function copyApiKey(id: string, apiKey: string) {
 await navigator.clipboard.writeText(apiKey);
 copiedId.value = id;
 setTimeout(() => {
 copiedId.value = null;
 }, 2000);
}
function selectModel(id: string) {
 selectedModelId.value = selectedModelId.value === id ? null : id;
}
</script>

<template>
  <div class="h-full flex bg-white">
    <div class="flex-1 overflow-y-auto p-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">模型管理</h1>
          <p class="text-sm text-gray-500">管理AI模型配置和参数</p>
        </div>
        <button class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2">
          <Plus class="w-4 h-4" />
          添加模型
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="model in models"
          :key="model.id"
          @click="selectModel(model.id)"
          class="bg-gray-50 rounded-xl p-5 border cursor-pointer transition-all"
          :class="[
            selectedModelId === model.id
              ? 'border-blue-300 shadow-lg'
              : 'border-gray-200 hover:border-gray-300',
          ]"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                <Settings class="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900">{{ model.name }}</h3>
                <div class="flex items-center gap-2 mt-1">
                  <span
                    class="px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="getProviderConfig(model.provider).color"
                  >
                    {{ getProviderConfig(model.provider).name }}
                  </span>
                  <span class="text-sm text-gray-500">{{ model.model }}</span>
                </div>
              </div>
            </div>
            <component :is="getStatusIcon(model.status)" class="w-5 h-5" :class="getStatusClass(model.status)" />
          </div>

          <div class="grid grid-cols-3 gap-4 mb-4">
            <div>
              <div class="text-xs text-gray-500 mb-1">Temperature</div>
              <div class="font-medium text-gray-900">{{ model.temperature }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1">Max Tokens</div>
              <div class="font-medium text-gray-900">{{ model.maxTokens.toLocaleString() }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1">Context</div>
              <div class="font-medium text-gray-900">{{ model.contextWindow.toLocaleString() }}</div>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500">{{ getStatusText(model.status) }}</span>
            <ChevronRight class="w-4 h-4 text-gray-400" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="currentModel" class="w-96 flex-shrink-0 border-l border-gray-200 bg-gray-50">
      <div class="p-4 border-b border-gray-200">
        <h3 class="font-semibold text-gray-900">模型配置</h3>
      </div>

      <div class="p-4 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">模型名称</label>
          <input
            type="text"
            :value="currentModel.name"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">提供商</label>
          <select
            :value="currentModel.provider"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          >
            <option value="deepseek">DeepSeek</option>
            <option value="openai">OpenAI</option>
            <option value="qwen">Qwen</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">模型</label>
          <input
            type="text"
            :value="currentModel.model"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">API Key</label>
          <div class="relative">
            <input
              type="password"
              :value="currentModel.apiKey"
              class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none pr-24"
            />
            <button
              @click.stop="copyApiKey(currentModel.id, currentModel.apiKey)"
              class="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 bg-gray-100 rounded text-xs hover:bg-gray-200 transition-colors flex items-center gap-1"
            >
              <component :is="copiedId === currentModel.id ? Check : Copy" class="w-3 h-3" />
              {{ copiedId === currentModel.id ? '已复制' : '复制' }}
            </button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Temperature</label>
          <div class="flex items-center gap-4">
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              :value="currentModel.temperature"
              class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <span class="w-12 text-sm text-gray-700 text-right">{{ currentModel.temperature }}</span>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
          <input
            type="number"
            :value="currentModel.maxTokens"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Context Window</label>
          <input
            type="number"
            :value="currentModel.contextWindow"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>

        <div class="pt-4 border-t border-gray-200">
          <button
            @click.stop
            class="w-full px-4 py-2 bg-red-100 text-red-600 rounded-lg font-medium hover:bg-red-200 transition-colors flex items-center justify-center gap-2"
          >
            <Trash2 class="w-4 h-4" />
            删除模型
          </button>
        </div>
      </div>
    </div>
  </div>
</template>