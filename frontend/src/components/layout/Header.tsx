"use client"

import { Bell, Search } from "lucide-react"
import { WorkspaceSelector } from "./WorkspaceSelector"

export function Header() {
  return (
    <header className="h-16 bg-indigo-700 flex items-center px-4 gap-4 shrink-0 shadow-md">
      {/* Workspace Selector */}
      <WorkspaceSelector />

      {/* Search */}
      <div className="flex-1 max-w-md hidden sm:flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2 border border-white/20">
        <Search size={16} className="text-white/60" />
        <input
          type="text"
          placeholder="搜索知识库、会话..."
          className="bg-transparent text-sm text-white placeholder-white/50 outline-none flex-1"
        />
        <kbd className="text-xs text-white/40 bg-white/10 px-1.5 py-0.5 rounded hidden md:block">
          ⌘K
        </kbd>
      </div>

      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button className="w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors relative">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-400 rounded-full" />
        </button>
      </div>
    </header>
  )
}
