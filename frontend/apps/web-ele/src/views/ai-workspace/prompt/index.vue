<script setup lang="ts">import { ref, computed } from 'vue';
import { Plus, Search, MoreVertical, Play, Save, Copy, Check, Edit2, Trash2, ChevronRight } from 'lucide-vue-next';
interface Prompt {
 id: string;
 name: string;
 category: string;
 version: string;
 status: 'active' | 'draft' | 'archived';
 variables: string[];
 template: string;
 createdAt: Date;
 updatedAt: Date;
}
const searchQuery = ref('');
const selectedCategory = ref('all');
const selectedPromptId = ref<string | null>(null);
const copiedId = ref<string | null>(null);
const categories = ['all', '客服', '销售', '技术支持', '运营', '通用'];
const prompts = ref<Prompt[]>([
 { id: 'prompt-1', name: '企业制度查询', category: '通用', version: 'v1.2', status: 'active', variables: ['question'], template: '根据企业知识库，回答以下问题：{{question}}\n\n请使用中文详细回答，并引用相关文档来源。', createdAt: new Date(Date.now() - 86400000), updatedAt: new Date(Date.now() - 3600000) },
 { id: 'prompt-2', name: '员工信息查询', category: '通用', version: 'v1.0', status: 'active', variables: ['employee_name'], template: '查询员工{{employee_name}}的相关信息，包括部门、职位、入职日期等。', createdAt: new Date(Date.now() - 86400000 * 2), updatedAt: new Date(Date.now() - 86400000) },
 { id: 'prompt-3', name: '数据分析报告', category: '运营', version: 'v2.1', status: 'active', variables: ['metric', 'time_range'], template: '分析{{metric}}在{{time_range}}期间的趋势，并生成详细报告。', createdAt: new Date(Date.now() - 86400000 * 3), updatedAt: new Date(Date.now() - 7200000) },
 { id: 'prompt-4', name: '客户投诉处理', category: '客服', version: 'v1.1', status: 'draft', variables: ['complaint', 'customer_info'], template: '处理客户投诉：{{complaint}}\n客户信息：{{customer_info}}\n\n请生成友好的回复方案。', createdAt: new Date(Date.now() - 86400000 * 5), updatedAt: new Date(Date.now() - 86400000 * 4) },
 { id: 'prompt-5', name: '技术问题解答', category: '技术支持', version: 'v3.0', status: 'active', variables: ['problem', 'environment'], template: '解决技术问题：{{problem}}\n环境信息：{{environment}}\n\n提供详细的解决方案和步骤。', createdAt: new Date(Date.now() - 86400000 * 7), updatedAt: new Date(Date.now() - 86400000 * 2) },
]);
const filteredPrompts = computed(() => {
 let result = prompts.value;
 if (searchQuery.value) {
 const query = searchQuery.value.toLowerCase();
 result = result.filter((p) => p.name.toLowerCase().includes(query) || p.template.toLowerCase().includes(query));
 }
 if (selectedCategory.value !== 'all') {
 result = result.filter((p) => p.category === selectedCategory.value);
 }
 return result;
});
const selectedPrompt = computed(() => {
 return prompts.value.find((p) => p.id === selectedPromptId.value);
});
function getStatusClass(status: string) {
 const classes = {
 active: 'bg-green-100 text-green-600',
 draft: 'bg-yellow-100 text-yellow-600',
 archived: 'bg-gray-100 text-gray-600',
 };
 return classes[status as keyof typeof classes] || 'bg-gray-100 text-gray-600';
}
function getStatusText(status: string) {
 const texts = {
 active: '已发布',
 draft: '草稿',
 archived: '已归档',
 };
 return texts[status as keyof typeof texts] || '未知';
}
async function copyTemplate(id: string, template: string) {
 await navigator.clipboard.writeText(template);
 copiedId.value = id;
 setTimeout(() => {
 copiedId.value = null;
 }, 2000);
}
function selectPrompt(id: string) {
 selectedPromptId.value = selectedPromptId.value === id ? null : id;
}
</script>

