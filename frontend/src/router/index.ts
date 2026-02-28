import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/LoginPage.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/components/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'upload',
        name: 'Upload',
        component: () => import('@/pages/upload/UploadPage.vue'),
        meta: { title: '数据上传', icon: 'Upload', requiresAuth: true, requiredRole: 'uploader' },
      },
      {
        path: 'kpi/ifir',
        name: 'IFIR',
        redirect: '/kpi/ifir/odm-analysis',
        meta: { title: 'IFIR分析', icon: 'DataAnalysis', requiresAuth: true },
        children: [
          {
            path: 'odm-analysis',
            name: 'IfirOdmAnalysis',
            component: () => import('@/pages/ifir/OdmAnalysisPage.vue'),
            meta: { title: 'ODM分析', requiresAuth: true },
          },
          {
            path: 'segment-analysis',
            name: 'IfirSegmentAnalysis',
            component: () => import('@/pages/ifir/SegmentAnalysisPage.vue'),
            meta: { title: 'Segment分析', requiresAuth: true },
          },
          {
            path: 'model-analysis',
            name: 'IfirModelAnalysis',
            component: () => import('@/pages/ifir/ModelAnalysisPage.vue'),
            meta: { title: 'Model分析', requiresAuth: true },
          },
        ],
      },
      {
        path: 'kpi/ra',
        name: 'RA',
        redirect: '/kpi/ra/odm-analysis',
        meta: { title: 'RA分析', icon: 'TrendCharts', requiresAuth: true },
        children: [
          {
            path: 'odm-analysis',
            name: 'RaOdmAnalysis',
            component: () => import('@/pages/ra/OdmAnalysisPage.vue'),
            meta: { title: 'ODM分析', requiresAuth: true },
          },
          {
            path: 'segment-analysis',
            name: 'RaSegmentAnalysis',
            component: () => import('@/pages/ra/SegmentAnalysisPage.vue'),
            meta: { title: 'Segment分析', requiresAuth: true },
          },
          {
            path: 'model-analysis',
            name: 'RaModelAnalysis',
            component: () => import('@/pages/ra/ModelAnalysisPage.vue'),
            meta: { title: 'Model分析', requiresAuth: true },
          },
        ],
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/pages/admin/UserManagePage.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', requiresAuth: true, requiredRole: 'admin' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const getDefaultPath = (role?: string) => {
  if (role === 'viewer') return '/kpi/ifir/odm-analysis'
  return '/upload'
}

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  if (to.name === 'Login' && authStore.isAuthenticated) {
    return next({ path: getDefaultPath(authStore.user?.role) })
  }

  if (to.meta.requiresAuth === false) {
    return next()
  }

  if (!authStore.isAuthenticated) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  if (!authStore.checkTokenValidity()) {
    return next({ name: 'Login' })
  }

  if (!authStore.user) {
    try {
      await authStore.fetchCurrentUser()
    } catch {
      return next({ name: 'Login' })
    }
  }

  if (to.path === '/' || to.name === 'Layout') {
    return next({ path: getDefaultPath(authStore.user?.role), replace: true })
  }

  if (to.meta.requiredRole === 'admin' && !authStore.isAdmin) {
    ElMessage.error('权限不足，需要管理员账号')
    return next(false)
  }
  if (to.meta.requiredRole === 'uploader' && !authStore.canUpload) {
    ElMessage.error('权限不足，需要上传权限')
    return next(false)
  }

  next()
})

export default router
