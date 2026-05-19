"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"
import { workspaceApi } from "@/lib/api"

export interface Workspace {
  id: string
  name: string
  description?: string
  createdAt?: string
}

interface WorkspaceStore {
  workspaces: Workspace[]
  activeWorkspaceId: string
  setActiveWorkspace: (id: string) => void
  setWorkspaces: (list: Workspace[]) => void
  reset: () => void
  refresh: () => Promise<void>
}

export const useWorkspaceStore = create<WorkspaceStore>()(
  persist(
    (set, get) => ({
      workspaces: [],
      activeWorkspaceId: "",

      setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),

      setWorkspaces: (list) => {
        const current = get().activeWorkspaceId
        const exists = list.some((w) => w.id === current)
        set({
          workspaces: list,
          activeWorkspaceId: exists ? current : list[0]?.id ?? "",
        })
      },

      reset: () => set({ workspaces: [], activeWorkspaceId: "" }),

      refresh: async () => {
        try {
          const list = await workspaceApi.list()
          get().setWorkspaces(
            list.map((w) => ({
              id: w.id,
              name: w.name,
              description: w.description,
              createdAt: w.created_at,
            }))
          )
        } catch {
          /* silent: 未登录或离线 */
        }
      },
    }),
    {
      name: "workspace-storage",
      partialize: (s) => ({
        workspaces: s.workspaces,
        activeWorkspaceId: s.activeWorkspaceId,
      }),
    }
  )
)
