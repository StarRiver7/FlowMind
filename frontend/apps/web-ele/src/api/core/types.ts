/**
 * FlowMind 共享类型定义
 * 对应 Java/Python 后端的 DTO 结构
 */

/** Java LoginVO.UserInfo */
export interface JavaUserInfo {
  id: number;
  username: string;
  nickname: string;
  email: string;
  avatarUrl: string | null;
}

/** Java LoginVO 完整响应 */
export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  userInfo: JavaUserInfo;
}

/** 知识库文档 */
export interface Document {
  id: number;
  title: string;
  fileName: string;
  filePath: string;
  fileSize: number;
  fileType: string;
  description: string;
  tenantId: string;
  userId: number;
  status: number;
  chunksProcessed: number;
  createTime: string;
  updateTime: string;
}

/** 会话 */
export interface Conversation {
  id: number;
  userId: number;
  title: string;
  modelName: string;
  messageCount: number;
  lastMessageAt: string;
  createTime: string;
}

/** 消息 */
export interface Message {
  id: number;
  conversationId: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  intent: string;
  tokensUsed: number;
  sources: string;
  createTime: string;
}

/** 聊天请求（发往 Python AI） */
export interface ChatRequest {
  conversation_id: string;
  user_id: string;
  message: string;
  model?: string;
  stream: boolean;
  use_rag: boolean;
  use_tools: boolean;
}

/** Source引用 */
export interface SourceCitation {
  file: string;
  score: number;
  excerpt: string;
}

/** Python AI 聊天响应 */
export interface ChatResponse {
  content: string;
  conversation_id: string;
  intent: string;
  sources: SourceCitation[];
}

/** RAG 搜索请求 */
export interface RagSearchRequest {
  query: string;
  top_k: number;
  doc_ids?: number[];
  tenant_id?: string;
}

/** 分页结果 */
export interface PageResult<T> {
  records: T[];
  total: number;
  size: number;
  current: number;
}

/** Prompt 模板 */
export interface PromptTemplate {
  id: string;
  name: string;
  content: string;
  variables: string[];
  version: number;
  enabled: boolean;
  createTime: string;
}

/** 模型配置 */
export interface ModelConfig {
  id: string;
  name: string;
  provider: 'deepseek' | 'openai';
  modelName: string;
  temperature: number;
  maxTokens: number;
  apiKey: string;
  enabled: boolean;
}
