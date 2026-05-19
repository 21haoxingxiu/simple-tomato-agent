import { GATEWAY_URL, authHeaders, ApiError } from "@/lib/api"

export interface ProviderInfo {
  name: string
  provider_class: string
  supports: string[]
  model_count: number
  configured: boolean
}

export interface ModelInfo {
  name: string
  max_tokens: number
  model_types: string[]
  extra_params: Record<string, unknown>
}

export interface ModelTestRequest {
  provider: string
  model: string
  model_type: "chat" | "embedding" | "rerank"
  api_key?: string
  base_url?: string
}

export interface ModelTestResponse {
  success: boolean
  latency_ms: number
  error?: string
  model_info?: Record<string, unknown>
}

export interface DefaultsRequest {
  chat_model?: string | null
  embedding_model?: string | null
  rerank_model?: string | null
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
  if (res.status === 204) return undefined as T
  return res.json()
}

export const modelApi = {
  listProviders: () =>
    request<ProviderInfo[]>("/api/models/providers"),

  listModels: (provider: string) =>
    request<ModelInfo[]>(`/api/models/providers/${provider}/models`),

  getModel: (provider: string, model: string) =>
    request<ModelInfo>(`/api/models/providers/${provider}/models/${model}`),

  testModel: (body: ModelTestRequest) =>
    request<ModelTestResponse>("/api/models/test", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  saveCredentials: (provider: string, apiKey: string, baseUrl?: string) =>
    request<{ ok: boolean }>("/api/models/credentials", {
      method: "POST",
      body: JSON.stringify({ provider, api_key: apiKey, base_url: baseUrl }),
    }),

  setDefaults: (body: DefaultsRequest) =>
    request<{ ok: boolean; defaults: DefaultsRequest }>("/api/models/defaults", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
}
