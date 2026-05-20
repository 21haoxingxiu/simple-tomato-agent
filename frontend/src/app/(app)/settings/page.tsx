"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Settings, Bot, Database, Sparkles, Key, RefreshCw, Check, X, Loader2, Eye, EyeOff, User, ChevronRight } from "lucide-react"
import { modelApi, ProviderInfo, ModelInfo } from "@/lib/api/models"
import { useAuthStore } from "@/store/auth"
import clsx from "clsx"

type ModelType = "chat" | "embedding" | "rerank"

interface ModelSettings {
  chat: { provider: string; model: string } | null
  embedding: { provider: string; model: string } | null
  rerank: { provider: string; model: string } | null
}

interface ApiKeys {
  [provider: string]: string
}

export default function SettingsPage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [models, setModels] = useState<Record<string, ModelInfo[]>>({})
  const [settings, setSettings] = useState<ModelSettings>({
    chat: null,
    embedding: null,
    rerank: null,
  })
  const [apiKeys, setApiKeys] = useState<ApiKeys>({})
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<"models" | "keys">("keys")

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const providerList = await modelApi.listProviders()
      setProviders(providerList)

      // Load models for each provider
      const modelMap: Record<string, ModelInfo[]> = {}
      for (const p of providerList) {
        try {
          modelMap[p.provider_class] = await modelApi.listModels(p.provider_class)
        } catch {
          modelMap[p.provider_class] = []
        }
      }
      setModels(modelMap)

      // Load current settings from localStorage
      const saved = localStorage.getItem("model-settings")
      if (saved) {
        setSettings(JSON.parse(saved))
      }

      // Load saved API keys from localStorage
      const savedKeys = localStorage.getItem("api-keys")
      if (savedKeys) {
        setApiKeys(JSON.parse(savedKeys))
      }
    } catch (e) {
      console.error("Failed to load settings:", e)
    } finally {
      setLoading(false)
    }
  }

  async function testConnection(type: ModelType) {
    const config = settings[type]
    if (!config) return

    const apiKey = apiKeys[config.provider]
    if (!apiKey) {
      setTestResult({
        success: false,
        message: `请先配置 ${config.provider} 的 API Key`,
      })
      return
    }

    setTesting(type)
    setTestResult(null)

    try {
      const result = await modelApi.testModel({
        provider: config.provider,
        model: config.model,
        model_type: type,
        api_key: apiKey,
      })
      setTestResult({
        success: result.success,
        message: result.success
          ? `连接成功 (${result.latency_ms}ms)`
          : result.error || "连接失败",
      })
    } catch (e) {
      setTestResult({
        success: false,
        message: e instanceof Error ? e.message : "测试失败",
      })
    } finally {
      setTesting(null)
    }
  }

  async function saveAllSettings() {
    setSaving(true)
    try {
      // Save model settings to localStorage
      localStorage.setItem("model-settings", JSON.stringify(settings))

      // Save API keys to localStorage
      localStorage.setItem("api-keys", JSON.stringify(apiKeys))

      // Save credentials to backend for each provider with a key
      for (const [provider, key] of Object.entries(apiKeys)) {
        if (key) {
          await modelApi.saveCredentials(provider, key)
        }
      }

      // Save default models to backend
      await modelApi.setDefaults({
        chat_model: settings.chat ? `${settings.chat.provider}:${settings.chat.model}` : null,
        embedding_model: settings.embedding ? `${settings.embedding.provider}:${settings.embedding.model}` : null,
        rerank_model: settings.rerank ? `${settings.rerank.provider}:${settings.rerank.model}` : null,
      })

      setTestResult({ success: true, message: "设置已保存" })
    } catch (e) {
      setTestResult({
        success: false,
        message: e instanceof Error ? e.message : "保存失败",
      })
    } finally {
      setSaving(false)
    }
  }

  function updateSetting(type: ModelType, provider: string, model: string) {
    setSettings((prev) => ({
      ...prev,
      [type]: { provider, model },
    }))
    setTestResult(null)
  }

  function updateApiKey(provider: string, key: string) {
    setApiKeys((prev) => ({
      ...prev,
      [provider]: key,
    }))
    setTestResult(null)
  }

  function toggleShowKey(provider: string) {
    setShowKeys((prev) => ({
      ...prev,
      [provider]: !prev[provider],
    }))
  }

  function getModelsForType(type: ModelType): { provider: string; models: ModelInfo[] }[] {
    return providers
      .filter((p) => p.supports.includes(type))
      .map((p) => ({
        provider: p.provider_class,
        models: (models[p.provider_class] || []).filter((m) => m.model_types.includes(type)),
      }))
      .filter((p) => p.models.length > 0)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Settings className="w-7 h-7" />
          设置
        </h1>
        <p className="text-gray-500 mt-1">管理您的账户和应用设置</p>
      </div>

      {/* Profile Settings Card */}
      <Link
        href="/settings/profile"
        className="block mb-6 bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-300 hover:shadow-sm transition-all"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <User size={24} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">个人资料</h3>
              <p className="text-sm text-gray-500">管理您的名称、头像等个人信息</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </div>
      </Link>

      {/* Divider */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">模型配置</h2>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab("keys")}
          className={clsx(
            "px-4 py-2 rounded-lg font-medium transition-colors",
            activeTab === "keys"
              ? "bg-indigo-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          )}
        >
          <Key className="w-4 h-4 inline mr-2" />
          API Key 配置
        </button>
        <button
          onClick={() => setActiveTab("models")}
          className={clsx(
            "px-4 py-2 rounded-lg font-medium transition-colors",
            activeTab === "models"
              ? "bg-indigo-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          )}
        >
          <Bot className="w-4 h-4 inline mr-2" />
          模型选择
        </button>
      </div>

      {testResult && (
        <div
          className={clsx(
            "mb-6 p-4 rounded-lg flex items-center gap-2",
            testResult.success
              ? "bg-green-50 text-green-700 border border-green-200"
              : "bg-red-50 text-red-700 border border-red-200"
          )}
        >
          {testResult.success ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
          {testResult.message}
        </div>
      )}

      {activeTab === "keys" && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-100 bg-gray-50">
            <h3 className="font-semibold text-gray-900">API Key 配置</h3>
            <p className="text-sm text-gray-500">为各个模型提供商配置 API Key</p>
          </div>
          <div className="divide-y divide-gray-100">
            {providers.map((provider) => (
              <div key={provider.provider_class} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-700 capitalize">{provider.name}</span>
                    <span className="text-xs text-gray-400">
                      ({provider.supports.join(", ")})
                    </span>
                  </div>
                  {apiKeys[provider.provider_class] && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      已配置
                    </span>
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showKeys[provider.provider_class] ? "text" : "password"}
                    value={apiKeys[provider.provider_class] || ""}
                    onChange={(e) => updateApiKey(provider.provider_class, e.target.value)}
                    placeholder={`输入 ${provider.name} API Key`}
                    className="w-full px-3 py-2 pr-10 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey(provider.provider_class)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showKeys[provider.provider_class] ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "models" && (
        <div className="space-y-6">
          {/* Chat Model */}
          <ModelSection
            title="对话模型"
            description="用于对话和问答的大语言模型"
            icon={<Bot className="w-5 h-5" />}
            type="chat"
            options={getModelsForType("chat")}
            value={settings.chat}
            hasApiKey={settings.chat ? !!apiKeys[settings.chat.provider] : false}
            onChange={(provider, model) => updateSetting("chat", provider, model)}
            onTest={() => testConnection("chat")}
            testing={testing === "chat"}
          />

          {/* Embedding Model */}
          <ModelSection
            title="向量模型"
            description="用于文档向量化和语义检索的嵌入模型"
            icon={<Database className="w-5 h-5" />}
            type="embedding"
            options={getModelsForType("embedding")}
            value={settings.embedding}
            hasApiKey={settings.embedding ? !!apiKeys[settings.embedding.provider] : false}
            onChange={(provider, model) => updateSetting("embedding", provider, model)}
            onTest={() => testConnection("embedding")}
            testing={testing === "embedding"}
          />

          {/* Rerank Model */}
          <ModelSection
            title="重排模型"
            description="用于对检索结果进行重新排序"
            icon={<Sparkles className="w-5 h-5" />}
            type="rerank"
            options={getModelsForType("rerank")}
            value={settings.rerank}
            hasApiKey={settings.rerank ? !!apiKeys[settings.rerank.provider] : false}
            onChange={(provider, model) => updateSetting("rerank", provider, model)}
            onTest={() => testConnection("rerank")}
            testing={testing === "rerank"}
          />
        </div>
      )}

      <div className="mt-8 flex items-center gap-4">
        <button
          onClick={saveAllSettings}
          disabled={saving}
          className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {saving && <Loader2 className="w-4 h-4 animate-spin" />}
          保存设置
        </button>
        <button
          onClick={loadData}
          className="px-4 py-2.5 text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>
    </div>
  )
}

function ModelSection({
  title,
  description,
  icon,
  type,
  options,
  value,
  hasApiKey,
  onChange,
  onTest,
  testing,
}: {
  title: string
  description: string
  icon: React.ReactNode
  type: ModelType
  options: { provider: string; models: ModelInfo[] }[]
  value: { provider: string; model: string } | null
  hasApiKey: boolean
  onChange: (provider: string, model: string) => void
  onTest: () => void
  testing: boolean
}) {
  const [expanded, setExpanded] = useState<string | null>(value?.provider || null)

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
        </div>
      </div>

      <div className="p-4">
        <div className="space-y-2">
          {options.map(({ provider, models }) => (
            <div key={provider} className="border border-gray-100 rounded-lg">
              <button
                onClick={() => setExpanded(expanded === provider ? null : provider)}
                className={clsx(
                  "w-full flex items-center justify-between px-4 py-3 text-left transition-colors",
                  expanded === provider ? "bg-gray-50" : "hover:bg-gray-50"
                )}
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-700 capitalize">{provider}</span>
                  {value?.provider === provider && (
                    <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                      {value.model}
                    </span>
                  )}
                </div>
                <span className="text-gray-400">{models.length} 个模型</span>
              </button>

              {expanded === provider && (
                <div className="border-t border-gray-100 p-2 space-y-1">
                  {models.map((model) => (
                    <button
                      key={model.name}
                      onClick={() => onChange(provider, model.name)}
                      className={clsx(
                        "w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors",
                        value?.provider === provider && value?.model === model.name
                          ? "bg-indigo-50 text-indigo-700"
                          : "hover:bg-gray-50 text-gray-600"
                      )}
                    >
                      <span className="font-mono text-sm">{model.name}</span>
                      <span className="text-xs text-gray-400">{model.max_tokens / 1000}k</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {value && (
          <div className="mt-4 flex items-center gap-2">
            <button
              onClick={onTest}
              disabled={testing || !hasApiKey}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {testing && <Loader2 className="w-4 h-4 animate-spin" />}
              测试连接
            </button>
            {!hasApiKey && (
              <span className="text-xs text-amber-600">
                请先在 "API Key 配置" 中配置 {value.provider} 的密钥
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
