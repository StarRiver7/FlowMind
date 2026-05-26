import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { Conversation, Message, SourceCitation } from '#/api';

export interface ChatMessageUI {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  sources?: SourceCitation[];
  intent?: string;
  timestamp: number;
  streaming?: boolean;
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([]);
  const currentConversationId = ref<string | null>(null);
  const messages = ref<ChatMessageUI[]>([]);
  const isStreaming = ref(false);
  const selectedSources = ref<SourceCitation[]>([]);
  const agentTrace = ref<string[]>([]);

  const currentConversation = computed(() =>
    conversations.value.find((c) => String(c.id) === currentConversationId.value),
  );

  function setConversations(list: Conversation[]) {
    conversations.value = list;
  }

  function setCurrentConversation(id: string | null) {
    currentConversationId.value = id;
    if (!id) {
      messages.value = [];
      selectedSources.value = [];
      agentTrace.value = [];
    }
  }

  function addMessage(msg: ChatMessageUI) {
    messages.value.push(msg);
  }

  function appendToLastMessage(content: string) {
    const last = messages.value[messages.value.length - 1];
    if (last && last.role === 'assistant') {
      last.content += content;
    }
  }

  function finishStreaming() {
    isStreaming.value = false;
    const last = messages.value[messages.value.length - 1];
    if (last) last.streaming = false;
  }

  function setSources(sources: SourceCitation[]) {
    selectedSources.value = sources;
  }

  function addAgentTrace(step: string) {
    agentTrace.value.push(step);
  }

  function clearMessages() {
    messages.value = [];
    selectedSources.value = [];
    agentTrace.value = [];
  }

  function $reset() {
    conversations.value = [];
    currentConversationId.value = null;
    messages.value = [];
    isStreaming.value = false;
    selectedSources.value = [];
    agentTrace.value = [];
  }

  return {
    conversations,
    currentConversationId,
    messages,
    isStreaming,
    selectedSources,
    agentTrace,
    currentConversation,
    setConversations,
    setCurrentConversation,
    addMessage,
    appendToLastMessage,
    finishStreaming,
    setSources,
    addAgentTrace,
    clearMessages,
    $reset,
  };
});
