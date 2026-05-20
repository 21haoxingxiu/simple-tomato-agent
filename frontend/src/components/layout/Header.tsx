"use client"

import { useState, useRef, useEffect } from "react"
import { ChevronDown, LogOut, Search, User as UserIcon, Settings, HelpCircle, X } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { WorkspaceSelector } from "./WorkspaceSelector"
import { useAuthStore } from "@/store/auth"
import { useWorkspaceStore } from "@/store/workspace"
import { searchApi, SearchResult } from "@/lib/api/search"

export function Header() {
  const router = useRouter()
  const { user, logout } = useAuthStore()
  const resetWorkspaces = useWorkspaceStore((s) => s.reset)

  const [open, setOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null)
  const [searching, setSearching] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
      if (!searchRef.current?.contains(e.target as Node)) setSearchOpen(false)
    }
    window.addEventListener("mousedown", onClick)
    return () => window.removeEventListener("mousedown", onClick)
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setSearchOpen(true)
        setTimeout(() => searchInputRef.current?.focus(), 100)
      }
      if (e.key === "Escape") {
        setSearchOpen(false)
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }
    const timer = setTimeout(async () => {
      setSearching(true)
      try {
        const results = await searchApi.search(searchQuery)
        setSearchResults(results)
      } catch (e) {
        console.error("Search failed:", e)
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  function handleLogout() {
    logout()
    resetWorkspaces()
    router.replace("/login")
  }

  const initial = (user?.name || user?.email || "?")[0]?.toUpperCase() || "?"

  return (
    <header className="h-16 bg-indigo-700 flex items-center px-4 gap-4 shrink-0 shadow-md">
      <WorkspaceSelector />

      <div className="flex-1 max-w-md hidden sm:flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2 border border-white/20 cursor-pointer" onClick={() => { setSearchOpen(true); setTimeout(() => searchInputRef.current?.focus(), 100) }}>
        <Search size={16} className="text-white/60" />
        <span className="text-sm text-white/50 flex-1">搜索知识库、会话...</span>
        <kbd className="text-xs text-white/40 bg-white/10 px-1.5 py-0.5 rounded hidden md:block">
          ⌘K
        </kbd>
      </div>

      <div className="flex-1" />

      {/* Settings & Help buttons */}
      <Link
        href="/settings"
        className="w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
        title="设置"
      >
        <Settings size={18} />
      </Link>
      <Link
        href="/help"
        className="w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
        title="帮助"
      >
        <HelpCircle size={18} />
      </Link>

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
              <Link
                href="/settings/profile"
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left"
                onClick={() => setOpen(false)}
              >
                <UserIcon size={14} />
                账号设置
              </Link>
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

      {/* Search Modal */}
      {searchOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-[15vh]">
          <div ref={searchRef} className="w-full max-w-xl bg-white rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
              <Search size={20} className="text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索知识库、会话..."
                className="flex-1 text-lg outline-none text-gray-900 placeholder-gray-400"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery("")} className="text-gray-400 hover:text-gray-600">
                  <X size={18} />
                </button>
              )}
              <kbd className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">ESC</kbd>
            </div>

            <div className="max-h-[60vh] overflow-y-auto">
              {searching && (
                <div className="px-4 py-8 text-center text-gray-500">
                  搜索中...
                </div>
              )}

              {!searching && searchQuery && !searchResults && (
                <div className="px-4 py-8 text-center text-gray-500">
                  输入关键词开始搜索
                </div>
              )}

              {!searching && searchResults && (
                <>
                  {searchResults.knowledge_bases.length === 0 && searchResults.conversations.length === 0 && searchResults.documents.length === 0 ? (
                    <div className="px-4 py-8 text-center text-gray-500">
                      未找到相关结果
                    </div>
                  ) : (
                    <div className="py-2">
                      {searchResults.knowledge_bases.length > 0 && (
                        <div>
                          <p className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">知识库</p>
                          {searchResults.knowledge_bases.map((kb) => (
                            <Link
                              key={kb.id}
                              href={`/knowledge/${kb.id}`}
                              onClick={() => setSearchOpen(false)}
                              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 cursor-pointer"
                            >
                              <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">
                                {kb.name[0]}
                              </div>
                              <div>
                                <p className="text-sm font-medium text-gray-900">{kb.name}</p>
                                <p className="text-xs text-gray-500">{kb.doc_count} 文档</p>
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}

                      {searchResults.conversations.length > 0 && (
                        <div>
                          <p className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase border-t border-gray-100 mt-1">会话</p>
                          {searchResults.conversations.map((conv) => (
                            <Link
                              key={conv.id}
                              href={`/chat?conversation=${conv.id}`}
                              onClick={() => setSearchOpen(false)}
                              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 cursor-pointer"
                            >
                              <div className="w-8 h-8 rounded-lg bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium">
                                {conv.title?.[0] || "C"}
                              </div>
                              <div>
                                <p className="text-sm font-medium text-gray-900">{conv.title || "未命名会话"}</p>
                                <p className="text-xs text-gray-500 truncate max-w-xs">{conv.last_message || "无消息"}</p>
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}

                      {searchResults.documents.length > 0 && (
                        <div>
                          <p className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase border-t border-gray-100 mt-1">文档</p>
                          {searchResults.documents.map((doc) => (
                            <Link
                              key={doc.id}
                              href={`/knowledge/${doc.kb_id}`}
                              onClick={() => setSearchOpen(false)}
                              className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 cursor-pointer"
                            >
                              <div className="w-8 h-8 rounded-lg bg-orange-100 text-orange-600 flex items-center justify-center text-sm font-medium">
                                {doc.filename.split('.').pop()?.toUpperCase() || "D"}
                              </div>
                              <div>
                                <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                                <p className="text-xs text-gray-500">{doc.status}</p>
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {!searchQuery && (
                <div className="px-4 py-8 text-center text-gray-500">
                  输入关键词搜索知识库和会话
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
