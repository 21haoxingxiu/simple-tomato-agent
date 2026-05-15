"use client"

import { useState } from "react"
import { FlaskConical, Plus, Play, CheckCircle, XCircle, Clock, BarChart3 } from "lucide-react"
import clsx from "clsx"

interface EvalCase {
  id: string
  question: string
  expected: string
  actual: string
  score: number | null
  status: "pending" | "running" | "passed" | "failed"
}

const MOCK_CASES: EvalCase[] = [
  {
    id: "ec-1",
    question: "什么是 RAG？",
    expected: "RAG（检索增强生成）是一种将外部知识库与大语言模型结合的技术...",
    actual: "RAG 是 Retrieval Augmented Generation 的缩写，通过检索相关文档来增强 LLM 的回答能力。",
    score: 0.92,
    status: "passed",
  },
  {
    id: "ec-2",
    question: "如何优化向量检索性能？",
    expected: "可以通过 HNSW 索引、批量查询、缓存等方式优化...",
    actual: "使用近似最近邻算法如 HNSW，并做好索引预热。",
    score: 0.78,
    status: "passed",
  },
  {
    id: "ec-3",
    question: "LangGraph 与 LangChain 的区别？",
    expected: "LangGraph 基于 LangChain，提供有状态的图结构来编排复杂 Agent 流程...",
    actual: "",
    score: null,
    status: "pending",
  },
]

const STATUS_ICON: Record<EvalCase["status"], React.ReactNode> = {
  pending: <Clock size={16} className="text-gray-400" />,
  running: <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />,
  passed: <CheckCircle size={16} className="text-green-500" />,
  failed: <XCircle size={16} className="text-red-500" />,
}

export default function EvalPage() {
  const [cases] = useState<EvalCase[]>(MOCK_CASES)
  const passed = cases.filter((c) => c.status === "passed").length
  const avgScore = cases
    .filter((c) => c.score !== null)
    .reduce((sum, c) => sum + (c.score ?? 0), 0) / (cases.filter((c) => c.score !== null).length || 1)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评测中心</h1>
          <p className="text-sm text-gray-500 mt-1">测试和评估 AI 智能体的回答质量</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-50 transition-colors">
            <Plus size={16} />
            添加测试用例
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
            <Play size={16} />
            运行全部
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {[
          { label: "测试用例", value: cases.length, icon: FlaskConical, color: "indigo" },
          { label: "通过", value: passed, icon: CheckCircle, color: "green" },
          { label: "失败", value: cases.filter((c) => c.status === "failed").length, icon: XCircle, color: "red" },
          { label: "平均得分", value: `${(avgScore * 100).toFixed(0)}%`, icon: BarChart3, color: "purple" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className={clsx("w-9 h-9 rounded-lg flex items-center justify-center mb-3", `bg-${color}-50`)}>
              <Icon size={18} className={`text-${color}-600`} />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Test Cases */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">测试用例</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {cases.map((c) => (
            <div key={c.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start gap-3">
                <div className="mt-0.5">{STATUS_ICON[c.status]}</div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 mb-2">{c.question}</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="bg-green-50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-green-600 mb-1">期望答案</p>
                      <p className="text-sm text-gray-700 line-clamp-3">{c.expected}</p>
                    </div>
                    <div className={clsx("rounded-lg p-3", c.actual ? "bg-blue-50" : "bg-gray-50")}>
                      <p className="text-xs font-semibold text-blue-600 mb-1">实际输出</p>
                      <p className="text-sm text-gray-700 line-clamp-3">
                        {c.actual || <span className="text-gray-400 italic">尚未运行</span>}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {c.score !== null && (
                    <div className={clsx(
                      "text-sm font-bold px-2.5 py-1 rounded-lg",
                      c.score >= 0.8 ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                    )}>
                      {(c.score * 100).toFixed(0)}%
                    </div>
                  )}
                  <button className="p-2 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors">
                    <Play size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
