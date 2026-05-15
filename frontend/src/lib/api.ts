const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8080"

// Token management (in-memory + localStorage)
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
  if (typeof window !== "undefined") {
    localStorage.setItem("auth_token", token)
  }
}

export function clearToken() {
  _token = null
  if (typeof window !== "undefined") {
    localStorage.removeItem("auth_token")
  }
}

// Base request helper
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${GATEWAY_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    clearToken()
    throw new Error("UNAUTHORIZED")
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }))
    throw new Error(err.message ?? "Request failed")
  }
  return res.json()
}

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    request<{ token: string; user_id: string; email: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<{ user_id: string; workspace_id: string }>("/api/me"),
}

// Chat API (proxied through gateway → Python agent)
export interface ChatMessage {
  role: "user" | "assistant" | "system"
  content: string
}

export const chatApi = {
  completions: (messages: ChatMessage[], workspaceId: string, knowledgeBaseId?: string) =>
    request<{ message: ChatMessage; usage: Record<string, string> }>("/api/chat/completions", {
      method: "POST",
      body: JSON.stringify({
        messages,
        workspace_id: workspaceId,
        knowledge_base_id: knowledgeBaseId ?? null,
      }),
    }),
}

// Knowledge base API
export const knowledgeApi = {
  list: (workspaceId: string) =>
    request<{ items: unknown[] }>(`/api/knowledge/bases`, {
      headers: { "X-Workspace-ID": workspaceId },
    }),
}
