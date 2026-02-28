import apiClient from './index'
import type { UserInfo } from './auth'

export interface UserListData {
  items: UserInfo[]
  total: number
  page: number
  page_size: number
}

export async function listUsers(params: {
  q?: string
  role?: string
  page?: number
  page_size?: number
}): Promise<UserListData> {
  const response = await apiClient.get('/admin/users', { params })
  return response.data
}

export async function createUser(params: {
  username: string
  display_name: string
  email?: string
  password: string
  role: 'admin' | 'uploader' | 'viewer'
}): Promise<UserInfo> {
  const response = await apiClient.post('/admin/users', params)
  return response.data
}

export async function updateUser(
  id: number,
  params: {
    display_name?: string
    email?: string | null
    role?: 'admin' | 'uploader' | 'viewer'
    is_active?: boolean
  }
): Promise<UserInfo> {
  const response = await apiClient.put(`/admin/users/${id}`, params)
  return response.data
}

export async function deleteUser(id: number): Promise<UserInfo> {
  const response = await apiClient.delete(`/admin/users/${id}`)
  return response.data
}

export async function resetPassword(id: number, new_password: string): Promise<UserInfo> {
  const response = await apiClient.post(`/admin/users/${id}/reset-password`, {
    new_password,
  })
  return response.data
}
