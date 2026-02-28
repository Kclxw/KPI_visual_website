<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-icon class="collapse-btn" @click="$emit('toggle-sidebar')">
        <Fold v-if="!collapse" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <span class="app-title">KPI 可视化分析平台</span>
      <div class="user-area" v-if="authStore.user">
        <el-dropdown trigger="click">
          <span class="user-trigger">
            <el-avatar :size="28" :style="{ backgroundColor: avatarColor }">
              {{ userInitial }}
            </el-avatar>
            <span class="user-name">{{ displayName }}</span>
            <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="openPasswordDialog">修改密码</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </el-header>

  <el-dialog v-model="passwordDialogVisible" title="修改密码" width="420px">
    <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="90px">
      <el-form-item label="旧密码" prop="old_password">
        <el-input v-model="passwordForm.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="passwordForm.new_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm_password">
        <el-input v-model="passwordForm.confirm_password" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="passwordDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="passwordSubmitting" @click="submitPasswordChange">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Fold, Expand, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { changePassword } from '@/api/auth'

defineProps<{
  collapse: boolean
}>()

defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const route = useRoute()
const authStore = useAuthStore()

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title)
  return matched.map((item) => ({
    title: item.meta.title as string,
    path: item.path,
  }))
})

const displayName = computed(() => authStore.user?.display_name || authStore.user?.username || '')
const userInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())

const roleLabel = computed(() => {
  const role = authStore.user?.role
  if (role === 'admin') return '管理员'
  if (role === 'uploader') return '上传者'
  return '查看者'
})

const roleTagType = computed(() => {
  const role = authStore.user?.role
  if (role === 'admin') return 'danger'
  if (role === 'uploader') return 'warning'
  return 'info'
})

const avatarColor = computed(() => {
  const seed = (authStore.user?.username || 'user').split('').reduce((s, c) => s + c.charCodeAt(0), 0)
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
  return colors[seed % colors.length]
})

const passwordDialogVisible = ref(false)
const passwordSubmitting = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    {
      validator: (_: any, value: string, callback: (error?: Error) => void) => {
        if (!value) return callback()
        if (!/[A-Z]/.test(value)) return callback(new Error('密码需包含大写字母'))
        if (!/[a-z]/.test(value)) return callback(new Error('密码需包含小写字母'))
        if (!/[0-9]/.test(value)) return callback(new Error('密码需包含数字'))
        callback()
      },
      trigger: 'blur',
    },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_: any, value: string, callback: (error?: Error) => void) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const openPasswordDialog = () => {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordDialogVisible.value = true
}

const submitPasswordChange = async () => {
  const form = passwordFormRef.value
  if (!form) return
  await form.validate(async (valid) => {
    if (!valid) return
    passwordSubmitting.value = true
    try {
      await changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      })
      ElMessage.success('密码修改成功，请重新登录')
      passwordDialogVisible.value = false
      authStore.logout()
    } catch {
      // errors handled by interceptor
    } finally {
      passwordSubmitting.value = false
    }
  })
}

const handleLogout = () => {
  authStore.logout()
}
</script>

<style scoped lang="scss">
.app-header {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: var(--text-color-secondary);
  transition: color 0.2s;

  &:hover {
    color: var(--primary-color);
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;

  .app-title {
    font-size: 16px;
    font-weight: 500;
    color: var(--primary-color);
  }
}

.user-area {
  display: flex;
  align-items: center;
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-color);
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-breadcrumb) {
  font-size: 14px;
}
</style>
