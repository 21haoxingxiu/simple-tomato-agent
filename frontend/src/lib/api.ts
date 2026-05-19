import type {
  ChatMessage,
  ConversationSummary,
  EvalBatchSummary,
  EvalCase,
  EvalDataset,
  EvalRun,
  EvalSummary,
  KnowledgeBase,
  KnowledgeDocument,
  RetrievedChunk,
  ServerMessage,
} from "@/types"

export const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8080"

// ---------- Token ----------
let _token: string | null = null

export function getToken(): string | null {
  if (_token) return _token
  if (typeof window !== "undefined") {
    _token = localStorage.getItem("auth_token")
  }
  return _token
}

export function setToken(token: string) {
  _token = token
  if (typeof window !== "undefined") localStorage.setItem("auth_token", token)
}

export function clearToken() {
  _token = null
  if (typeof window !== "undefined") localStorage.removeItem("auth_token")
}

function getWorkspaceId(): string | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem("workspace-storage")
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.state?.activeWorkspaceId ?? null
  } catch {
    return null
  }
}

export function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers["Authorization"] = `Bearer ${token}`
  const ws = getWorkspaceId()
  if (ws) headers["X-Workspace-ID"] = ws
  return headers
}

export class ApiError extends Error {
  status: number
  code?: string
  constructor(message: string, status: number, code?: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...authHeaders(),
    ...((options.headers as Record<string, string>) ?? {}),
  }

  const res = await fetch(`${GATEWAY_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    clearToken()
    throw new ApiError("未登录或登录已过期", 401, "UNAUTHORIZED")
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(
      body.detail ?? body.message ?? res.statusText,
      res.status,
      body.code
    )
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// ---------- Auth ----------
export interface UserInfo {
  id: string
  email: string
  name: string
  default_workspace_id: string
  created_at: string
}

export interface AuthResponse {
  token: string
  user: UserInfo
}

export const authApi = {
  login: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, name?: string) =>
    request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),
  me: () => request<UserInfo>("/api/me"),
  workspaces: () =>
    request<{ id: string; name: string; description: string; created_at: string }[]>(
      "/api/auth/workspaces"
    ),
}

export interface WorkspaceCreateRequest {
  name: string
  description?: string
}

export interface WorkspaceUpdateRequest {
  name?: string
  description?: string
}

export interface WorkspaceResponse {
  id: string
  name: string
  description: string
  owner_id: string
  created_at: string
}

export const workspaceApi = {
  list: () =>
    request<{ id: string; name: string; description: string; created_at: string }[]>(
      "/api/auth/workspaces"
    ),
  get: (id: string) =>
    request<WorkspaceResponse>(`/api/auth/workspaces/${id}`),
  create: (body: WorkspaceCreateRequest) =>
    request<WorkspaceResponse>("/api/auth/workspaces", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  update: (id: string, body: WorkspaceUpdateRequest) =>
    request<WorkspaceResponse>(`/api/auth/workspaces/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  remove: (id: string) =>
    request<{ ok: boolean; deleted_id: string }>(`/api/auth/workspaces/${id}`, {
      method: "DELETE",
    }),
}

// ---------- Knowledge ----------
export const knowledgeApi = {
  list: () => request<KnowledgeBase[]>("/api/knowledge/bases"),
  create: (name: string, description?: string, config?: Record<string, unknown>) =>
    request<KnowledgeBase>("/api/knowledge/bases", {
      method: "POST",
      body: JSON.stringify({ name, description, config: config ?? {} }),
    }),
  update: (id: string, body: Partial<{ name: string; description: string; config: Record<string, unknown> }>) =>
    request<KnowledgeBase>(`/api/knowledge/bases/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  remove: (id: string) =>
    request<{ ok: boolean }>(`/api/knowledge/bases/${id}`, { method: "DELETE" }),
  documents: (id: string) =>
    request<KnowledgeDocument[]>(`/api/knowledge/bases/${id}/documents`),
  removeDocument: (id: string, docId: string) =>
    request<{ ok: boolean }>(
      `/api/knowledge/bases/${id}/documents/${docId}`,
      { method: "DELETE" }
    ),
  upload: async (
    id: string,
    file: File,
    chunkSize = 800,
    chunkOverlap = 120
  ): Promise<KnowledgeDocument> => {
    const fd = new FormData()
    fd.append("file", file)
    fd.append("chunk_size", String(chunkSize))
    fd.append("chunk_overlap", String(chunkOverlap))
    const res = await fetch(`${GATEWAY_URL}/api/knowledge/bases/${id}/upload`, {
      method: "POST",
      body: fd,
      headers: authHeaders(),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new ApiError(body.detail ?? "上传失败", res.status)
    }
    return res.json()
  },
  retrieve: (
    id: string,
    query: string,
    opts: { topK?: number; recallK?: number; useRerank?: boolean | null } = {}
  ) =>
    request<RetrievedChunk[]>(`/api/knowledge/bases/${id}/retrieve`, {
      method: "POST",
      body: JSON.stringify({
        query,
        top_k: opts.topK ?? 5,
        recall_k: opts.recallK ?? 12,
        use_rerank: opts.useRerank ?? null,
      }),
    }),
}

// ---------- Chat ----------
export const chatApi = {
  conversations: () =>
    request<ConversationSummary[]>("/api/chat/conversations"),
  messages: (id: string) =>
    request<ServerMessage[]>(`/api/chat/conversations/${id}/messages`),
  removeConversation: (id: string) =>
    request<{ ok: boolean }>(`/api/chat/conversations/${id}`, { method: "DELETE" }),

  completions: (
    messages: ChatMessage[],
    opts: { conversationId?: string | null; knowledgeBaseId?: string | null } = {}
  ) =>
    request<{
      conversation_id: string
      message: ChatMessage
      citations: import("@/types").Citation[]
      usage: Record<string, unknown>
    }>("/api/chat/completions", {
      method: "POST",
      body: JSON.stringify({
        messages,
        conversation_id: opts.conversationId ?? null,
        knowledge_base_id: opts.knowledgeBaseId ?? null,
      }),
    }),

  /**
   * SSE 流式聊天。
   * onEvent 回调收到服务端事件 {event, ...}。
   */
  stream: async (
    messages: ChatMessage[],
    opts: { conversationId?: string | null; knowledgeBaseId?: string | null },
    onEvent: (evt: Record<string, unknown>) => void,
    signal?: AbortSignal
  ): Promise<void> => {
    const res = await fetch(`${GATEWAY_URL}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        messages,
        conversation_id: opts.conversationId ?? null,
        knowledge_base_id: opts.knowledgeBaseId ?? null,
        stream: true,
      }),
      signal,
    })
    if (!res.ok || !res.body) {
      const body = await res.json().catch(() => ({}))
      throw new ApiError(
        body.detail ?? body.message ?? res.statusText,
        res.status
      )
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buf = ""
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const parts = buf.split("\n\n")
      buf = parts.pop() ?? ""
      for (const block of parts) {
        const line = block.split("\n").find((l) => l.startsWith("data:"))
        if (!line) continue
        const payload = line.slice(5).trim()
        if (!payload) continue
        try {
          onEvent(JSON.parse(payload))
        } catch {
          /* ignore malformed */
        }
      }
    }
  },
}

