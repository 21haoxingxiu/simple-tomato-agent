"use client"

import { useState, useRef, useEffect } from "react"
import { Bell, ChevronDown, LogOut, Search, User as UserIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { WorkspaceSelector } from "./WorkspaceSelector"
import { useAuthStore } from "@/store/auth"
import { useWorkspaceStore } from "@/store/workspace"

export function Header() {
  const router = useRouter()
  const { user, logout } = useAuthStore()
  const resetWorkspaces = useWorkspaceStore((s) => s.reset)

  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener("mousedown", onClick)
    return () => window.removeEventListener("mousedown", onClick)
  }, [])

  function handleLogout() {
    logout()
    resetWorkspaces()
    router.replace("/login")
  }

  const initial = (user?.name || user?.email || "?")[0]?.toUpperCase() || "?"

  return (
    <header className="h-16 bg-indigo-700 flex items-center px-4 gap-4 shrink-0 shadow-md">
      <WorkspaceSelector />

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

      <button className="w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors relative">
        <Bell size={18} />
        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-400 rounded-full" />
      </button>

      <div className="relative" ref={ref}>
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
        >
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-xs font-bold text-white shrink-0">
            {initial}
          </div>
          <div className="hidden md:block text-left min-w-0">
            <p className="text-sm font-medium leading-tight truncate max-w-[120px]">
              {user?.name || "未登录"}
            </p>
            <p className="text-[11px] text-white/60 leading-tight truncate max-w-[120px]">
              {user?.email || ""}
            </p>
          </div>
          <ChevronDown size={14} className={`transition-transform ${open && "rotate-180"}`} />
        </button>

        {open && (
          <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden z-30">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {user?.name || "用户"}
              </p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
            <div className="py-1">
              <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left">
                <UserIcon size={14} />
                账号设置
              </button>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left"
              >
                <LogOut size={14} />
                退出登录
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
