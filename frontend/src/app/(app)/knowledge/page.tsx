"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  BookOpen,
  Plus,
  Upload,
  Search,
  FileText,
  Trash2,
  RefreshCw,
  Database,
  Layers,
  X,
  Settings2,
  Sparkles,
} from "lucide-react"
import clsx from "clsx"
import { knowledgeApi, ApiError } from "@/lib/api"
import { useWorkspaceStore } from "@/store/workspace"
import { Modal } from "@/components/ui/Modal"
import { toast } from "@/components/ui/Toast"
import type { KnowledgeBase, KnowledgeDocument, RetrievedChunk } from "@/types"

const STATUS_MAP: Record<KnowledgeBase["status"], { label: string; cls: string }> = {
  ready: { label: "就绪", cls: "bg-green-100 text-green-700" },
  indexing: { label: "索引中", cls: "bg-yellow-100 text-yellow-700" },
  error: { label: "错误", cls: "bg-red-100 text-red-700" },
}

const DOC_STATUS: Record<KnowledgeDocument["status"], { label: string; cls: string }> = {
  parsing: { label: "解析中", cls: "text-yellow-600" },
  indexing: { label: "索引中", cls: "text-yellow-600" },
  ready: { label: "就绪", cls: "text-green-600" },
  error: { label: "错误", cls: "text-red-600" },
}

