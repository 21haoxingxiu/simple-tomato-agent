"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Bot, Loader2, Mail, Lock, User as UserIcon, AlertCircle } from "lucide-react"
import { useAuthStore } from "@/store/auth"
import { useWorkspaceStore } from "@/store/workspace"
import { ApiError } from "@/lib/api"

export default function RegisterPage() {
  const router = useRouter()
  const params = useSearchParams()
  const next = params.get("next") || "/chat"

  const { register, isLoading } = useAuthStore()
  const refreshWorkspaces = useWorkspaceStore((s) => s.refresh)

  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("请输入有效邮箱")
      return
    }
    if (password.length < 6) {
      setError("密码至少 6 位")
      return
    }
    if (password !== confirm) {
      setError("两次输入的密码不一致")
      return
    }

    try {
      await register(email, password, name || undefined)
      await refreshWorkspaces()
      router.replace(next)
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "注册失败"
      setError(msg)
    }
  }

  return (
    <div className="bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/60 p-8">
      <div className="flex flex-col items-center mb-6">
        <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center mb-3 shadow-lg shadow-indigo-600/30">
          <Bot size={24} className="text-white" />
        </div>
        <h1 className="text-xl font-bold text-gray-900">创建 AgentStudio 账号</h1>
        <p className="text-sm text-gray-500 mt-1">几秒钟即可开始</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Field
          icon={<Mail size={16} />}
          type="email"
          placeholder="邮箱"
          value={email}
          onChange={setEmail}
          autoFocus
          autoComplete="email"
        />
        <Field
          icon={<UserIcon size={16} />}
          type="text"
          placeholder="昵称(可选)"
          value={name}
          onChange={setName}
          autoComplete="name"
        />
        <Field
          icon={<Lock size={16} />}
          type="password"
          placeholder="密码(至少 6 位)"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
        />
        <Field
          icon={<Lock size={16} />}
          type="password"
          placeholder="再输入一次密码"
          value={confirm}
          onChange={setConfirm}
          autoComplete="new-password"
        />

        {error && (
          <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : null}
          {isLoading ? "注册中..." : "注册并登录"}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-500">
        已有账号?{" "}
        <Link
          href={`/login${next !== "/chat" ? `?next=${encodeURIComponent(next)}` : ""}`}
          className="text-indigo-600 font-medium hover:underline"
        >
          直接登录
        </Link>
      </div>
    </div>
  )
}

interface FieldProps {
  icon: React.ReactNode
  type: "email" | "password" | "text"
  placeholder: string
  value: string
  onChange: (v: string) => void
  autoFocus?: boolean
  autoComplete?: string
}

function Field({ icon, type, placeholder, value, onChange, autoFocus, autoComplete }: FieldProps) {
  return (
    <label className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
      <span className="text-gray-400">{icon}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        autoComplete={autoComplete}
        className="flex-1 bg-transparent outline-none text-sm text-gray-800 placeholder-gray-400"
      />
    </label>
  )
}
