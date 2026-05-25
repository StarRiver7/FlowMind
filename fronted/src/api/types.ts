// ============================================================
// FlowMind — API Type Definitions
// ============================================================

/** SpringBoot unified response wrapper */
export interface Result<T = unknown> {
  code: number
  message: string
  data: T
  timestamp: number
  traceId?: string
}

/** JWT login request */
export interface LoginReq {
  username: string
  password: string
}

/** JWT login response */
export interface LoginVO {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  userInfo: UserInfo
}

export interface UserInfo {
  id: number
  username: string
  nickname: string
  email: string
  avatarUrl: string
}

/** Refresh token request */
export interface RefreshTokenReq {
  refreshToken: string
}

// ---- Chat / AI types (existing) ----

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

export interface AgentTraceStep {
  node: string
  status: 'pending' | 'running' | 'completed' | 'error'
  input?: string
  output?: string
  duration_ms?: number
  timestamp: number
}

/** User permission / role info */
export interface UserPermission {
  roles: string[]
  permissions: string[]
}