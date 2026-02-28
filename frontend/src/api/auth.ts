import apiClient from './index'

export interface UserInfo {
  id: number
  username: string
  display_name: string
  email?: string | null
  role: 'admin' | 'uploader' | 'viewer'
  is_active: boolean
  last_login?: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export async function login(params: {
  username: string
  password: string
}): Promise<TokenResponse> {
  const response = await apiClient.post('/auth/login', params)
  return response.data
}

export async function getCurrentUser(): Promise<UserInfo> {
  const response = await apiClient.get('/auth/me')
  return response.data
}

export async function changePassword(params: {
  old_password: string
  new_password: string
}): Promise<UserInfo> {
  const response = await apiClient.put('/auth/me/password', params)
  return response.data
}
