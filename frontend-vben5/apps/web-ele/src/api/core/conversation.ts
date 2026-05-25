/**
 * Conversation API Service
 */
import type { Conversation, ChatMessage } from './types';

import { requestClient } from '#/api/request';

const AI_BASE = '/ai';

/** List conversations for a user */
export async function listConversations(userId: string) {
  return requestClient.get<{ conversations: Conversation[]; total: number }>(
    `${AI_BASE}/chat/conversations?user_id=${encodeURIComponent(userId)}`,
  );
}

/** Create a new conversation */
export async function createConversation(userId: string, title?: string) {
  let url = `${AI_BASE}/chat/conversations?user_id=${encodeURIComponent(userId)}`;
  if (title) url += `&title=${encodeURIComponent(title)}`;
  return requestClient.post<{ conversation_id: string }>(url);
}

/** Get messages for a conversation */
export async function getMessages(conversationId: string, limit = 50) {
  return requestClient.get<{ messages: ChatMessage[]; total: number }>(
    `${AI_BASE}/chat/conversations/${encodeURIComponent(conversationId)}/messages?limit=${limit}`,
  );
}