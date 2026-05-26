# FlowMind AI Platform - Frontend

基于 [vue-vben-admin v5](https://github.com/vbenjs/vue-vben-admin) 构建的企业级 AI 工作台。

## 技术栈

- **框架**: Vue3 + TypeScript + Vite
- **UI库**: ElementPlus
- **状态管理**: Pinia
- **路由**: Vue Router
- **基础架构**: vue-vben-admin v5

## 快速启动

### 环境要求

- Node.js >= 22
- pnpm >= 9

### 安装依赖

```bash
cd frontend
pnpm install
```

### 启动开发服务器

```bash
# 使用 Node 22
set PATH=F:\_Code\Ai\FlowMind\node22\node-v22.14.0-win-x64;%PATH%
pnpm -F @vben/web-ele dev
```

访问: http://localhost:5777/

## 后端对接

### Java SpringBoot (端口 8080)

```
前端 /api/* -> localhost:8080
```

| 页面功能 | 接口 |
|---------|------|
| 登录 | POST /api/v1/auth/login |
| 注册 | POST /api/v1/auth/register |
| 用户信息 | GET /api/v1/admin/users/me |
| 文档列表 | GET /api/v1/documents |
| 文档上传 | POST /api/v1/documents/upload |
| 文档删除 | DELETE /api/v1/documents/:id |

### Python AI 服务 (端口 8000)

```
前端 /ai/* -> localhost:8000
```

| 页面功能 | 接口 |
|---------|------|
| AI 聊天 (SSE) | POST /ai/chat |
| 会话列表 | GET /ai/chat/conversations |
| 消息历史 | GET /ai/chat/conversations/:id/messages |
| RAG 搜索 | POST /ai/rag/search |
| 工具列表 | GET /ai/tools |
| Prompt 管理 | GET/POST /ai/prompts |

## 项目结构

```
apps/web-ele/src/
├── api/core/          # API 封装层
│   ├── auth.ts        # 登录/注册/登出
│   ├── chat.ts        # AI 聊天 (SSE)
│   ├── knowledge.ts   # 知识库管理
│   ├── model.ts       # 模型管理
│   ├── prompt.ts      # Prompt 管理
│   └── types.ts       # 类型定义
├── store/             # Pinia 状态管理
│   ├── auth.ts        # 登录态
│   └── chat.ts        # 聊天状态
├── router/routes/modules/
│   ├── ai-workspace.ts # AI 工作台路由
│   └── dashboard.ts    # 首页路由
├── views/ai-workspace/
│   ├── chat/          # AI 聊天工作台
│   ├── knowledge/     # 知识库管理
│   ├── prompt/        # Prompt 管理
│   ├── model/         # 模型管理
│   ├── agent/         # Agent Router
│   └── history/       # 会话历史
└── views/dashboard/   # 首页
```

## 登录

默认用户: flowmind / flowmind123 (需先启动 Java 后端并注册)