// ---------- Eval ----------
export const evalApi = {
  summary: () => request<EvalSummary>("/api/eval/summary"),
  listDatasets: () => request<EvalDataset[]>("/api/eval/datasets"),
  createDataset: (name: string, description?: string) =>
    request<EvalDataset>("/api/eval/datasets", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  listCases: (datasetId?: string) =>
    request<EvalCase[]>(
      `/api/eval/cases${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),
  createCase: (body: {
    question: string
    expected_answer?: string
    dataset_id?: string | null
    tags?: string[]
  }) =>
    request<EvalCase>("/api/eval/cases", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateCase: (
    id: string,
    body: Partial<{
      question: string
      expected_answer: string
      dataset_id: string | null
      tags: string[]
    }>
  ) =>
    request<EvalCase>(`/api/eval/cases/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  removeCase: (id: string) =>
    request<{ ok: boolean }>(`/api/eval/cases/${id}`, { method: "DELETE" }),
  runCase: (id: string, kbId?: string | null) =>
    request<EvalRun>(`/api/eval/cases/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ kb_id: kbId ?? null }),
    }),
  runBatch: (body: { case_ids?: string[]; dataset_id?: string; kb_id?: string | null }) =>
    request<EvalBatchSummary>("/api/eval/runs/batch", {
      method: "POST",
      body: JSON.stringify(body),
    }),
}

// ---------- Voice ----------
export const voiceApi = {
  transcribe: async (blob: Blob, filename = "audio.webm"): Promise<{ text: string }> => {
    const fd = new FormData()
    fd.append("file", blob, filename)
    const res = await fetch(`${GATEWAY_URL}/api/voice/transcribe`, {
      method: "POST",
      body: fd,
      headers: authHeaders(),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new ApiError(body.detail ?? "转写失败", res.status)
    }
    return res.json()
  },
  synthesize: async (text: string, voice?: string): Promise<Blob> => {
    const res = await fetch(`${GATEWAY_URL}/api/voice/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ text, voice: voice ?? null }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new ApiError(body.detail ?? "合成失败", res.status)
    }
    return res.blob()
  },
}

export type { ChatMessage }