<template>
  <div class="h-full flex bg-white">
    <div class="flex-1 overflow-y-auto p-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">Prompt 管理</h1>
          <p class="text-sm text-gray-500">管理和配置AI提示词模板</p>
        </div>
        <button class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center gap-2">
          <Plus class="w-4 h-4" />
          创建 Prompt
        </button>
      </div>

      <div class="flex items-center gap-4 mb-6">
        <div class="relative flex-1 max-w-md">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索 Prompt..."
            class="w-full pl-10 pr-4 py-2 bg-gray-50 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
          />
        </div>
        <select
          v-model="selectedCategory"
          class="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
        >
          <option v-for="cat in categories" :key="cat" :value="cat">
            {{ cat === 'all' ? '全部分类' : cat }}
          </option>
        </select>
      </div>

      <div class="space-y-3">
        <div
          v-for="prompt in filteredPrompts"
          :key="prompt.id"
          @click="selectPrompt(prompt.id)"
          class="bg-gray-50 rounded-xl p-4 border cursor-pointer transition-all"
          :class="[
            selectedPromptId === prompt.id
              ? 'border-blue-300 shadow-lg'
              : 'border-gray-200 hover:border-gray-300',
          ]"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="font-semibold text-gray-900">{{ prompt.name }}</h3>
                <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="getStatusClass(prompt.status)">
                  {{ getStatusText(prompt.status) }}
                </span>
                <span class="text-sm text-gray-500">{{ prompt.version }}</span>
              </div>
              <div class="flex items-center gap-2 mb-2">
                <span class="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">{{ prompt.category }}</span>
                <span class="text-sm text-gray-500">{{ prompt.variables.length }} 个变量</span>
              </div>
              <p class="text-sm text-gray-600 line-clamp-2">{{ prompt.template }}</p>
            </div>
            <div class="flex items-center gap-2 ml-4">
              <button
                @click.stop="copyTemplate(prompt.id, prompt.template)"
                class="w-8 h-8 rounded-lg hover:bg-gray-200 flex items-center justify-center transition-colors"
              >
                <component :is="copiedId === prompt.id ? Check : Copy" class="w-4 h-4 text-gray-500" />
              </button>
              <button @click.stop class="w-8 h-8 rounded-lg hover:bg-gray-200 flex items-center justify-center transition-colors">
                <Play class="w-4 h-4 text-gray-500" />
              </button>
              <ChevronRight class="w-4 h-4 text-gray-400" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredPrompts.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
        <Edit2 class="w-16 h-16 mb-4 opacity-50" />
        <p class="text-lg">暂无 Prompt</p>
        <button class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors">
          创建第一个 Prompt
        </button>
      </div>
    </div>

    <div v-if="selectedPrompt" class="w-[500px] flex-shrink-0 border-l border-gray-200 bg-gray-50">
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 class="font-semibold text-gray-900">Prompt 详情</h3>
        <div class="flex items-center gap-2">
          <button class="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors flex items-center gap-1">
            <Save class="w-4 h-4" />
            保存
          </button>
          <button class="px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-sm hover:bg-red-200 transition-colors flex items-center gap-1">
            <Trash2 class="w-4 h-4" />
            删除
          </button>
        </div>
      </div>

      <div class="p-4 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Prompt 名称</label>
          <input
            type="text"
            :value="selectedPrompt.name"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">分类</label>
            <select
              :value="selectedPrompt.category"
              class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            >
              <option v-for="cat in categories.filter(c => c !== 'all')" :key="cat" :value="cat">
                {{ cat }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">版本</label>
            <input
              type="text"
              :value="selectedPrompt.version"
              class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">状态</label>
          <select
            :value="selectedPrompt.status"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          >
            <option value="active">已发布</option>
            <option value="draft">草稿</option>
            <option value="archived">已归档</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">变量</label>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="variable in selectedPrompt.variables"
              :key="variable"
              class="px-3 py-1 bg-blue-100 text-blue-600 rounded-full text-sm"
            >
              {{ variable }}
            </span>
            <button class="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm hover:bg-gray-300 transition-colors">
              + 添加变量
            </button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">模板内容</label>
          <textarea
            :value="selectedPrompt.template"
            rows="8"
            class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none font-mono text-sm"
          ></textarea>
        </div>

        <div class="pt-4 border-t border-gray-200">
          <button class="w-full px-4 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors flex items-center justify-center gap-2">
            <Play class="w-4 h-4" />
            测试 Prompt
          </button>
        </div>
      </div>
    </div>
  </div>
</template>