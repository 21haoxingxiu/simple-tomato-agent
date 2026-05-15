import { create } from "zustand"
import { persist } from "zustand/middleware"
import { authApi, setToken, clearToken } from "@/lib/api"

interface AuthState {
  token: string | null
  userId: string | null
  email: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  ensureToken: () => Promise<void>
}

const DEMO_EMAIL = "demo@agentstudio.io"
const DEMO_PASSWORD = "demo1234"

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      userId: null,
      email: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const res = await authApi.login(email, password)
          setToken(res.token)
          set({ token: res.token, userId: res.user_id, email: res.email, isLoading: false })
        } catch (err) {
          set({ isLoading: false })
          throw err
        }
      },

      logout: () => {
        clearToken()
        set({ token: null, userId: null, email: null })
      },

      // Auto-login with demo account if no token
      ensureToken: async () => {
        const state = get()
        if (state.token) {
          setToken(state.token)
          return
        }
        await get().login(DEMO_EMAIL, DEMO_PASSWORD)
      },
    }),
    { name: "auth-storage", partialize: (s) => ({ token: s.token, userId: s.userId, email: s.email }) }
  )
)
