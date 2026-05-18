import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ToastContainer } from "@/components/ui/Toast"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "AgentStudio - AI 智能体平台",
  description: "构建、管理和评测企业级 AI 智能体 (RAG · GraphRAG · 多路召回 · 评测 · 语音)",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={`${inter.className} antialiased`}>
        {children}
        <ToastContainer />
      </body>
    </html>
  )
}
