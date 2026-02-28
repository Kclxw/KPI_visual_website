<template>
  <el-aside :width="collapse ? '64px' : '220px'" class="app-sidebar">
    <div class="logo-container">
      <img src="/vite.svg" alt="Logo" class="logo" />
      <span v-show="!collapse" class="logo-text">KPI分析</span>
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="collapse"
      :collapse-transition="false"
      router
      class="sidebar-menu"
    >
      <template v-for="item in visibleMenuItems" :key="item.key">
        <el-sub-menu v-if="item.children?.length" :index="item.key">
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </template>
          <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
            <el-icon><component :is="child.icon" /></el-icon>
            <template #title>{{ child.title }}</template>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item v-else :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </template>
    </el-menu>
  </el-aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Upload,
  DataAnalysis,
  TrendCharts,
  OfficeBuilding,
  PieChart,
  Monitor,
  UserFilled,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  collapse: boolean
}>()

const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const visibleMenuItems = computed(() => {
  const role = authStore.user?.role ?? 'viewer'
  const hasRole = (roles: string[]) => roles.includes(role)

  const menus = [
    {
      key: 'upload',
      title: '数据上传',
      path: '/upload',
      icon: Upload,
      roles: ['admin', 'uploader'],
    },
    {
      key: 'ifir',
      title: 'IFIR分析',
      icon: DataAnalysis,
      roles: ['admin', 'uploader', 'viewer'],
      children: [
        {
          title: 'ODM分析',
          path: '/kpi/ifir/odm-analysis',
          icon: OfficeBuilding,
        },
        {
          title: 'Segment分析',
          path: '/kpi/ifir/segment-analysis',
          icon: PieChart,
        },
        {
          title: 'Model分析',
          path: '/kpi/ifir/model-analysis',
          icon: Monitor,
        },
      ],
    },
    {
      key: 'ra',
      title: 'RA分析',
      icon: TrendCharts,
      roles: ['admin', 'uploader', 'viewer'],
      children: [
        {
          title: 'ODM分析',
          path: '/kpi/ra/odm-analysis',
          icon: OfficeBuilding,
        },
        {
          title: 'Segment分析',
          path: '/kpi/ra/segment-analysis',
          icon: PieChart,
        },
        {
          title: 'Model分析',
          path: '/kpi/ra/model-analysis',
          icon: Monitor,
        },
      ],
    },
    {
      key: 'admin-users',
      title: '用户管理',
      path: '/admin/users',
      icon: UserFilled,
      roles: ['admin'],
    },
  ]

  return menus
    .filter((item) => hasRole(item.roles))
    .map((item) => {
      if (!item.children) return item
      return {
        ...item,
        children: item.children,
      }
    })
})
</script>

<style scoped lang="scss">
.app-sidebar {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo-container {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #263445;

  .logo {
    width: 32px;
    height: 32px;
  }

  .logo-text {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    white-space: nowrap;
  }
}

.sidebar-menu {
  border-right: none;
  background: transparent;

  &:not(.el-menu--collapse) {
    width: 220px;
  }
}

:deep(.el-menu) {
  background: transparent;
  border: none;

  .el-menu-item,
  .el-sub-menu__title {
    color: #bfcbd9;

    &:hover {
      background-color: #263445;
    }

    .el-icon {
      color: inherit;
    }
  }

  .el-menu-item.is-active {
    background-color: var(--primary-color);
    color: #fff;
  }

  .el-sub-menu.is-active > .el-sub-menu__title {
    color: #fff;
  }
}

:deep(.el-sub-menu .el-menu) {
  background: #1f2d3d;
}
</style>