export default function KnowledgePage() {
  const { activeWorkspaceId } = useWorkspaceStore()

  const [bases, setBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<KnowledgeBase | null>(null)
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [creating, setCreating] = useState(false)
  const [createName, setCreateName] = useState("")
  const [createDesc, setCreateDesc] = useState("")
  const [uploading, setUploading] = useState(false)
  const [retrieveQuery, setRetrieveQuery] = useState("")
  const [retrieveResults, setRetrieveResults] = useState<RetrievedChunk[]>([])
  const [retrieving, setRetrieving] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const list = await knowledgeApi.list()
      setBases(list)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "加载失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh, activeWorkspaceId])

  const loadDocs = useCallback(async (kb: KnowledgeBase) => {
    try {
      const docs = await knowledgeApi.documents(kb.id)
      setDocuments(docs)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "加载文档失败")
    }
  }, [])

  useEffect(() => {
    if (selected) loadDocs(selected)
    else setDocuments([])
  }, [selected, loadDocs])

  async function handleCreate() {
    if (!createName.trim()) return
    try {
      const kb = await knowledgeApi.create(createName.trim(), createDesc.trim())
      setBases((prev) => [kb, ...prev])
      setCreating(false)
      setCreateName("")
      setCreateDesc("")
      toast.success("知识库已创建")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "创建失败")
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("确定删除该知识库及其所有文档?")) return
    try {
      await knowledgeApi.remove(id)
      setBases((prev) => prev.filter((b) => b.id !== id))
      if (selected?.id === id) setSelected(null)
      toast.success("已删除")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "删除失败")
    }
  }

  async function handleUpload(files: FileList | null) {
    if (!files || !selected) return
    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        await knowledgeApi.upload(selected.id, file)
        toast.success(`已索引: ${file.name}`)
      }
      await Promise.all([refresh(), loadDocs(selected)])
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "上传失败")
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ""
    }
  }

  async function handleDeleteDoc(docId: string) {
    if (!selected) return
    if (!confirm("确定删除该文档?")) return
    try {
      await knowledgeApi.removeDocument(selected.id, docId)
      await Promise.all([refresh(), loadDocs(selected)])
      toast.success("文档已删除")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "删除失败")
    }
  }

  async function handleRetrieve() {
    if (!selected || !retrieveQuery.trim()) return
    setRetrieving(true)
    try {
      const res = await knowledgeApi.retrieve(selected.id, retrieveQuery.trim(), {
        topK: 5,
        recallK: 12,
      })
      setRetrieveResults(res)
      if (res.length === 0) toast.info("无召回结果")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "检索失败")
    } finally {
      setRetrieving(false)
    }
  }

  const filtered = useMemo(
    () =>
      bases.filter(
        (b) => b.name.includes(search) || b.description.includes(search)
      ),
    [bases, search]
  )

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">知识库</h1>
          <p className="text-sm text-gray-500 mt-1">
            管理 AI 智能体的知识文档,支持多路召回(向量 + BM25) 与可选 GraphRAG
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={refresh}
            className="flex items-center gap-2 px-3 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={14} />
            刷新
          </button>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Plus size={16} />
            新建知识库
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {[
          { label: "知识库", value: bases.length, icon: BookOpen, color: "indigo" },
          {
            label: "文档总数",
            value: bases.reduce((s, b) => s + b.doc_count, 0),
            icon: FileText,
            color: "blue",
          },
          {
            label: "切片总数",
            value: bases.reduce((s, b) => s + b.chunk_count, 0),
            icon: Layers,
            color: "purple",
          },
          {
            label: "向量库",
            value: process.env.NEXT_PUBLIC_VECTOR_STORE ?? "Chroma",
            icon: Database,
            color: "green",
          },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div
              className={clsx(
                "w-9 h-9 rounded-lg flex items-center justify-center mb-3",
                `bg-${color}-50`
              )}
            >
              <Icon size={18} className={`text-${color}-600`} />
            </div>
            <p className="text-xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 mb-6 max-w-sm">
        <Search size={16} className="text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索知识库..."
          className="flex-1 text-sm outline-none text-gray-700 placeholder-gray-400 bg-transparent"
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading && bases.length === 0 ? (
          <div className="col-span-full text-center text-gray-400 py-16">加载中...</div>
        ) : (
          <>
            {filtered.map((kb) => {
              const status = STATUS_MAP[kb.status] ?? STATUS_MAP.ready
              const isSel = selected?.id === kb.id
              return (
                <div
                  key={kb.id}
                  onClick={() => setSelected(isSel ? null : kb)}
                  className={clsx(
                    "bg-white rounded-xl border p-5 cursor-pointer transition-all hover:shadow-md",
                    isSel
                      ? "border-indigo-400 ring-2 ring-indigo-100 shadow-md"
                      : "border-gray-200"
                  )}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                      <BookOpen size={20} className="text-indigo-600" />
                    </div>
                    <span
                      className={clsx(
                        "text-xs font-medium px-2 py-1 rounded-full",
                        status.cls
                      )}
                    >
                      {kb.status === "indexing" && (
                        <RefreshCw size={10} className="inline mr-1 animate-spin" />
                      )}
                      {status.label}
                    </span>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-1 truncate">
                    {kb.name}
                  </h3>
                  <p className="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[2.5rem]">
                    {kb.description || "—"}
                  </p>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <FileText size={12} />
                        {kb.doc_count} 文档
                      </span>
                      <span className="flex items-center gap-1">
                        <Layers size={12} />
                        {kb.chunk_count} 切片
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
            <button
              onClick={() => setCreating(true)}
              className="bg-white rounded-xl border-2 border-dashed border-gray-200 p-5 flex flex-col items-center justify-center gap-3 text-gray-400 hover:border-indigo-300 hover:text-indigo-500 hover:bg-indigo-50/30 transition-all min-h-[180px]"
            >
              <Plus size={24} />
              <span className="text-sm font-medium">新建知识库</span>
            </button>
          </>
        )}
      </div>

      {/* Detail Drawer */}
      {selected && (
        <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-white shadow-2xl border-l border-gray-200 z-30 flex flex-col">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h2 className="font-bold text-gray-900">{selected.name}</h2>
              <p className="text-xs text-gray-500 mt-0.5">{selected.id}</p>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-400 hover:text-gray-700"
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Upload + Documents */}
            <section>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <FileText size={14} />
                  文档管理
                </h3>
                <button
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Upload size={12} />
                  {uploading ? "上传中..." : "上传文档"}
                </button>
                <input
                  ref={fileRef}
                  type="file"
                  multiple
                  className="hidden"
                  accept=".pdf,.txt,.md,.docx,.html,.htm"
                  onChange={(e) => handleUpload(e.target.files)}
                />
              </div>
              <div className="border border-gray-100 rounded-lg divide-y divide-gray-100">
                {documents.length === 0 ? (
                  <p className="text-sm text-gray-400 px-4 py-6 text-center">
                    暂无文档,上传 PDF / DOCX / MD / TXT / HTML 开始构建索引
                  </p>
                ) : (
                  documents.map((d) => {
                    const ds = DOC_STATUS[d.status] ?? DOC_STATUS.ready
                    return (
                      <div
                        key={d.id}
                        className="flex items-center justify-between px-4 py-2.5 text-sm"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-900 truncate">{d.filename}</p>
                          <p className="text-xs text-gray-400">
                            <span className={ds.cls}>{ds.label}</span> ·{" "}
                            {d.chunk_count} 切片 · {(d.size_bytes / 1024).toFixed(1)} KB
                          </p>
                          {d.error_msg && (
                            <p className="text-xs text-red-500 truncate">
                              {d.error_msg}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => handleDeleteDoc(d.id)}
                          className="ml-2 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    )
                  })
                )}
              </div>
            </section>

            {/* Retrieve Debug */}
            <section>
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <Sparkles size={14} />
                检索调试 (多路召回 + 重排)
              </h3>
              <div className="flex gap-2 mb-3">
                <input
                  value={retrieveQuery}
                  onChange={(e) => setRetrieveQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleRetrieve()}
                  placeholder="输入查询语句..."
                  className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                />
                <button
                  onClick={handleRetrieve}
                  disabled={retrieving || !retrieveQuery.trim()}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {retrieving ? "..." : "检索"}
                </button>
              </div>
              <div className="space-y-2">
                {retrieveResults.map((c, i) => (
                  <div
                    key={c.chunk_id}
                    className="border border-gray-200 rounded-lg p-3 bg-gray-50/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-indigo-600">
                          [{i + 1}]
                        </span>
                        <span className="text-xs text-gray-500">{c.filename}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        {c.sources?.map((s) => (
                          <span
                            key={s}
                            className="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-500 font-mono"
                          >
                            {s}
                          </span>
                        ))}
                        <span className="font-mono text-gray-700">
                          {c.score.toFixed(3)}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-4 whitespace-pre-wrap">
                      {c.content}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* Danger Zone */}
            <section className="pt-4 border-t border-gray-100">
              <button
                onClick={() => handleDelete(selected.id)}
                className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <Trash2 size={14} />
                删除知识库
              </button>
            </section>
          </div>
        </div>
      )}

      {/* Create Modal */}
      <Modal
        open={creating}
        onClose={() => setCreating(false)}
        title="新建知识库"
        footer={
          <>
            <button
              onClick={() => setCreating(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              取消
            </button>
            <button
              onClick={handleCreate}
              disabled={!createName.trim()}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              创建
            </button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block">
              名称
            </label>
            <input
              autoFocus
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="如:产品文档"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block">
              描述
            </label>
            <textarea
              rows={3}
              value={createDesc}
              onChange={(e) => setCreateDesc(e.target.value)}
              placeholder="可选..."
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <p className="text-xs text-gray-400 flex items-start gap-1.5">
            <Settings2 size={12} className="shrink-0 mt-0.5" />
            创建后可在详情面板中上传文档、进行检索调试
          </p>
        </div>
      </Modal>
    </div>
  )
}
