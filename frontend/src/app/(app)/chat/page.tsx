"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Send,
  Bot,
  User,
  Plus,
  Sparkles,
  AlertCircle,
  Mic,
  Square,
  Volume2,
  BookOpen,
  Trash2,
  Loader2,
} from "lucide-react"
import clsx from "clsx"
import { ApiError, chatApi, knowledgeApi } from "@/lib/api"
import { useWorkspaceStore } from "@/store/workspace"
import { speak, stopSpeak, useVoiceRecorder } from "@/lib/speech"
import { Markdown } from "@/components/ui/Markdown"
import { toast } from "@/components/ui/Toast"
import type {
  ChatMessage,
  Citation,
  ConversationSummary,
  KnowledgeBase,
} from "@/types"

const SUGGESTED_PROMPTS = [
  "介绍一下 LangChain 与 LangGraph 的关系",
  "RAG 的多路召回是怎么做的?",
  "如何评估一个 RAG 系统的回答质量?",
  "GraphRAG 比传统向量检索强在哪里?",
]

interface DisplayMessage extends ChatMessage {
  id: string
  streaming?: boolean
}

export default function ChatPage() {
  const { activeWorkspaceId } = useWorkspaceStore()

  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [kbList, setKbList] = useState<KnowledgeBase[]>([])
  const [kbId, setKbId] = useState<string | null>(null)

  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  const recorder = useVoiceRecorder()

  // 初始加载
  const refreshConversations = useCallback(async () => {
    try {
      const list = await chatApi.conversations()
      setConversations(list)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) return
      toast.error(err instanceof ApiError ? err.message : "加载会话失败")
    }
  }, [])

  const refreshKbs = useCallback(async () => {
    try {
      const list = await knowledgeApi.list()
      setKbList(list)
    } catch {
      /* silent */
    }
  }, [])

  useEffect(() => {
    ;(async () => {
      try {
        await Promise.all([refreshConversations(), refreshKbs()])
      } catch (err) {
        toast.error(err instanceof ApiError ? err.message : "初始化失败")
      }
    })()
  }, [refreshConversations, refreshKbs, activeWorkspaceId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function loadConversation(id: string) {
    try {
      setActiveConvId(id)
      const msgs = await chatApi.messages(id)
      setMessages(
        msgs.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations,
        }))
      )
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "加载消息失败")
    }
  }

  function newConversation() {
    abortRef.current?.abort()
    setActiveConvId(null)
    setMessages([])
    setError(null)
  }

  async function deleteConversation(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm("删除该会话?")) return
    try {
      await chatApi.removeConversation(id)
      setConversations((p) => p.filter((c) => c.id !== id))
      if (activeConvId === id) newConversation()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "删除失败")
    }
  }

  async function handleSend(text?: string) {
    const content = (text ?? input).trim()
    if (!content || loading) return

    setError(null)
    const userMsg: DisplayMessage = {
      id: `local-u-${Date.now()}`,
      role: "user",
      content,
    }
    const assistantId = `local-a-${Date.now()}`
    const assistantPlaceholder: DisplayMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      citations: [],
      streaming: true,
    }
    setMessages((prev) => [...prev, userMsg, assistantPlaceholder])
    setInput("")
    setLoading(true)

    const history: ChatMessage[] = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }))

    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    let convId = activeConvId
    let acc = ""
    let citations: Citation[] = []

    try {
      await chatApi.stream(
        history,
        { conversationId: convId, knowledgeBaseId: kbId },
        (evt) => {
          const e = evt as { event?: string; [k: string]: unknown }
          if (e.event === "conversation" && typeof e.conversation_id === "string") {
            convId = e.conversation_id
            setActiveConvId(convId)
          } else if (e.event === "retrieved" && Array.isArray(e.chunks)) {
            citations = e.chunks as Citation[]
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, citations } : m
              )
            )
          } else if (e.event === "token" && typeof e.text === "string") {
            acc += e.text
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, content: acc } : m))
            )
          } else if (e.event === "done") {
            const final = (e.content as string) || acc
            const finalCit = (e.chunks as Citation[] | undefined) || citations
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: final, citations: finalCit, streaming: false }
                  : m
              )
            )
          } else if (e.event === "error") {
            setError((e.message as string) || "服务异常")
          }
        },
        ctrl.signal
      )
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        // user-cancelled
      } else {
        const msg = err instanceof ApiError ? err.message : "请求失败"
        setError(msg)
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m))
        )
      }
    } finally {
      setLoading(false)
      abortRef.current = null
      await refreshConversations()
    }
  }

  function cancelStream() {
    abortRef.current?.abort()
    setLoading(false)
  }

  async function handleVoice() {
    if (recorder.recording) {
      const text = await recorder.stopAndTranscribe()
      if (text) {
        setInput((prev) => (prev ? `${prev} ${text}` : text))
      } else if (recorder.error) {
        toast.error(recorder.error)
      }
    } else {
      await recorder.start()
      if (recorder.error) toast.error(recorder.error)
    }
  }

  async function handleSpeak(content: string) {
    try {
      stopSpeak()
      await speak(content)
    } catch {
      toast.error("播报失败")
    }
  }

  const activeKb = useMemo(
    () => kbList.find((k) => k.id === kbId) ?? null,
    [kbList, kbId]
  )

  return (
    <div className="flex h-full">
      {/* Conversation List */}
      <aside className="w-64 bg-white border-r border-gray-200 flex-col hidden md:flex">
        <div className="p-4 border-b border-gray-100 space-y-2">
          <button
            onClick={newConversation}
            className="w-full flex items-center gap-2 px-3 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Plus size={16} />
            新建会话
          </button>
          {/* KB selector */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1.5 uppercase tracking-wide">
              知识库
            </label>
            <select
              value={kbId ?? ""}
              onChange={(e) => setKbId(e.target.value || null)}
              className="w-full text-sm px-2.5 py-2 border border-gray-200 rounded-lg outline-none focus:border-indigo-400"
            >
              <option value="">无 (直接调用 LLM)</option>
              {kbList.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
            </select>
            {activeKb && (
              <p className="text-[11px] text-gray-400 mt-1 flex items-center gap-1">
                <BookOpen size={11} />
                {activeKb.doc_count} 文档 · {activeKb.chunk_count} 切片
              </p>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <p className="text-xs font-semibold text-gray-400 px-2 py-1 uppercase tracking-wide">
            会话历史
          </p>
          {conversations.length === 0 && (
            <p className="text-xs text-gray-400 px-3 py-2">暂无会话记录</p>
          )}
          {conversations.map((c) => {
            const active = c.id === activeConvId
            return (
              <div
                key={c.id}
                onClick={() => loadConversation(c.id)}
                className={clsx(
                  "group flex items-center justify-between gap-1 px-2.5 py-2 rounded-lg text-sm cursor-pointer transition-colors",
                  active
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-700 hover:bg-gray-50"
                )}
              >
                <span className="truncate flex-1">{c.title || "新会话"}</span>
                <button
                  onClick={(e) => deleteConversation(c.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            )
          })}
        </div>
      </aside>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-indigo-100 flex items-center justify-center mb-4">
              <Sparkles size={32} className="text-indigo-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">有什么可以帮你?</h2>
            <p className="text-gray-500 text-sm mb-8">
              LangGraph + 多路召回 + 重排 · {activeKb ? `已绑定:${activeKb.name}` : "未绑定知识库"}
            </p>
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
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onSpeak={() => handleSpeak(msg.content)}
              />
            ))}
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
          <div className="flex gap-2 items-end max-w-4xl mx-auto">
            <button
              onClick={handleVoice}
              disabled={recorder.transcribing}
              title={recorder.recording ? "停止并转写" : "语音输入"}
              className={clsx(
                "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-colors",
                recorder.recording
                  ? "bg-red-500 text-white animate-pulse"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {recorder.transcribing ? (
                <Loader2 size={18} className="animate-spin" />
              ) : recorder.recording ? (
                <Square size={16} />
              ) : (
                <Mic size={18} />
              )}
            </button>

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
                placeholder="输入消息… (Enter 发送, Shift+Enter 换行)"
                className="w-full bg-transparent text-sm text-gray-800 placeholder-gray-400 outline-none resize-none"
                style={{ maxHeight: 160 }}
              />
            </div>

            {loading ? (
              <button
                onClick={cancelStream}
                className="w-10 h-10 rounded-xl bg-gray-200 text-gray-700 flex items-center justify-center hover:bg-gray-300 shrink-0"
                title="停止生成"
              >
                <Square size={16} />
              </button>
            ) : (
              <button
                onClick={() => handleSend()}
                disabled={!input.trim()}
                className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
              >
                <Send size={18} />
              </button>
            )}
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            消息经过 Go 网关 JWT 鉴权 → Python LangGraph(多路召回 + 重排)
            {activeKb ? ` · 当前知识库: ${activeKb.name}` : ""}
          </p>
        </div>
      </div>
    </div>
  )
}

interface BubbleProps {
  msg: DisplayMessage
  onSpeak: () => void
}

function MessageBubble({ msg, onSpeak }: BubbleProps) {
  const isUser = msg.role === "user"
  const [activeCite, setActiveCite] = useState<number | null>(null)

  return (
    <div className={clsx("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
          isUser ? "bg-gray-200 text-gray-600" : "bg-indigo-600 text-white"
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className={clsx("max-w-2xl", isUser ? "items-end" : "items-start", "flex flex-col gap-2")}>
        <div
          className={clsx(
            "px-4 py-3 rounded-2xl text-sm",
            isUser
              ? "bg-indigo-600 text-white whitespace-pre-wrap"
              : "bg-white border border-gray-200 text-gray-800 shadow-sm"
          )}
        >
          {isUser ? (
            msg.content
          ) : msg.streaming && !msg.content ? (
            <div className="flex gap-1 py-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          ) : (
            <Markdown
              content={msg.content}
              onCiteClick={(idx) => setActiveCite(idx)}
            />
          )}
        </div>
        {/* Citations */}
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div className="space-y-1.5 max-w-2xl">
            {msg.citations.map((c, i) => {
              const active = activeCite === i + 1
              return (
                <div
                  key={c.chunk_id}
                  className={clsx(
                    "border rounded-lg p-2 text-xs cursor-pointer transition-all",
                    active
                      ? "border-indigo-400 bg-indigo-50 ring-2 ring-indigo-100"
                      : "border-gray-200 bg-gray-50 hover:border-gray-300"
                  )}
                  onClick={() => setActiveCite(active ? null : i + 1)}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="font-bold text-indigo-600">[{i + 1}]</span>
                    <span className="text-gray-500 truncate flex-1">
                      {c.filename || c.document_id}
                    </span>
                    {c.sources?.map((s) => (
                      <span
                        key={s}
                        className="px-1 py-0.5 bg-white border border-gray-200 rounded text-gray-500 font-mono text-[10px]"
                      >
                        {s}
                      </span>
                    ))}
                    <span className="font-mono text-gray-500">
                      {c.score.toFixed(3)}
                    </span>
                  </div>
                  <p
                    className={clsx(
                      "text-gray-700 whitespace-pre-wrap",
                      active ? "" : "line-clamp-2"
                    )}
                  >
                    {c.content}
                  </p>
                </div>
              )
            })}
          </div>
        )}
        {/* TTS button */}
        {!isUser && !msg.streaming && msg.content && (
          <button
            onClick={onSpeak}
            className="self-start text-xs text-gray-400 hover:text-indigo-600 flex items-center gap-1"
          >
            <Volume2 size={12} />
            朗读
          </button>
        )}
      </div>
    </div>
  )
}
