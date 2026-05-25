// ============================================================
// SSE Client Utility — EventSource wrapper with reconnection
// ============================================================
export interface SSEClientOptions {
  onMessage: (data: string) => void
  onError?: (error: Event) => void
  onOpen?: () => void
}

export class SSEClient {
  private eventSource: EventSource | null = null
  private url: string
  private options: SSEClientOptions
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3

  constructor(url: string, options: SSEClientOptions) {
    this.url = url
    this.options = options
  }

  connect() {
    this.eventSource = new EventSource(this.url)

    this.eventSource.onopen = () => {
      this.reconnectAttempts = 0
      this.options.onOpen?.()
    }

    this.eventSource.onmessage = (event) => {
      this.options.onMessage(event.data)
    }

    this.eventSource.onerror = (event) => {
      this.options.onError?.(event)
      this.close()
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        setTimeout(() => this.connect(), 1000 * this.reconnectAttempts)
      }
    }
  }

  close() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }
}