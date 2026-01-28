import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/components/layout/MainLayout.vue'),
    redirect: '/upload',
    children: [
      {
        path: 'upload',
        name: 'Upload',
        component: () => import('@/pages/upload/UploadPage.vue'),
        meta: { title: '数据上传', icon: 'Upload' },
      },
      {
        path: 'kpi/ifir',
        name: 'IFIR',
        redirect: '/kpi/ifir/odm-analysis',
        meta: { title: 'IFIR分析', icon: 'DataAnalysis' },
        children: [
          {
            path: 'odm-analysis',
            name: 'IfirOdmAnalysis',
            component: () => import('@/pages/ifir/OdmAnalysisPage.vue'),
            meta: { title: 'ODM分析' },
          },
          {
            path: 'segment-analysis',
            name: 'IfirSegmentAnalysis',
            component: () => import('@/pages/ifir/SegmentAnalysisPage.vue'),
            meta: { title: 'Segment分析' },
          },
          {
            path: 'model-analysis',
            name: 'IfirModelAnalysis',
            component: () => import('@/pages/ifir/ModelAnalysisPage.vue'),
            meta: { title: 'Model分析' },
          },
        ],
      },
      {
        path: 'kpi/ra',
        name: 'RA',
        redirect: '/kpi/ra/odm-analysis',
        meta: { title: 'RA分析', icon: 'TrendCharts' },
        children: [
          {
            path: 'odm-analysis',
            name: 'RaOdmAnalysis',
            component: () => import('@/pages/ra/OdmAnalysisPage.vue'),
            meta: { title: 'ODM分析' },
          },
          {
            path: 'segment-analysis',
            name: 'RaSegmentAnalysis',
            component: () => import('@/pages/ra/SegmentAnalysisPage.vue'),
            meta: { title: 'Segment分析' },
          },
          {
            path: 'model-analysis',
            name: 'RaModelAnalysis',
            component: () => import('@/pages/ra/ModelAnalysisPage.vue'),
            meta: { title: 'Model分析' },
          },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
