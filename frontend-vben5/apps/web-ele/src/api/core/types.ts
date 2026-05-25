/**
 * FlowMind - API Type Definitions
 */

/** SpringBoot unified response wrapper */
export interface Result<T = unknown> {
  code: number;
  message: string;
  data: T;
  timestamp: number;
  traceId?: string;
}

/** Conversation */
export interface Conversation {
  conversation_id: string;
  title: string;
  model: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

/** Source citation from RAG */
export interface SourceCitation {
  file: string;
  score: number;
  excerpt: string;
}

/** Chat message */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking?: boolean;
  streaming?: boolean;
  sources?: SourceCitation[];
  intent?: string;
  timestamp: number;
}

/** SSE event from streaming */
export interface SSEEvent {
  type: 'thinking' | 'token' | 'done' | 'error' | 'heartbeat';
  content?: string;
  intent?: string;
  sources?: SourceCitation[];
  conversation_id?: string;
  error?: string;
  full_text?: string;
}

/** Chat request payload */
export interface ChatRequest {
  user_id: string;
  conversation_id: string;
  message: string;
  stream: boolean;
  use_rag: boolean;
  use_tools: boolean;
  model?: string;
}

/** Agent trace step for LangGraph visualization */
export interface AgentTraceStep {
  node: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  input?: string;
  output?: string;
  duration_ms?: number;
  timestamp: number;
}