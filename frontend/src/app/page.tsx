"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { useAuthStore } from "@/store/auth"

export default function RootPage() {
  const router = useRouter()
  const { token, isHydrated } = useAuthStore()

  useEffect(() => {
    if (!isHydrated) return
    router.replace(token ? "/chat" : "/login")
  }, [isHydrated, token, router])

  return (
    <div className="h-screen flex items-center justify-center text-gray-400">
      <Loader2 size={20} className="animate-spin mr-2" />
      正在加载...
    </div>
  )
}
