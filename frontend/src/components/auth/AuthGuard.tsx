"use client"

import { useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { useAuthStore } from "@/store/auth"
import { useWorkspaceStore } from "@/store/workspace"

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { token, isHydrated, verify } = useAuthStore()
  const refreshWorkspaces = useWorkspaceStore((s) => s.refresh)
  const resetWorkspaces = useWorkspaceStore((s) => s.reset)

  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!isHydrated) return

    let cancelled = false
    ;(async () => {
      if (!token) {
        resetWorkspaces()
        const next = encodeURIComponent(pathname || "/chat")
        router.replace(`/login?next=${next}`)
        if (!cancelled) setChecking(false)
        return
      }

      const ok = await verify()
      if (cancelled) return
      if (!ok) {
        resetWorkspaces()
        const next = encodeURIComponent(pathname || "/chat")
        router.replace(`/login?next=${next}`)
        setChecking(false)
        return
      }
      await refreshWorkspaces()
      setChecking(false)
    })()

    return () => {
      cancelled = true
    }
  }, [isHydrated, token, pathname, router, verify, refreshWorkspaces, resetWorkspaces])

  if (!isHydrated || checking) {
    return (
      <div className="h-screen flex items-center justify-center text-gray-400">
        <Loader2 size={20} className="animate-spin mr-2" />
        正在加载...
      </div>
    )
  }

  if (!token) return null
  return <>{children}</>
}
