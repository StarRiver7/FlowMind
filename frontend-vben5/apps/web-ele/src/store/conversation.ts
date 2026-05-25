/**
 * Conversation Store - session list, switching, CRUD
 */
import type { Conversation, ChatMessage } from '#/api/core/types';
import { listConversations, createConversation, getMessages } from '#/api/core/conversation';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export const useConversationStore = defineStore('ai-conversation', () => {
  const conversations = ref<Conversation[]>([]);
  const currentId = ref<string>('');
  const loading = ref(false);

  const current = computed(() =>
    conversations.value.find((c) => c.conversation_id === currentId.value) || null,
  );

  const sortedConversations = computed(() =>
    [...conversations.value].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    ),
  );

  async function fetchList(userId: string) {
    loading.value = true;
    try {
      const resp = await listConversations(userId);
      conversations.value = resp.conversations || [];
    } catch {
      conversations.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function create(userId: string, title?: string): Promise<string> {
    const resp = await createConversation(userId, title);
    await fetchList(userId);
    return resp.conversation_id;
  }

  async function switchTo(
    convId: string,
    chatStore?: { loadMessages: (msgs: ChatMessage[]) => void },
  ) {
    currentId.value = convId;
    if (chatStore) {
      try {
        const resp = await getMessages(convId);
        chatStore.loadMessages(resp.messages || []);
      } catch {
        chatStore.loadMessages([]);
      }
    }
  }

  async function newAndSwitch(
    userId: string,
    chatStore: { clearMessages: () => void; loadMessages: (msgs: ChatMessage[]) => void },
  ) {
    const id = await create(userId);
    currentId.value = id;
    chatStore.clearMessages();
    return id;
  }

  function selectConversation(id: string) {
    currentId.value = id;
  }

  return {
    conversations, currentId, loading, current, sortedConversations,
    fetchList, create, switchTo, newAndSwitch, selectConversation,
  };
});