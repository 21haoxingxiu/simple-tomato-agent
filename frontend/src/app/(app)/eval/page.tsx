"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  FlaskConical,
  Plus,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Trash2,
  Pencil,
  Database,
  RefreshCw,
} from "lucide-react"
import clsx from "clsx"
import { ApiError, evalApi, knowledgeApi } from "@/lib/api"
import { useWorkspaceStore } from "@/store/workspace"
import { Modal } from "@/components/ui/Modal"
import { toast } from "@/components/ui/Toast"
import type { EvalCase, EvalRun, EvalSummary, KnowledgeBase } from "@/types"

interface CaseFormState {
  id?: string
  question: string
  expected_answer: string
}

const EMPTY_FORM: CaseFormState = { question: "", expected_answer: "" }

export default function EvalPage() {
  const { activeWorkspaceId } = useWorkspaceStore()

  const [cases, setCases] = useState<EvalCase[]>([])
  const [summary, setSummary] = useState<EvalSummary | null>(null)
  const [kbs, setKbs] = useState<KnowledgeBase[]>([])
  const [kbId, setKbId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [runningAll, setRunningAll] = useState(false)
  const [runningId, setRunningId] = useState<string | null>(null)

  const [formOpen, setFormOpen] = useState(false)
  const [form, setForm] = useState<CaseFormState>(EMPTY_FORM)
  const [detail, setDetail] = useState<EvalRun | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [list, sum, kbList] = await Promise.all([
        evalApi.listCases(),
        evalApi.summary(),
        knowledgeApi.list(),
      ])
      setCases(list)
      setSummary(sum)
      setKbs(kbList)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "加载失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh, activeWorkspaceId])

  function openCreate() {
    setForm(EMPTY_FORM)
    setFormOpen(true)
  }

  function openEdit(c: EvalCase) {
    setForm({
      id: c.id,
      question: c.question,
      expected_answer: c.expected_answer,
    })
    setFormOpen(true)
  }

  async function submitForm() {
    if (!form.question.trim()) return
    try {
      if (form.id) {
        const updated = await evalApi.updateCase(form.id, {
          question: form.question.trim(),
          expected_answer: form.expected_answer,
        })
        setCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
        toast.success("已更新")
      } else {
        const created = await evalApi.createCase({
          question: form.question.trim(),
          expected_answer: form.expected_answer,
        })
        setCases((prev) => [created, ...prev])
        toast.success("已添加")
      }
      setFormOpen(false)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "保存失败")
    }
  }

  async function removeCase(id: string) {
    if (!confirm("删除该测试用例?")) return
    try {
      await evalApi.removeCase(id)
      setCases((prev) => prev.filter((c) => c.id !== id))
      toast.success("已删除")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "删除失败")
    }
  }

  async function runOne(id: string) {
    setRunningId(id)
    try {
      const run = await evalApi.runCase(id, kbId)
      setCases((prev) =>
        prev.map((c) => (c.id === id ? { ...c, latest_run: run } : c))
      )
      const sum = await evalApi.summary()
      setSummary(sum)
      toast.success(run.passed ? "通过" : "未通过")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "运行失败")
    } finally {
      setRunningId(null)
    }
  }

  async function runAll() {
    if (cases.length === 0) return
    setRunningAll(true)
    try {
      const summary = await evalApi.runBatch({
        case_ids: cases.map((c) => c.id),
        kb_id: kbId ?? undefined,
      })
      toast.success(
        `批量运行完成: ${summary.passed}/${summary.total} 通过 · 平均分 ${
          summary.avg_score !== null ? (summary.avg_score * 100).toFixed(0) + "%" : "-"
        }`
      )
      await refresh()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "批量运行失败")
    } finally {
      setRunningAll(false)
    }
  }

  const stats = useMemo(() => {
    const passed = summary?.passed ?? 0
    const failed = summary?.failed ?? 0
    const avg = summary?.avg_score ?? null
    return { passed, failed, avg }
  }, [summary])

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评测中心</h1>
          <p className="text-sm text-gray-500 mt-1">
            多指标评估: 语义相似度 / Faithfulness / Answer Relevance
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <select
            value={kbId ?? ""}
            onChange={(e) => setKbId(e.target.value || null)}
            className="text-sm px-3 py-2 border border-gray-200 rounded-lg outline-none focus:border-indigo-400 bg-white"
          >
            <option value="">不使用知识库</option>
            {kbs.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
          <button
            onClick={refresh}
            className="flex items-center gap-2 px-3 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
          >
            <RefreshCw size={14} />
            刷新
          </button>
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
          >
            <Plus size={16} />
            添加用例
          </button>
          <button
            onClick={runAll}
            disabled={runningAll || cases.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            <Play size={16} />
            {runningAll ? "运行中..." : "运行全部"}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="测试用例"
          value={cases.length}
          icon={<FlaskConical size={18} />}
          tone="indigo"
        />
        <StatCard
          label="通过"
          value={stats.passed}
          icon={<CheckCircle size={18} />}
          tone="green"
        />
        <StatCard
          label="失败"
          value={stats.failed}
          icon={<XCircle size={18} />}
          tone="red"
        />
        <StatCard
          label="平均得分"
          value={stats.avg !== null ? `${(stats.avg * 100).toFixed(0)}%` : "—"}
          icon={<BarChart3 size={18} />}
          tone="purple"
        />
      </div>

      {/* Cases */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">测试用例</h2>
          {kbId && (
            <span className="text-xs text-indigo-600 flex items-center gap-1.5">
              <Database size={12} />
              将使用知识库 RAG 检索
            </span>
          )}
        </div>

        {loading && cases.length === 0 ? (
          <p className="p-10 text-center text-gray-400">加载中...</p>
        ) : cases.length === 0 ? (
          <div className="p-10 text-center">
            <FlaskConical size={32} className="mx-auto text-gray-300 mb-2" />
            <p className="text-gray-500 mb-3">还没有测试用例</p>
            <button
              onClick={openCreate}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
            >
              添加第一个用例
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {cases.map((c) => (
              <CaseRow
                key={c.id}
                cse={c}
                running={runningId === c.id}
                onRun={() => runOne(c.id)}
                onEdit={() => openEdit(c)}
                onDelete={() => removeCase(c.id)}
                onShowRun={(r) => setDetail(r)}
              />
            ))}
          </div>
        )}
      </div>

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={form.id ? "编辑用例" : "新建用例"}
        size="lg"
        footer={
          <>
            <button
              onClick={() => setFormOpen(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              取消
            </button>
            <button
              onClick={submitForm}
              disabled={!form.question.trim()}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              保存
            </button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block">问题</label>
            <textarea
              rows={3}
              value={form.question}
              onChange={(e) => setForm({ ...form, question: e.target.value })}
              placeholder="例如:什么是 RAG?"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block">
              期望答案 (用于语义相似度计算)
            </label>
            <textarea
              rows={5}
              value={form.expected_answer}
              onChange={(e) =>
                setForm({ ...form, expected_answer: e.target.value })
              }
              placeholder="可选..."
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        </div>
      </Modal>

      <Modal
        open={!!detail}
        onClose={() => setDetail(null)}
        title="本次运行详情"
        size="lg"
      >
        {detail && <RunDetail run={detail} />}
      </Modal>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
  tone,
}: {
  label: string
  value: number | string
  icon: React.ReactNode
  tone: "indigo" | "green" | "red" | "purple"
}) {
  const toneCls: Record<typeof tone, string> = {
    indigo: "bg-indigo-50 text-indigo-600",
    green: "bg-green-50 text-green-600",
    red: "bg-red-50 text-red-600",
    purple: "bg-purple-50 text-purple-600",
  }
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div
        className={clsx(
          "w-9 h-9 rounded-lg flex items-center justify-center mb-3",
          toneCls[tone]
        )}
      >
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  )
}

interface CaseRowProps {
  cse: EvalCase
  running: boolean
  onRun: () => void
  onEdit: () => void
  onDelete: () => void
  onShowRun: (r: EvalRun) => void
}

function CaseRow({ cse, running, onRun, onEdit, onDelete, onShowRun }: CaseRowProps) {
  const run = cse.latest_run
  const statusIcon = !run ? (
    <Clock size={16} className="text-gray-400" />
  ) : running ? (
    <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
  ) : run.passed ? (
    <CheckCircle size={16} className="text-green-500" />
  ) : (
    <XCircle size={16} className="text-red-500" />
  )

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{statusIcon}</div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 mb-2">{cse.question}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-green-50 rounded-lg p-3 min-h-[6rem]">
              <p className="text-xs font-semibold text-green-600 mb-1">期望答案</p>
              <p className="text-sm text-gray-700 line-clamp-4 whitespace-pre-wrap">
                {cse.expected_answer || (
                  <span className="text-gray-400 italic">未设置</span>
                )}
              </p>
            </div>
            <div
              className={clsx(
                "rounded-lg p-3 min-h-[6rem] cursor-pointer hover:ring-2 hover:ring-indigo-100 transition-all",
                run ? "bg-blue-50" : "bg-gray-50"
              )}
              onClick={() => run && onShowRun(run)}
            >
              <p className="text-xs font-semibold text-blue-600 mb-1">实际输出</p>
              <p className="text-sm text-gray-700 line-clamp-4 whitespace-pre-wrap">
                {run?.actual_answer || (
                  <span className="text-gray-400 italic">尚未运行</span>
                )}
              </p>
            </div>
          </div>
          {run && (
            <div className="flex flex-wrap items-center gap-3 mt-3 text-xs">
              <Metric label="综合" value={run.score} />
              <Metric label="相似度" value={run.similarity} />
              <Metric label="Faithfulness" value={run.faithfulness} />
              <Metric label="Relevance" value={run.relevance} />
              <span className="text-gray-400">· {run.latency_ms} ms</span>
              {run.error_msg && (
                <span className="text-red-500 truncate" title={run.error_msg}>
                  {run.error_msg}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={onRun}
            disabled={running}
            className="p-2 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-50"
            title="运行"
          >
            <Play size={16} />
          </button>
          <button
            onClick={onEdit}
            className="p-2 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
            title="编辑"
          >
            <Pencil size={14} />
          </button>
          <button
            onClick={onDelete}
            className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="删除"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number | null }) {
  if (value === null || value === undefined)
    return (
      <span className="text-gray-400">
        {label}: <span className="font-mono">—</span>
      </span>
    )
  const pct = Math.round(value * 100)
  const tone =
    pct >= 80
      ? "text-green-700 bg-green-100"
      : pct >= 60
      ? "text-yellow-700 bg-yellow-100"
      : "text-red-700 bg-red-100"
  return (
    <span className={clsx("font-medium px-2 py-0.5 rounded-full", tone)}>
      {label}: {pct}%
    </span>
  )
}

function RunDetail({ run }: { run: EvalRun }) {
  return (
    <div className="space-y-4 text-sm">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <DetailMetric label="综合" value={run.score} />
        <DetailMetric label="相似度" value={run.similarity} />
        <DetailMetric label="Faithfulness" value={run.faithfulness} />
        <DetailMetric label="Relevance" value={run.relevance} />
      </div>
      <div>
        <p className="text-xs font-semibold text-gray-500 mb-1">实际输出</p>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 whitespace-pre-wrap">
          {run.actual_answer || "(空)"}
        </div>
      </div>
      {run.citations.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-1">引用片段</p>
          <div className="space-y-2">
            {run.citations.map((c, i) => (
              <div
                key={c.chunk_id}
                className="border border-gray-200 rounded-lg p-2 bg-gray-50/50 text-xs"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-bold text-indigo-600">[{i + 1}]</span>
                  <span className="text-gray-500 truncate flex-1">
                    {c.filename}
                  </span>
                  <span className="font-mono text-gray-500">
                    {c.score.toFixed(3)}
                  </span>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap line-clamp-4">
                  {c.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      <p className="text-xs text-gray-400">
        延迟 {run.latency_ms} ms · {new Date(run.created_at).toLocaleString()}
      </p>
    </div>
  )
}

function DetailMetric({ label, value }: { label: string; value: number | null }) {
  if (value === null) {
    return (
      <div className="border border-gray-200 rounded-lg p-3 text-center bg-gray-50">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-lg font-bold text-gray-400">—</p>
      </div>
    )
  }
  const pct = Math.round(value * 100)
  return (
    <div className="border border-gray-200 rounded-lg p-3 text-center bg-white">
      <p className="text-xs text-gray-500">{label}</p>
      <p
        className={clsx(
          "text-lg font-bold",
          pct >= 80
            ? "text-green-600"
            : pct >= 60
            ? "text-yellow-600"
            : "text-red-600"
        )}
      >
        {pct}%
      </p>
    </div>
  )
}
