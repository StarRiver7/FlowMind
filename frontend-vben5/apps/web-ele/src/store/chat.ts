/**
 * Chat Store - streaming state, messages, agent trace
 */
import type { ChatMessage, SSEEvent, AgentTraceStep, SourceCitation } from '#/api/core/types';
import { createSSEConnection } from '#/api/core/chat';
import type { ChatRequest } from '#/api/core/types';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export const useChatStore = defineStore('ai-chat', () => {
  // ---- State ----
  const messages = ref<ChatMessage[]>([]);
  const streaming = ref(false);
  const abortController = ref<AbortController | null>(null);
  const traceSteps = ref<AgentTraceStep[]>([]);
  const currentSources = ref<SourceCitation[]>([]);
  const error = ref<string | null>(null);

  // ---- Getters ----
  const lastMessage = computed(() => messages.value[messages.value.length - 1] || null);
  const hasMessages = computed(() => messages.value.length > 0);

  // ---- Helpers ----
  function genId(): string {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg);
  }

  function appendLastToken(token: string) {
    const last = messages.value[messages.value.length - 1];
    if (last) {
      if (last.thinking) {
        last.thinking = false;
        last.content = '';
      }
      last.content += token;
    }
  }

  function setLastThinking(text: string) {
    const last = messages.value[messages.value.length - 1];
    if (last) {
      last.thinking = true;
      last.content = text;
    }
  }

  function finishLastMessage(sources: SourceCitation[], intent: string) {
    const last = messages.value[messages.value.length - 1];
    if (last) {
      last.streaming = false;
      last.sources = sources;
      last.intent = intent;
    }
    currentSources.value = sources;
  }

  function addTraceStep(step: AgentTraceStep) {
    traceSteps.value.push(step);
  }

  function updateTraceStep(nodeName: string, updates: Partial<AgentTraceStep>) {
    const step = traceSteps.value.find((s) => s.node === nodeName);
    if (step) Object.assign(step, { ...updates, timestamp: Date.now() });
  }

  function clearTrace() {
    traceSteps.value = [];
  }

  // ---- Core: send message ----
  async function sendMessage(request: ChatRequest) {
    if (streaming.value) return;

    streaming.value = true;
    error.value = null;
    clearTrace();

    // Add user message
    addMessage({
      id: genId(),
      role: 'user',
      content: request.message,
      timestamp: Date.now(),
    });

    // Add placeholder assistant message
    addMessage({
      id: genId(),
      role: 'assistant',
      content: '',
      thinking: true,
      streaming: true,
      timestamp: Date.now(),
    });

    // Initialize trace steps
    addTraceStep({ node: '意图识别', status: 'pending', timestamp: Date.now() });
    addTraceStep({ node: '知识库检索', status: 'pending', timestamp: Date.now() });
    addTraceStep({ node: 'LLM生成', status: 'pending', timestamp: Date.now() });

    const controller = createSSEConnection(
      request,
      (event: SSEEvent) => handleSSEEvent(event),
      (err: Error) => {
        error.value = err.message;
        streaming.value = false;
        finishLastMessage([], 'chat');
      },
      () => {
        streaming.value = false;
        abortController.value = null;
      },
    );
    abortController.value = controller;
  }

  function handleSSEEvent(event: SSEEvent) {
    switch (event.type) {
      case 'thinking': {
        updateTraceStep('意图识别', { status: 'running' });
        if (event.content?.includes('检索') || event.content?.includes('RAG')) {
          updateTraceStep('意图识别', { status: 'completed', output: event.content });
          updateTraceStep('知识库检索', { status: 'running' });
        } else if (event.content?.includes('LLM') || event.content?.includes('生成')) {
          updateTraceStep('知识库检索', { status: 'completed' });
          updateTraceStep('LLM生成', { status: 'running' });
        }
        setLastThinking(event.content || '');
        break;
      }

      case 'token':
        appendLastToken(event.content || '');
        break;

      case 'done':
        updateTraceStep('LLM生成', { status: 'completed', output: '回复已生成' });
        finishLastMessage(event.sources || [], event.intent || 'chat');
        break;

      case 'error':
        error.value = event.content || '未知错误';
        updateTraceStep('LLM生成', { status: 'error', output: event.content });
        finishLastMessage([], 'chat');
        break;
    }
  }

  function stopGeneration() {
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }
    streaming.value = false;
    finishLastMessage([], 'chat');
  }

  function clearMessages() {
    messages.value = [];
    currentSources.value = [];
    clearTrace();
  }

  function loadMessages(msgs: ChatMessage[]) {
    messages.value = msgs.map((m) => ({
      ...m,
      id: m.id || genId(),
      streaming: false,
      thinking: false,
    }));
  }

  return {
    messages, streaming, error, traceSteps, currentSources,
    lastMessage, hasMessages,
    sendMessage, stopGeneration, clearMessages, loadMessages,
    addTraceStep, updateTraceStep, clearTrace,
  };
});