// ============================================================
// Chat API Service — SSE streaming + non-streaming
// ============================================================
import type { ChatRequest, SSEEvent, ApiResponse } from '../types'

const BASE = '/ai'

export function createSSEConnection(
  request: ChatRequest,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void,
): AbortController {
  const controller = new AbortController()

  fetch(BASE + '/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': 'dev-api-key',
    },
    body: JSON.stringify(request),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error('HTTP ' + response.status + ': ' + response.statusText)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const dataStr = line.slice(6).trim()
          if (!dataStr || dataStr.startsWith(':')) continue

          try {
            const event: SSEEvent = JSON.parse(dataStr)
            onEvent(event)
            if (event.type === 'done' || event.type === 'error') {
              onComplete()
              return
            }
          } catch {
            // skip unparseable
          }
        }
      }
      onComplete()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err)
      }
      onComplete()
    })

  return controller
}

export async function sendChatMessage(
  request: ChatRequest & { stream: false },
): Promise<ApiResponse<{ content: string; conversation_id: string; intent: string; sources: unknown[] }>> {
  const resp = await fetch(BASE + '/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': 'dev-api-key',
    },
    body: JSON.stringify(request),
  })
  if (!resp.ok) throw new Error('Chat failed: ' + resp.status)
  return resp.json()
}