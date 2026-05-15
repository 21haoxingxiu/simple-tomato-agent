"use client"

import { useState } from "react"
import { ChevronDown, Plus, Building2 } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspace"
import clsx from "clsx"

export function WorkspaceSelector() {
  const [open, setOpen] = useState(false)
  const { workspaces, activeWorkspaceId, setActiveWorkspace } = useWorkspaceStore()
  const active = workspaces.find((w) => w.id === activeWorkspaceId)

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
        <span className="max-w-[140px] truncate">{active?.name ?? "选择工作区"}</span>
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
              <button className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors">
                <Plus size={16} />
                新建工作区
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
