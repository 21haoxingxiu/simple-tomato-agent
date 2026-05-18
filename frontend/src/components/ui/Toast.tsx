"use client"

import { create } from "zustand"
import { CheckCircle, AlertCircle, X, Info } from "lucide-react"
import { useEffect } from "react"
import clsx from "clsx"

type ToastKind = "success" | "error" | "info"

interface Toast {
  id: number
  kind: ToastKind
  message: string
}

interface ToastStore {
  toasts: Toast[]
  push: (kind: ToastKind, message: string) => void
  remove: (id: number) => void
}

let _id = 0

const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  push: (kind, message) => {
    const id = ++_id
    set((s) => ({ toasts: [...s.toasts, { id, kind, message }] }))
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
    }, 3800)
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

export const toast = {
  success: (msg: string) => useToastStore.getState().push("success", msg),
  error: (msg: string) => useToastStore.getState().push("error", msg),
  info: (msg: string) => useToastStore.getState().push("info", msg),
}

const ICONS = {
  success: <CheckCircle size={18} className="text-green-500" />,
  error: <AlertCircle size={18} className="text-red-500" />,
  info: <Info size={18} className="text-indigo-500" />,
}

export function ToastContainer() {
  const { toasts, remove } = useToastStore()
  useEffect(() => {
    /* noop, keeps subscription live */
  }, [toasts])

  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={clsx(
            "pointer-events-auto flex items-start gap-2 px-4 py-3 rounded-xl shadow-lg border bg-white",
            t.kind === "error" && "border-red-200",
            t.kind === "success" && "border-green-200",
            t.kind === "info" && "border-indigo-200"
          )}
        >
          <span className="mt-0.5 shrink-0">{ICONS[t.kind]}</span>
          <span className="text-sm text-gray-800 flex-1">{t.message}</span>
          <button
            onClick={() => remove(t.id)}
            className="text-gray-400 hover:text-gray-700"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
