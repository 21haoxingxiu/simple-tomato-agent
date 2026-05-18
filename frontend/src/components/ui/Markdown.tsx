"use client"

import { useMemo } from "react"
import { renderMarkdown } from "@/lib/markdown"

interface MarkdownProps {
  content: string
  onCiteClick?: (index: number) => void
  className?: string
}

export function Markdown({ content, onCiteClick, className }: MarkdownProps) {
  const html = useMemo(() => renderMarkdown(content), [content])

  function handleClick(e: React.MouseEvent<HTMLDivElement>) {
    if (!onCiteClick) return
    const target = e.target as HTMLElement
    if (target.classList.contains("md-cite")) {
      const idx = Number(target.dataset.idx)
      if (Number.isFinite(idx)) onCiteClick(idx)
    }
  }

  return (
    <div
      className={`md-body ${className ?? ""}`}
      onClick={handleClick}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
