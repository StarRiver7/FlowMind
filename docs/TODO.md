# FlowMind v2.0 完整TODO清单

> 生成日期: 2026-05-24 | 状态: 开发中

---

## Phase 1: 基础设施 (Week 1-2)

### 1.1 环境搭建
- [x] Java Service Spring Boot 3.3.5 项目骨架
- [x] Python AI Service FastAPI 项目骨架
- [x] Docker Compose 开发环境 (MySQL + Redis + Milvus)
- [ ] CI/CD Pipeline (GitHub Actions / Jenkins)
- [ ] 统一配置中心 (Nacos / Consul)

### 1.2 数据库
- [x] V1: 认证授权表 (t_user, t_role, t_permission, t_user_role, t_role_permission, t_login_log)
- [x] V2: 工具工作流表 (t_tool_definition, t_tool_call_log, t_workflow, t_workflow_node, t_workflow_execution)
- [ ] V3: AI模块表 (t_prompt_template, t_knowledge_base, t_document_permission, t_conversation, t_message)
- [ ] V4: 审计日志表 (t_audit_log, t_api_call_log)

---

## Phase 2: 核心模块 (Week 3-4)

### 2.1 认证与授权 (Java)
- [x] JWT Token 生成与校验
- [x] RBAC 权限模型 (5角色)
- [x] Refresh Token 机制 (Redis)
- [x] Token 黑名单 (登出)
- [x] 登录日志记录
- [ ] OAuth2 集成 (企业微信/钉钉)
- [ ] 多因素认证 (MFA)

### 2.2 AI对话引擎 (Python)
- [x] LLM Gateway (OpenAI + DeepSeek 双Provider)
- [x] LangGraph Router (意图分类 → 节点路由)
- [x] Prompt Manager (DB持久化 + Jinja2渲染)
- [x] Conversation Memory (Redis滑动窗口)
- [ ] 函数调用 (原生Function Calling替代文本解析)
- [ ] Token消耗监控与计费
- [ ] 流式输出性能优化 (chunk buffer)

### 2.3 RAG知识库 (Python)
- [x] Document Loader (PDF/Word/Markdown/TXT)
- [x] Text Splitter (LangChain RecursiveCharacterTextSplitter)
- [x] Embedding Engine (OpenAI / BGE-M3双模)
- [x] Milvus Retriever (向量检索)
- [ ] BM25关键词检索 (混合检索)
- [ ] Cross-encoder重排序 (BGE-Reranker)
- [ ] 查询重写 (Query Rewriting)
- [ ] 分块策略优化 (语义分块/句子级分块)

### 2.4 Tool Calling (Python)
- [x] Tool Registry (注册/发现/执行)
- [x] Calculator Tool (安全表达式求值)
- [x] Web Search Tool (DuckDuckGo)
- [ ] JSON Schema参数严格校验
- [ ] Tool执行沙箱隔离
- [ ] 自定义Tool热加载 (DB → Registry)

### 2.5 知识库隔离 (Python)
- [x] 多租户模型 (tenant_id)
- [x] 文档级ACL权限
- [ ] 租户级Milvus分区
- [ ] 跨租户知识共享 (白名单机制)

---

## Phase 3: 前端与集成 (Week 5-6)

### 3.1 前端 (Vue3)
- [ ] 登录/注册页面
- [ ] AI对话界面 (流式输出 + Markdown渲染)
- [ ] 知识库管理 (文档上传/列表/搜索)
- [ ] 工具市场 (工具注册/测试)
- [ ] Prompt管理 (可视化编辑/版本对比)
- [ ] 用户管理 (管理员)

### 3.2 集成测试
- [ ] 端到端对话流程测试
- [ ] RAG检索准确率测试
- [ ] 工具调用集成测试
- [ ] 压力测试 (并发100用户)

---

## Phase 4: 生产就绪 (Week 7-8)

### 4.1 可观测性
- [ ] OpenTelemetry全链路追踪
- [ ] Prometheus指标采集
- [ ] Grafana监控面板
- [ ] 告警规则配置

### 4.2 安全加固
- [ ] Prompt注入防护
- [ ] 输出内容安全过滤
- [ ] API速率限制
- [ ] SQL注入防护

### 4.3 部署
- [ ] K8s部署配置
- [ ] 蓝绿部署策略
- [ ] 数据库备份策略
- [ ] 灾难恢复方案

---

## 面试重点 (简历亮点)

| 模块 | 技术亮点 | 面试价值 |
|------|----------|----------|
| LangGraph Router | 状态机多Agent路由 | 体现架构设计能力 |
| RAG Pipeline | 混合检索 + 重排序 | AI应用深度 |
| Prompt Manager | DB化模板管理 | 工程化思维 |
| KB Isolation | 多租户 + ACL | 企业级安全 |
| LLM Gateway | 多Provider + 熔断 | 高可用设计 |

---

## 技术债务

| 项目 | 优先级 | 说明 |
|------|--------|------|
| Function Calling 原生支持 | P0 | 当前使用文本解析 [TOOL:...] |
| 工具执行沙箱 | P1 | eval() 仍需更安全替代 |
| BGE-M3本地部署 | P2 | 降低embedding成本 |
| 对话摘要压缩 | P2 | 长对话记忆优化 |
| Milvus Partition Key | P3 | 租户物理隔离 |
