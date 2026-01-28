<template>
  <div class="page-container">
    <div class="page-header">
      <h1>数据上传</h1>
      <p class="description">上传Excel数据文件进行分析</p>
    </div>
    
    <div class="upload-section">
      <el-card class="upload-card">
        <template #header>
          <div class="card-header">
            <span>请上传以下四个Excel文件（至少选择一个）</span>
          </div>
        </template>
        
        <div class="upload-grid">
          <div class="upload-item">
            <el-upload
              ref="ifirDetailRef"
              class="uploader"
              drag
              action="#"
              :auto-upload="false"
              accept=".xlsx,.xls"
              :limit="1"
              :on-change="(file: any) => handleFileChange('ifir_detail', file)"
              :on-remove="() => handleFileRemove('ifir_detail')"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                <strong>IFIR Detail</strong>
                <p>拖拽文件到此处或点击上传</p>
              </div>
            </el-upload>
            <div v-if="taskStatus?.ifir_detail" class="file-status">
              <el-tag :type="getStatusType(taskStatus.ifir_detail.status)">
                {{ getStatusText(taskStatus.ifir_detail.status) }}
              </el-tag>
              <span v-if="taskStatus.ifir_detail.rows">
                {{ taskStatus.ifir_detail.rows }} 行
              </span>
            </div>
          </div>
          
          <div class="upload-item">
            <el-upload
              ref="ifirRowRef"
              class="uploader"
              drag
              action="#"
              :auto-upload="false"
              accept=".xlsx,.xls"
              :limit="1"
              :on-change="(file: any) => handleFileChange('ifir_row', file)"
              :on-remove="() => handleFileRemove('ifir_row')"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                <strong>IFIR Row</strong>
                <p>拖拽文件到此处或点击上传</p>
              </div>
            </el-upload>
            <div v-if="taskStatus?.ifir_row" class="file-status">
              <el-tag :type="getStatusType(taskStatus.ifir_row.status)">
                {{ getStatusText(taskStatus.ifir_row.status) }}
              </el-tag>
              <span v-if="taskStatus.ifir_row.rows">
                {{ taskStatus.ifir_row.rows }} 行
              </span>
            </div>
          </div>
          
          <div class="upload-item">
            <el-upload
              ref="raDetailRef"
              class="uploader"
              drag
              action="#"
              :auto-upload="false"
              accept=".xlsx,.xls"
              :limit="1"
              :on-change="(file: any) => handleFileChange('ra_detail', file)"
              :on-remove="() => handleFileRemove('ra_detail')"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                <strong>RA Detail</strong>
                <p>拖拽文件到此处或点击上传</p>
              </div>
            </el-upload>
            <div v-if="taskStatus?.ra_detail" class="file-status">
              <el-tag :type="getStatusType(taskStatus.ra_detail.status)">
                {{ getStatusText(taskStatus.ra_detail.status) }}
              </el-tag>
              <span v-if="taskStatus.ra_detail.rows">
                {{ taskStatus.ra_detail.rows }} 行
              </span>
            </div>
          </div>
          
          <div class="upload-item">
            <el-upload
              ref="raRowRef"
              class="uploader"
              drag
              action="#"
              :auto-upload="false"
              accept=".xlsx,.xls"
              :limit="1"
              :on-change="(file: any) => handleFileChange('ra_row', file)"
              :on-remove="() => handleFileRemove('ra_row')"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                <strong>RA Row</strong>
                <p>拖拽文件到此处或点击上传</p>
              </div>
            </el-upload>
            <div v-if="taskStatus?.ra_row" class="file-status">
              <el-tag :type="getStatusType(taskStatus.ra_row.status)">
                {{ getStatusText(taskStatus.ra_row.status) }}
              </el-tag>
              <span v-if="taskStatus.ra_row.rows">
                {{ taskStatus.ra_row.rows }} 行
              </span>
            </div>
          </div>
        </div>
        
        <!-- 进度条 -->
        <div v-if="taskStatus && taskStatus.status !== 'completed'" class="progress-section">
          <el-progress 
            :percentage="taskStatus.progress" 
            :status="taskStatus.status === 'failed' ? 'exception' : undefined"
          />
          <p class="progress-text">
            {{ getOverallStatusText(taskStatus.status) }}
          </p>
        </div>
        
        <!-- 完成提示 -->
        <el-alert
          v-if="taskStatus?.status === 'completed'"
          title="上传完成"
          type="success"
          :description="`数据已成功导入数据库，可以进行分析了`"
          show-icon
          class="complete-alert"
        />
        
        <!-- 错误提示 -->
        <el-alert
          v-if="taskStatus?.status === 'failed'"
          title="上传失败"
          type="error"
          :description="taskStatus.error_message || '处理过程中发生错误'"
          show-icon
          class="error-alert"
        />
        
        <div class="upload-actions">
          <el-button 
            type="primary" 
            size="large" 
            :icon="Upload"
            :loading="uploading"
            :disabled="!hasFiles"
            @click="handleUpload"
          >
            {{ uploading ? '处理中...' : '开始上传并处理' }}
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { uploadFiles, getUploadStatus, type UploadTaskStatus } from '@/api/upload'
import { ElMessage } from 'element-plus'

