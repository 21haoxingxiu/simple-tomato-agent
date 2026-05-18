import { Sidebar } from "@/components/layout/Sidebar"
import { Header } from "@/components/layout/Header"
import { AuthGuard } from "@/components/auth/AuthGuard"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <Header />
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </div>
    </AuthGuard>
  )
}
