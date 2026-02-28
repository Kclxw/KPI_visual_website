<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <h1>KPI 可视化分析平台</h1>
        <p>请使用账号密码登录系统</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const getDefaultPath = (role?: string) => {
  if (role === 'viewer') return '/kpi/ifir/odm-analysis'
  return '/upload'
}

const handleLogin = async () => {
  const formIns = formRef.value
  if (!formIns) return
  await formIns.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.username, form.password)
      const redirect = (route.query.redirect as string) || getDefaultPath(authStore.user?.role)
      router.replace(redirect)
    } catch (error: any) {
      ElMessage.error(error?.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f1ff 0%, #f6fbff 50%, #ffffff 100%);
  padding: 20px;
}

.login-card {
  width: 380px;
  background: #fff;
  border-radius: 12px;
  padding: 32px 28px;
  box-shadow: 0 10px 30px rgba(64, 158, 255, 0.15);
}

.brand {
  text-align: center;
  margin-bottom: 24px;

  h1 {
    font-size: 20px;
    margin: 0 0 6px 0;
    color: #2c3e50;
  }

  p {
    margin: 0;
    font-size: 12px;
    color: #909399;
  }
}

.login-btn {
  width: 100%;
  margin-top: 6px;
}
</style>
