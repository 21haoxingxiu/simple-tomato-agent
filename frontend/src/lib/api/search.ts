import { GATEWAY_URL, authHeaders, ApiError } from "@/lib/api"

export interface KnowledgeBaseResult {
  id: string
  name: string
  description?: string
  doc_count: number
}

export interface ConversationResult {
  id: string
  title: string | null
  last_message: string | null
}

export interface DocumentResult {
  id: string
  kb_id: string
  filename: string
  status: string
}

export interface SearchResult {
  knowledge_bases: KnowledgeBaseResult[]
  conversations: ConversationResult[]
  documents: DocumentResult[]
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...authHeaders(),
    ...((options.headers as Record<string, string>) ?? {}),
  }

  const res = await fetch(`${GATEWAY_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
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
  return res.json()
}

export const searchApi = {
  search: async (query: string): Promise<SearchResult> => {
    return request<SearchResult>(`/api/search?q=${encodeURIComponent(query)}`)
  },
}
