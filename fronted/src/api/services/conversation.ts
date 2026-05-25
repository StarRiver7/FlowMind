// ============================================================
// Conversation API Service
// ============================================================
import type { Conversation, ApiResponse, ChatMessage } from '../types'

const BASE = '/ai'

export async function listConversations(userId: string): Promise<Conversation[]> {
  const resp = await fetch(BASE + '/chat/conversations?user_id=' + encodeURIComponent(userId), {
    headers: { 'X-Api-Key': 'dev-api-key' },
  })
  if (!resp.ok) throw new Error('List conversations failed')
  const data: ApiResponse<{ conversations: Conversation[] }> = await resp.json()
  return data.data.conversations || []
}

export async function createConversation(userId: string, title?: string): Promise<string> {
  let url = BASE + '/chat/conversations?user_id=' + encodeURIComponent(userId)
  if (title) url += '&title=' + encodeURIComponent(title)
  const resp = await fetch(url, { method: 'POST', headers: { 'X-Api-Key': 'dev-api-key' } })
  if (!resp.ok) throw new Error('Create conversation failed')
  const data: ApiResponse<{ conversation_id: string }> = await resp.json()
  return data.data.conversation_id
}

export async function getMessages(conversationId: string, limit = 50): Promise<ChatMessage[]> {
  const resp = await fetch(
    BASE + '/chat/conversations/' + encodeURIComponent(conversationId) + '/messages?limit=' + limit,
    { headers: { 'X-Api-Key': 'dev-api-key' } },
  )
  if (!resp.ok) throw new Error('Get messages failed')
  const data: ApiResponse<{ messages: ChatMessage[] }> = await resp.json()
  return data.data.messages || []
}