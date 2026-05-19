"use client"

import { useEffect, useState } from "react"
import { ChevronDown, Plus, Building2, X } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspace"
import { workspaceApi } from "@/lib/api"
import clsx from "clsx"

export function WorkspaceSelector() {
  const [open, setOpen] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createName, setCreateName] = useState("")
  const [createDescription, setCreateDescription] = useState("")
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const { workspaces, activeWorkspaceId, setActiveWorkspace, refresh } =
    useWorkspaceStore()
  const active = workspaces.find((w) => w.id === activeWorkspaceId)

  useEffect(() => {
    if (workspaces.length === 0) refresh()
  }, [workspaces.length, refresh])

  async function handleCreate() {
    if (!createName.trim()) {
      setError("请输入工作区名称")
      return
    }
    setCreating(true)
    setError("")
    try {
      const newWorkspace = await workspaceApi.create({
        name: createName.trim(),
        description: createDescription.trim() || undefined,
      })
      await refresh()
      setActiveWorkspace(newWorkspace.id)
      setShowCreateModal(false)
      setCreateName("")
      setCreateDescription("")
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败")
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
          "bg-white/10 hover:bg-white/20 text-white border border-white/20"
        )}
      >
        <Building2 size={16} />
        <span className="max-w-[160px] truncate">
          {active?.name ?? (workspaces.length === 0 ? "暂无工作区" : "选择工作区")}
        </span>
        <ChevronDown
          size={14}
          className={clsx("transition-transform", open && "rotate-180")}
        />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute top-full mt-2 left-0 z-20 w-64 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden">
            <div className="p-2">
              <p className="text-xs font-semibold text-gray-400 px-2 py-1 uppercase tracking-wide">
                工作区
              </p>
              {workspaces.length === 0 && (
                <p className="text-xs text-gray-400 px-3 py-2">暂无工作区,登录后自动创建</p>
              )}
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => {
                    setActiveWorkspace(ws.id)
                    setOpen(false)
                  }}
                  className={clsx(
                    "w-full flex items-start gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                    ws.id === activeWorkspaceId
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-gray-700 hover:bg-gray-50"
                  )}
                >
                  <div
                    className={clsx(
                      "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0",
                      ws.id === activeWorkspaceId
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-100 text-gray-600"
                    )}
                  >
                    {ws.name[0]}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{ws.name}</p>
                    {ws.description && (
                      <p className="text-xs text-gray-400 truncate">{ws.description}</p>
                    )}
                  </div>
                </button>
              ))}
            </div>
            <div className="border-t border-gray-100 p-2">
              <button
                onClick={() => {
                  setOpen(false)
                  setShowCreateModal(true)
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                <Plus size={16} />
                新建工作区
              </button>
            </div>
          </div>
        </>
      )}

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowCreateModal(false)} />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900">新建工作区</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X size={18} className="text-gray-400" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  placeholder="输入工作区名称"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  描述
                </label>
                <textarea
                  value={createDescription}
                  onChange={(e) => setCreateDescription(e.target.value)}
                  placeholder="输入工作区描述（可选）"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                />
              </div>
              {error && (
                <p className="text-sm text-red-500">{error}</p>
              )}
            </div>
            <div className="flex justify-end gap-3 px-5 py-4 bg-gray-50 border-t border-gray-100">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={creating}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? "创建中..." : "创建"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
