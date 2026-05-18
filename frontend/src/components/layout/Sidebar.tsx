"use client"

import Link from "next/link"
import { useRouter, usePathname } from "next/navigation"
import {
  BookOpen,
  MessageSquare,
  FlaskConical,
  Bot,
  Settings,
  HelpCircle,
  LogOut,
} from "lucide-react"
import clsx from "clsx"
import { useAuthStore } from "@/store/auth"
import { useWorkspaceStore } from "@/store/workspace"

const NAV_ITEMS = [
  { href: "/knowledge", icon: BookOpen, label: "知识库" },
  { href: "/chat", icon: MessageSquare, label: "会话聊天" },
  { href: "/eval", icon: FlaskConical, label: "评测" },
]

const BOTTOM_ITEMS = [
  { href: "/settings", icon: Settings, label: "设置" },
  { href: "/help", icon: HelpCircle, label: "帮助" },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuthStore()
  const resetWorkspaces = useWorkspaceStore((s) => s.reset)

  function handleLogout() {
    logout()
    resetWorkspaces()
    router.replace("/login")
  }

  const initial = (user?.name || user?.email || "?")[0]?.toUpperCase() || "?"

  return (
    <aside className="w-16 lg:w-56 flex flex-col bg-gray-900 text-white shrink-0 h-full">
      <div className="h-16 flex items-center px-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
            <Bot size={18} />
          </div>
          <span className="font-bold text-sm hidden lg:block">AgentStudio</span>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2 hidden lg:block">
          功能
        </p>
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || pathname.startsWith(href + "/")
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium",
                active
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-gray-400 hover:text-white hover:bg-white/10"
              )}
            >
              <Icon size={18} className="shrink-0" />
              <span className="hidden lg:block">{label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-3 border-t border-white/10 space-y-1">
        {BOTTOM_ITEMS.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all text-sm"
          >
            <Icon size={18} className="shrink-0" />
            <span className="hidden lg:block">{label}</span>
          </Link>
        ))}

        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg mt-2 group">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold shrink-0">
            {initial}
          </div>
          <div className="hidden lg:block min-w-0 flex-1">
            <p className="text-sm font-medium text-white truncate">
              {user?.name || "未登录"}
            </p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            title="退出"
            className="hidden lg:inline-flex text-gray-400 hover:text-red-400 transition-colors"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  )
}
