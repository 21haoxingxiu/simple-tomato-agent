export interface Workspace {
  id: string
  name: string
  description?: string
  createdAt: string
}

export interface NavItem {
  id: string
  label: string
  icon: string
  href: string
}

export type Role = "user" | "assistant" | "system"

export interface Citation {
  chunk_id: string
  content: string
  score: number
  document_id?: string
  filename?: string
  rerank_score?: number | null
  sources?: string[]
}

export interface ChatMessage {
  role: Role
  content: string
  citations?: Citation[]
}

export interface ConversationSummary {
  id: string
  title: string
  kb_id?: string | null
  created_at: string
  updated_at: string
  message_count: number
}

export interface ServerMessage {
  id: string
  role: Role
  content: string
  citations: Citation[]
  created_at: string
}

export interface KnowledgeBase {
  id: string
  workspace_id: string
  name: string
  description: string
  doc_count: number
  chunk_count: number
  status: "ready" | "indexing" | "error"
  config: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface KnowledgeDocument {
  id: string
  kb_id: string
  filename: string
  mime_type: string
  size_bytes: number
  chunk_count: number
  status: "parsing" | "indexing" | "ready" | "error"
  error_msg?: string
  created_at: string
}

export interface RetrievedChunk {
  chunk_id: string
  content: string
  score: number
  document_id?: string
  filename?: string
  rerank_score?: number | null
  sources?: string[]
}

export interface EvalCase {
  id: string
  dataset_id?: string | null
  question: string
  expected_answer: string
  tags: string[]
  latest_run: EvalRun | null
  created_at: string
}

export interface EvalRun {
  id: string
  case_id: string
  batch_id?: string
  actual_answer: string
  similarity: number | null
  faithfulness: number | null
  relevance: number | null
  score: number | null
  passed: boolean
  latency_ms: number
  citations: Citation[]
  error_msg?: string
  created_at: string
}

export interface EvalBatchSummary {
  batch_id: string
  total: number
  passed: number
  failed: number
  avg_score: number | null
  avg_latency_ms: number
  runs: EvalRun[]
}

export interface EvalSummary {
  total_cases: number
  evaluated: number
  passed: number
  failed: number
  avg_score: number | null
}

export interface EvalDataset {
  id: string
  name: string
  description: string
  case_count: number
  created_at: string
}
