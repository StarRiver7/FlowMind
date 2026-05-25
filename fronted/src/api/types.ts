// ============================================================
// FlowMind AI Workspace — Type Definitions
// ============================================================

export interface Conversation {
  conversation_id: string
  title: string
  model: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface SourceCitation {
  file: string
  score: number
  excerpt: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: boolean
  streaming?: boolean
  sources?: SourceCitation[]
  intent?: string
  timestamp: number
}

export interface SSEEvent {
  type: 'thinking' | 'token' | 'done' | 'error'
  content?: string
  intent?: string
  sources?: SourceCitation[]
  conversation_id?: string
  error?: string
  full_text?: string
}

export interface ChatRequest {
  user_id: string
  conversation_id: string
  message: string
  stream: boolean
  use_rag: boolean
  use_tools: boolean
  model?: string
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: number
}

export interface AgentTraceStep {
  node: string
  status: 'pending' | 'running' | 'completed' | 'error'
  input?: string
  output?: string
  duration_ms?: number
  timestamp: number
}