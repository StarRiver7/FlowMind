<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

const quickActions = [
  {
    icon: '&#128214;',
    label: '查询企业制度',
    desc: '搜索公司规章制度与政策文件',
    prompt: '帮我查询公司请假制度',
  },
  {
    icon: '&#128202;',
    label: '查询企业数据',
    desc: '用SQL分析数据库中的数据',
    prompt: '统计本月各部门在职员工人数',
  },
  {
    icon: '&#128228;',
    label: '上传知识库',
    desc: '将文档加入企业知识库',
    route: '/ai-workspace/knowledge',
  },
  {
    icon: '&#129302;',
    label: 'AI 问答',
    desc: '问任何企业相关的问题',
    prompt: '员工手册中关于年假的规定是什么？',
  },
  {
    icon: '&#128270;',
    label: 'SQL 数据分析',
    desc: '自然语言生成SQL查询',
    prompt: '查询最近30天的销售趋势',
  },
  {
    icon: '&#128221;',
    label: '文档摘要',
    desc: '快速总结文档要点',
    prompt: '帮我总结最近上传的项目报告',
  },
];

function startChat(prompt?: string) {
  if (prompt) {
    router.push({ path: '/ai-workspace/chat', query: { prompt } });
  } else {
    router.push('/ai-workspace/chat');
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh] px-6">
    <!-- Logo & Brand -->
    <div class="mb-8 text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-500 mb-5 shadow-lg shadow-blue-200">
        <span class="text-2xl font-bold text-white">SU</span>
      </div>
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">
        老师，今天想让我帮您做什么？
      </h1>
      <p class="mt-2.5 text-sm text-gray-500 max-w-md leading-relaxed">
        我是 internSU，您的 AI 实习生。<br/>
        我可以帮您查询企业制度、分析业务数据、管理知识库。
      </p>
    </div>

    <!-- Big Input -->
    <div class="w-full max-w-2xl mb-10">
      <div
        class="relative rounded-2xl border border-gray-200 bg-white shadow-sm
               hover:border-blue-200 focus-within:border-blue-300 focus-within:shadow-[0_0_0_3px_rgba(59,130,246,0.08)]
               transition-all duration-200 cursor-text"
        @click="startChat()"
      >
        <div class="flex items-center px-5 py-4 gap-3">
          <svg class="shrink-0 text-gray-400" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span class="text-[15px] text-gray-400">老师，今天想让我帮您做什么？</span>
          <div class="ml-auto shrink-0 flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500 text-white">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="w-full max-w-2xl">
      <div class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
        快捷能力
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        <button
          v-for="action in quickActions"
          :key="action.label"
          class="group flex items-start gap-3 rounded-xl border border-gray-100 bg-white px-4 py-3.5 text-left
                 hover:border-blue-200 hover:bg-blue-50/20 hover:shadow-sm transition-all duration-150"
          @click="action.route ? router.push(action.route) : startChat(action.prompt)"
        >
          <span class="text-xl shrink-0 leading-none mt-0.5" v-html="action.icon" />
          <div>
            <div class="text-[13px] font-medium text-gray-700 group-hover:text-blue-600 transition-colors">
              {{ action.label }}
            </div>
            <div class="mt-0.5 text-[11px] text-gray-400 leading-snug">
              {{ action.desc }}
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
