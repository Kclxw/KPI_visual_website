<template>
  <div class="page-container">
    <div class="page-header">
      <h1>用户管理</h1>
      <p class="description">管理系统用户、角色与权限</p>
    </div>

    <div class="toolbar">
      <div class="filters">
        <el-input
          v-model="filters.q"
          placeholder="搜索用户名/显示名"
          style="width: 220px"
          clearable
        />
        <el-select v-model="filters.role" placeholder="角色筛选" clearable style="width: 160px">
          <el-option label="管理员" value="admin" />
          <el-option label="上传者" value="uploader" />
          <el-option label="查看者" value="viewer" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
      <el-button type="primary" @click="openCreateDialog">新建用户</el-button>
    </div>

    <el-table :data="users" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="display_name" label="显示名" min-width="140" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login" label="最后登录" min-width="170">
        <template #default="{ row }">
          {{ formatDate(row.last_login) }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="120">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            :disabled="row.id === currentUserId"
            @change="handleStatusChange(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" @click="openResetDialog(row)">重置密码</el-button>
          <el-button size="small" type="danger" :disabled="row.id === currentUserId" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchUsers"
        @size-change="handlePageSizeChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新建用户' : '编辑用户'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="显示名" prop="display_name">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="上传者" value="uploader" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogMode === 'create'" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置密码" width="420px">
      <el-form ref="resetRef" :model="resetForm" :rules="resetRules" label-width="90px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="resetForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="handleResetPassword">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { listUsers, createUser, updateUser, deleteUser, resetPassword } from '@/api/admin'
import type { UserInfo } from '@/api/auth'

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

const filters = reactive({
  q: '',
  role: '',
})

const users = ref<UserInfo[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  id: 0,
  username: '',
  display_name: '',
  email: '',
  role: 'viewer' as 'admin' | 'uploader' | 'viewer',
  password: '',
})

const resetVisible = ref(false)
const resetting = ref(false)
const resetRef = ref<FormInstance>()
const resetForm = reactive({
  id: 0,
  new_password: '',
  confirm_password: '',
})

const validatePassword = (_: any, value: string, callback: (error?: Error) => void) => {
  if (dialogMode.value !== 'create') {
    callback()
    return
  }
  if (!value) {
    callback(new Error('请输入密码'))
    return
  }
  if (value.length < 8) {
    callback(new Error('密码长度至少8位'))
    return
  }
  if (!/[A-Z]/.test(value)) {
    callback(new Error('密码需包含大写字母'))
    return
  }
  if (!/[a-z]/.test(value)) {
    callback(new Error('密码需包含小写字母'))
    return
  }
  if (!/[0-9]/.test(value)) {
    callback(new Error('密码需包含数字'))
    return
  }
  callback()
}

const validateEmail = (_: any, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback()
    return
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(value)) {
    callback(new Error('请输入正确邮箱'))
    return
  }
  callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]{3,50}$/, message: '用户名需为3-50位字母数字下划线', trigger: 'blur' },
  ],
  display_name: [{ required: true, message: '请输入显示名', trigger: 'blur' }],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ validator: validatePassword, trigger: 'blur' }],
}

const resetRules = {
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
        if (value !== resetForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const roleLabel = (role: string) => {
  if (role === 'admin') return '管理员'
  if (role === 'uploader') return '上传者'
  return '查看者'
}

const roleTagType = (role: string) => {
  if (role === 'admin') return 'danger'
  if (role === 'uploader') return 'warning'
  return 'info'
}

const formatDate = (value?: string | null) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const data = await listUsers({
      q: filters.q || undefined,
      role: filters.role || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    users.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  fetchUsers()
}

const handlePageSizeChange = () => {
  page.value = 1
  fetchUsers()
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  form.id = 0
  form.username = ''
  form.display_name = ''
  form.email = ''
  form.role = 'viewer'
  form.password = ''
  dialogVisible.value = true
}

const openEditDialog = (row: UserInfo) => {
  dialogMode.value = 'edit'
  form.id = row.id
  form.username = row.username
  form.display_name = row.display_name
  form.email = row.email || ''
  form.role = row.role
  form.password = ''
  dialogVisible.value = true
}

const handleSave = async () => {
  const formIns = formRef.value
  if (!formIns) return
  await formIns.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (dialogMode.value === 'create') {
        await createUser({
          username: form.username,
          display_name: form.display_name,
          email: form.email || undefined,
          password: form.password,
          role: form.role,
        })
        ElMessage.success('创建成功')
      } else {
        await updateUser(form.id, {
          display_name: form.display_name,
          email: form.email || undefined,
          role: form.role,
        })
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      fetchUsers()
    } finally {
      saving.value = false
    }
  })
}

const handleDelete = async (row: UserInfo) => {
  await ElMessageBox.confirm(`确认删除用户 ${row.username} 吗？`, '提示', {
    type: 'warning',
  })
  try {
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {
    ElMessage.error('删除失败')
  }
}

const handleStatusChange = async (row: UserInfo) => {
  try {
    await updateUser(row.id, { is_active: row.is_active })
    ElMessage.success('状态已更新')
  } catch {
    // 回滚开关状态
    row.is_active = !row.is_active
    ElMessage.error('状态更新失败')
  }
}

const openResetDialog = (row: UserInfo) => {
  resetForm.id = row.id
  resetForm.new_password = ''
  resetForm.confirm_password = ''
  resetVisible.value = true
}

const handleResetPassword = async () => {
  const formIns = resetRef.value
  if (!formIns) return
  await formIns.validate(async (valid) => {
    if (!valid) return
    resetting.value = true
    try {
      await resetPassword(resetForm.id, resetForm.new_password)
      ElMessage.success('密码已重置')
      resetVisible.value = false
    } finally {
      resetting.value = false
    }
  })
}

fetchUsers()
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 12px;

  h1 {
    margin: 0 0 4px 0;
    font-size: 20px;
  }

  .description {
    margin: 0;
    color: var(--text-color-secondary);
    font-size: 13px;
  }
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
