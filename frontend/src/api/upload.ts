/**
 * 上传相关 API
 */
import apiClient from './index'

// 上传任务状态
export interface FileInfo {
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  rows?: number
  error?: string
}

export interface UploadTaskStatus {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  ifir_detail?: FileInfo
  ifir_row?: FileInfo
  ra_detail?: FileInfo
  ra_row?: FileInfo
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

/**
 * 上传文件
 */
export async function uploadFiles(files: {
  ifir_detail?: File
  ifir_row?: File
  ra_detail?: File
  ra_row?: File
}): Promise<UploadTaskStatus> {
  const formData = new FormData()
  
  if (files.ifir_detail) {
    formData.append('ifir_detail', files.ifir_detail)
  }
  if (files.ifir_row) {
    formData.append('ifir_row', files.ifir_row)
  }
  if (files.ra_detail) {
    formData.append('ra_detail', files.ra_detail)
  }
  if (files.ra_row) {
    formData.append('ra_row', files.ra_row)
  }
  
  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * 查询上传任务状态
 */
export async function getUploadStatus(taskId: string): Promise<UploadTaskStatus> {
  const response = await apiClient.get(`/upload/${taskId}/status`)
  return response.data
}
