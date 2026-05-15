import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { Workspace } from "@/types"

const DEFAULT_WORKSPACES: Workspace[] = [
  { id: "ws-1", name: "默认工作区", description: "通用 AI 助手", createdAt: new Date().toISOString() },
  { id: "ws-2", name: "研发工作区", description: "代码助手与技术问答", createdAt: new Date().toISOString() },
  { id: "ws-3", name: "客服工作区", description: "客户支持与知识库", createdAt: new Date().toISOString() },
]

interface WorkspaceStore {
  workspaces: Workspace[]
  activeWorkspaceId: string
  setActiveWorkspace: (id: string) => void
  addWorkspace: (workspace: Workspace) => void
}

export const useWorkspaceStore = create<WorkspaceStore>()(
  persist(
    (set) => ({
      workspaces: DEFAULT_WORKSPACES,
      activeWorkspaceId: DEFAULT_WORKSPACES[0].id,
      setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),
      addWorkspace: (workspace) =>
        set((state) => ({ workspaces: [...state.workspaces, workspace] })),
    }),
    { name: "workspace-storage" }
  )
)
