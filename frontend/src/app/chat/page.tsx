"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Plus, Sparkles, AlertCircle } from "lucide-react"
import clsx from "clsx"
import { chatApi, type ChatMessage } from "@/lib/api"
import { useAuthStore } from "@/store/auth"
import { useWorkspaceStore } from "@/store/workspace"

const SUGGESTED_PROMPTS = [
  "介绍一下 LangChain 的基本概念",
  "用 Go 写一个 JWT 鉴权中间件",
  "什么是 RAG？怎么实现？",
  "解释一下 LangGraph 的工作原理",
]

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { ensureToken } = useAuthStore()
  const { activeWorkspaceId } = useWorkspaceStore()

  useEffect(() => {
    ensureToken().catch(console.error)
  }, [ensureToken])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function handleSend(text?: string) {
    const content = text ?? input.trim()
    if (!content || loading) return

    const userMsg: ChatMessage = { role: "user", content }
    const nextMessages = [...messages, userMsg]
    setMessages(nextMessages)
    setInput("")
    setError(null)
    setLoading(true)

    try {
      await ensureToken()
      const res = await chatApi.completions(nextMessages, activeWorkspaceId)
      setMessages((prev) => [...prev, res.message])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "请求失败"
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full">
      {/* Conversation List */}
      <aside className="w-64 bg-white border-r border-gray-200 flex-col hidden md:flex">
        <div className="p-4 border-b border-gray-100">
          <button
            onClick={() => setMessages([])}
            className="w-full flex items-center gap-2 px-3 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Plus size={16} />
            新建会话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <p className="text-xs font-semibold text-gray-400 px-2 py-1 uppercase tracking-wide">会话历史</p>
          {messages.length > 0 && (
            <div className="px-3 py-2 rounded-lg bg-indigo-50 text-indigo-700 text-sm font-medium truncate">
              {messages[0].content.slice(0, 30)}…
            </div>
          )}
          {messages.length === 0 && (
            <p className="text-xs text-gray-400 px-3 py-2">暂无会话记录</p>
          )}
        </div>
      </aside>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-indigo-100 flex items-center justify-center mb-4">
              <Sparkles size={32} className="text-indigo-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">有什么可以帮你？</h2>
            <p className="text-gray-500 text-sm mb-8">基于 LangGraph 的 AI 智能体，支持知识库检索增强</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  className="p-3 text-left text-sm text-gray-600 bg-white border border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={clsx("flex gap-3", msg.role === "user" && "flex-row-reverse")}
              >
                <div
                  className={clsx(
                    "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                    msg.role === "assistant"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  )}
                >
                  {msg.role === "assistant" ? <Bot size={16} /> : <User size={16} />}
                </div>
                <div
                  className={clsx(
                    "max-w-2xl px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap",
                    msg.role === "assistant"
                      ? "bg-white border border-gray-200 text-gray-800 shadow-sm"
                      : "bg-indigo-600 text-white"
                  )}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            {error && (
              <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex gap-3 items-end max-w-4xl mx-auto">
            <div className="flex-1 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
              <textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="输入消息… (Enter 发送，Shift+Enter 换行)"
                className="w-full bg-transparent text-sm text-gray-800 placeholder-gray-400 outline-none resize-none"
                style={{ maxHeight: 120 }}
              />
            </div>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            消息经过 Go 网关 JWT 鉴权后转发至 LangGraph Agent
          </p>
        </div>
      </div>
    </div>
  )
}
