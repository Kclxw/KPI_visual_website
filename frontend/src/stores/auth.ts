import { defineStore } from 'pinia'
import router from '@/router'
import { login as loginApi, getCurrentUser } from '@/api/auth'
import type { UserInfo } from '@/api/auth'

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

function readUser(): UserInfo | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as UserInfo
  } catch {
    return null
  }
}

function decodeToken(token: string): { exp?: number } | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => `%${('00' + c.charCodeAt(0).toString(16)).slice(-2)}`)
        .join('')
    )
    return JSON.parse(json)
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) as string | null,
    user: readUser() as UserInfo | null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    canUpload: (state) => state.user?.role === 'admin' || state.user?.role === 'uploader',
  },
  actions: {
    async login(username: string, password: string) {
      const data = await loginApi({ username, password })
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      if (router.currentRoute.value.name !== 'Login') {
        router.replace({ name: 'Login' })
      }
    },
    async fetchCurrentUser() {
      if (!this.token) return
      const user = await getCurrentUser()
      this.user = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    checkTokenValidity(): boolean {
      if (!this.token) return false
      const payload = decodeToken(this.token)
      if (!payload?.exp) return false
      const now = Math.floor(Date.now() / 1000)
      if (payload.exp <= now) {
        this.logout()
        return false
      }
      return true
    },
  },
})
