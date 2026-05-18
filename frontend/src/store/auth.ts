"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"
import { ApiError, authApi, clearToken, setToken, type UserInfo } from "@/lib/api"

interface AuthState {
  token: string | null
  user: UserInfo | null
  isLoading: boolean
  isHydrated: boolean
  setHydrated: () => void
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => void
  /** 用本地 token 验证当前会话;失败时清空,返回是否仍在登录 */
  verify: () => Promise<boolean>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: false,
      isHydrated: false,

      setHydrated: () => set({ isHydrated: true }),

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const res = await authApi.login(email.trim(), password)
          setToken(res.token)
          set({ token: res.token, user: res.user, isLoading: false })
        } catch (err) {
          set({ isLoading: false })
          throw err
        }
      },

      register: async (email, password, name) => {
        set({ isLoading: true })
        try {
          const res = await authApi.register(email.trim(), password, name?.trim())
          setToken(res.token)
          set({ token: res.token, user: res.user, isLoading: false })
        } catch (err) {
          set({ isLoading: false })
          throw err
        }
      },

      logout: () => {
        clearToken()
        set({ token: null, user: null })
      },

      verify: async () => {
        const { token } = get()
        if (!token) {
          clearToken()
          return false
        }
        setToken(token)
        try {
          const user = await authApi.me()
          set({ user })
          return true
        } catch (err) {
          if (err instanceof ApiError && err.status === 401) {
            clearToken()
            set({ token: null, user: null })
          }
          return false
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (s) => ({ token: s.token, user: s.user }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated()
      },
    }
  )
)
