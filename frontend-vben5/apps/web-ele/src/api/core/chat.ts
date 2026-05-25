/**
 * Chat API Service - SSE streaming + RAG retrieval
 */
import type { ChatRequest, SSEEvent, SourceCitation } from './types';

import { requestClient } from '#/api/request';
import { useAccessStore } from '@vben/stores';

const AI_BASE = '/ai';

/**
 * Create SSE connection for streaming chat
 */
export function createSSEConnection(
  request: ChatRequest,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void,
): AbortController {
  const controller = new AbortController();
  const accessStore = useAccessStore();

  fetch(AI_BASE + '/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': accessStore.accessToken ? `Bearer ${accessStore.accessToken}` : '',
    },
    body: JSON.stringify({ ...request, stream: true }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const dataStr = line.slice(6).trim();
          if (!dataStr || dataStr.startsWith(':')) continue;

          try {
            const event: SSEEvent = JSON.parse(dataStr);
            onEvent(event);
            if (event.type === 'done' || event.type === 'error') {
              onComplete();
              return;
            }
          } catch {
            // skip unparseable lines
          }
        }
      }
      onComplete();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err);
      }
      onComplete();
    });

  return controller;
}

/**
 * Non-streaming chat (fallback)
 */
export async function sendChatMessage(request: ChatRequest & { stream?: false }) {
  return requestClient.post<{
    content: string;
    conversation_id: string;
    intent: string;
    sources: SourceCitation[];
  }>(AI_BASE + '/chat', { ...request, stream: false });
}