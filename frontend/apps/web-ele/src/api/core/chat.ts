/**
 * AI Chat API — Python AI 服务 (SSE 流式 + REST)
 */
import { aiRequestClient, requestClient } from '#/api/request';
import type { ChatRequest, ChatResponse, PageResult, Conversation, Message } from './types';

const AI = '/ai';

/** POST /ai/chat — SSE流式聊天 */
export function chatStreamSSE(body: ChatRequest): Promise<Response> {
  const token = localStorage.getItem('flowmind_token') ?? '';
  return fetch(`${AI}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify({ ...body, stream: true }),
  });
}

/** POST /ai/chat/stream — 专用流式端点 */
export function chatStream(body: ChatRequest): Promise<Response> {
  const token = localStorage.getItem('flowmind_token') ?? '';
  return fetch(`${AI}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify(body),
  });
}

/** POST /ai/chat — 非流式聊天 */
export async function chatNonStream(body: ChatRequest) {
  return aiRequestClient.post<ChatResponse>(`${AI}/chat`, { ...body, stream: false });
}

/** GET /ai/conversations — 会话列表 */
export async function listConversations(userId: string) {
  return aiRequestClient.get<{ conversations: any[]; total: number }>(
    `${AI}/conversations?user_id=${userId}`,
  );
}

/** POST /ai/conversations — 创建会话 */
export async function createConversation(userId: string, title: string = '') {
  return aiRequestClient.post<{ conversation_id: string }>(
    `${AI}/conversations?user_id=${userId}&title=${encodeURIComponent(title)}`,
  );
}

/** GET /ai/conversations/:id/messages — 消息历史 */
export async function getMessages(conversationId: string, limit: number = 50) {
  return aiRequestClient.get<{ messages: any[]; total: number }>(
    `${AI}/conversations/${conversationId}/messages?limit=${limit}`,
  );
}

/** Java 端文档列表（分页） */
export async function listDocuments(pageNum: number = 1, pageSize: number = 10) {
  return requestClient.get<PageResult<Document>>(
    `/v1/documents?pageNum=${pageNum}&pageSize=${pageSize}`,
  );
}
