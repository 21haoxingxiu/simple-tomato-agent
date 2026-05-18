import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "AgentStudio - 登录",
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen relative overflow-hidden flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4 py-12">
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 20%, #6366f1aa 0, transparent 35%), radial-gradient(circle at 80% 60%, #a855f7aa 0, transparent 35%)",
        }}
      />
      <div className="relative z-10 w-full max-w-md">{children}</div>
    </div>
  )
}
