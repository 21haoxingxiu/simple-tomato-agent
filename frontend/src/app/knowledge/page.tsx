"use client"

import { useState } from "react"
import { BookOpen, Plus, Upload, Search, FileText, Trash2, RefreshCw } from "lucide-react"
import clsx from "clsx"

interface KnowledgeBase {
  id: string
  name: string
  description: string
  docCount: number
  status: "ready" | "indexing" | "error"
  updatedAt: string
}

const MOCK_BASES: KnowledgeBase[] = [
  { id: "kb-1", name: "产品文档", description: "产品使用说明和 API 文档", docCount: 24, status: "ready", updatedAt: "2026-05-15" },
  { id: "kb-2", name: "技术规范", description: "架构设计和技术规范文档", docCount: 8, status: "indexing", updatedAt: "2026-05-14" },
  { id: "kb-3", name: "FAQ 知识库", description: "常见问题解答", docCount: 56, status: "ready", updatedAt: "2026-05-13" },
]

const STATUS_MAP = {
  ready: { label: "就绪", cls: "bg-green-100 text-green-700" },
  indexing: { label: "索引中", cls: "bg-yellow-100 text-yellow-700" },
  error: { label: "错误", cls: "bg-red-100 text-red-700" },
}

export default function KnowledgePage() {
  const [bases] = useState<KnowledgeBase[]>(MOCK_BASES)
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<string | null>(null)

  const filtered = bases.filter(
    (b) => b.name.includes(search) || b.description.includes(search)
  )

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">知识库</h1>
          <p className="text-sm text-gray-500 mt-1">管理 AI 智能体使用的知识文档</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
          <Plus size={16} />
          新建知识库
        </button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 mb-6 max-w-sm">
        <Search size={16} className="text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索知识库..."
          className="flex-1 text-sm outline-none text-gray-700 placeholder-gray-400"
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((kb) => {
          const status = STATUS_MAP[kb.status]
          return (
            <div
              key={kb.id}
              onClick={() => setSelected(kb.id === selected ? null : kb.id)}
              className={clsx(
                "bg-white rounded-xl border p-5 cursor-pointer transition-all hover:shadow-md",
                selected === kb.id
                  ? "border-indigo-400 ring-2 ring-indigo-100 shadow-md"
                  : "border-gray-200"
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <BookOpen size={20} className="text-indigo-600" />
                </div>
                <span className={clsx("text-xs font-medium px-2 py-1 rounded-full", status.cls)}>
                  {kb.status === "indexing" && (
                    <RefreshCw size={10} className="inline mr-1 animate-spin" />
                  )}
                  {status.label}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{kb.name}</h3>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">{kb.description}</p>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <div className="flex items-center gap-1">
                  <FileText size={12} />
                  <span>{kb.docCount} 个文档</span>
                </div>
                <span>更新于 {kb.updatedAt}</span>
              </div>

              {selected === kb.id && (
                <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                  <button className="flex-1 flex items-center justify-center gap-1.5 py-2 text-sm bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors">
                    <Upload size={14} />
                    上传文档
                  </button>
                  <button className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </div>
          )
        })}

        {/* Add Card */}
        <button className="bg-white rounded-xl border-2 border-dashed border-gray-200 p-5 flex flex-col items-center justify-center gap-3 text-gray-400 hover:border-indigo-300 hover:text-indigo-500 hover:bg-indigo-50/30 transition-all min-h-[180px]">
          <Plus size={24} />
          <span className="text-sm font-medium">新建知识库</span>
        </button>
      </div>
    </div>
  )
}