// 文件引用
const files = ref<{
  ifir_detail?: File
  ifir_row?: File
  ra_detail?: File
  ra_row?: File
}>({})

// 上传状态
const uploading = ref(false)
const taskStatus = ref<UploadTaskStatus | null>(null)

// 是否有文件
const hasFiles = computed(() => {
  return Object.values(files.value).some(f => f !== undefined)
})

// 文件变更
const handleFileChange = (type: string, uploadFile: any) => {
  if (uploadFile?.raw) {
    (files.value as any)[type] = uploadFile.raw
  }
}

// 文件移除
const handleFileRemove = (type: string) => {
  (files.value as any)[type] = undefined
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'processing': return 'warning'
    default: return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '完成'
    case 'failed': return '失败'
    case 'processing': return '处理中'
    case 'pending': return '等待中'
    default: return status
  }
}

// 获取整体状态文本
const getOverallStatusText = (status: string) => {
  switch (status) {
    case 'queued': return '任务已提交，等待处理...'
    case 'processing': return '正在处理数据...'
    case 'completed': return '处理完成！'
    case 'failed': return '处理失败'
    default: return ''
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: string) => {
  try {
    const status = await getUploadStatus(taskId)
    taskStatus.value = status
    
    if (status.status === 'queued' || status.status === 'processing') {
      // 继续轮询
      setTimeout(() => pollTaskStatus(taskId), 1000)
    } else {
      uploading.value = false
      if (status.status === 'completed') {
        ElMessage.success('数据上传处理完成！')
      }
    }
  } catch (error) {
    uploading.value = false
  }
}

// 上传处理
const handleUpload = async () => {
  if (!hasFiles.value) {
    ElMessage.warning('请至少选择一个文件')
    return
  }
  
  uploading.value = true
  taskStatus.value = null
  
  try {
    const result = await uploadFiles(files.value)
    taskStatus.value = result
    
    // 开始轮询状态
    if (result.task_id) {
      pollTaskStatus(result.task_id)
    }
  } catch (error) {
    uploading.value = false
    ElMessage.error('上传失败，请重试')
  }
}
</script>

<style scoped lang="scss">
.upload-section {
  max-width: 1200px;
}

.upload-card {
  :deep(.el-card__header) {
    background: #f5f7fa;
  }
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.upload-item {
  .uploader {
    width: 100%;
    
    :deep(.el-upload) {
      width: 100%;
    }
    
    :deep(.el-upload-dragger) {
      width: 100%;
      height: 160px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
  }
  
  .el-upload__text {
    strong {
      display: block;
      font-size: 16px;
      color: var(--text-color);
      margin-bottom: 8px;
    }
    
    p {
      font-size: 12px;
      color: var(--text-color-secondary);
    }
  }
  
  .file-status {
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-color-secondary);
  }
}

.progress-section {
  margin-bottom: 20px;
  
  .progress-text {
    margin-top: 8px;
    text-align: center;
    color: var(--text-color-secondary);
    font-size: 14px;
  }
}

.complete-alert,
.error-alert {
  margin-bottom: 20px;
}

.upload-actions {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}
</style>
