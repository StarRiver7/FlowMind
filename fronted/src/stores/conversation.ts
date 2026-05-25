// ============================================================
// Conversation Store — session list, switching, CRUD
// ============================================================
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation } from '@/api/types'
import { listConversations, createConversation, getMessages } from '@/api/services/conversation'

export const useConversationStore = defineStore('conversation', () => {
  // ---- State ----
  const conversations = ref<Conversation[]>([])
  const currentId = ref<string>('')
  const loading = ref(false)

  // ---- Getters ----
  const current = computed(() =>
    conversations.value.find((c) => c.conversation_id === currentId.value) || null,
  )
  const sortedConversations = computed(() =>
    [...conversations.value].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    ),
  )

  // ---- Actions ----
  async function fetchList(userId: string) {
    loading.value = true
    try {
      conversations.value = await listConversations(userId)
    } catch {
      conversations.value = []
    } finally {
      loading.value = false
    }
  }

  async function create(userId: string, title?: string): Promise<string> {
    const id = await createConversation(userId, title)
    await fetchList(userId)
    return id
  }

  async function switchTo(convId: string, chatStore?: { loadMessages: (msgs: import('@/api/types').ChatMessage[]) => void }) {
    currentId.value = convId
    if (chatStore) {
      try {
        const msgs = await getMessages(convId)
        chatStore.loadMessages(msgs as unknown[])
      } catch {
        chatStore.loadMessages([])
      }
    }
  }

  async function newAndSwitch(userId: string, chatStore: { clearMessages: () => void; loadMessages: (msgs: import('@/api/types').ChatMessage[]) => void }) {
    const id = await create(userId)
    currentId.value = id
    chatStore.clearMessages()
    return id
  }

  function selectConversation(id: string) {
    currentId.value = id
  }

  return {
    conversations, currentId, loading, current, sortedConversations,
    fetchList, create, switchTo, newAndSwitch, selectConversation,
  }
})