/**
 * API 基础配置
 */
import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { getActivePinia } from 'pinia'

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动附加 Token
apiClient.interceptors.request.use(async (config) => {
  const pinia = getActivePinia()
  if (pinia) {
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore(pinia)
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
  }
  return config
})

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    if (data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  async (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '网络错误'
    if (status === 422) {
      const detail = error.response?.data?.detail
      let detailMessage = '参数校验失败'
      if (Array.isArray(detail) && detail.length) {
        detailMessage = detail.map((item) => item.msg).join('；')
      } else if (typeof detail === 'string') {
        detailMessage = detail
      }
      ElMessage.error(detailMessage)
      return Promise.reject(error)
    }
    if (status === 401) {
      const pinia = getActivePinia()
      if (pinia) {
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore(pinia)
        authStore.logout()
      }
      ElMessage.error(message)
      return Promise.reject(error)
    }
    if (status === 403) {
      ElMessage.error('权限不足')
      return Promise.reject(error)
    }
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default apiClient

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}
