"use client"

import { useEffect } from "react"
import { X } from "lucide-react"

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  footer?: React.ReactNode
  size?: "sm" | "md" | "lg"
}

const SIZE: Record<NonNullable<ModalProps["size"]>, string> = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-3xl",
}

export function Modal({ open, onClose, title, children, footer, size = "md" }: ModalProps) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className={`relative bg-white rounded-2xl shadow-2xl w-full ${SIZE[size]} max-h-[85vh] flex flex-col`}
      >
        {(title || true) && (
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">{title}</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-700 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
        {footer && (
          <div className="px-5 py-3 border-t border-gray-100 bg-gray-50 rounded-b-2xl flex justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
