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
      <!-- 数据上传 -->
      <el-menu-item index="/upload">
        <el-icon><Upload /></el-icon>
        <template #title>数据上传</template>
      </el-menu-item>

      <!-- IFIR分析 -->
      <el-sub-menu index="/kpi/ifir">
        <template #title>
          <el-icon><DataAnalysis /></el-icon>
          <span>IFIR分析</span>
        </template>
        <el-menu-item index="/kpi/ifir/odm-analysis">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>ODM分析</template>
        </el-menu-item>
        <el-menu-item index="/kpi/ifir/segment-analysis">
          <el-icon><PieChart /></el-icon>
          <template #title>Segment分析</template>
        </el-menu-item>
        <el-menu-item index="/kpi/ifir/model-analysis">
          <el-icon><Monitor /></el-icon>
          <template #title>Model分析</template>
        </el-menu-item>
      </el-sub-menu>

      <!-- RA分析 -->
      <el-sub-menu index="/kpi/ra">
        <template #title>
          <el-icon><TrendCharts /></el-icon>
          <span>RA分析</span>
        </template>
        <el-menu-item index="/kpi/ra/odm-analysis">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>ODM分析</template>
        </el-menu-item>
        <el-menu-item index="/kpi/ra/segment-analysis">
          <el-icon><PieChart /></el-icon>
          <template #title>Segment分析</template>
        </el-menu-item>
        <el-menu-item index="/kpi/ra/model-analysis">
          <el-icon><Monitor /></el-icon>
          <template #title>Model分析</template>
        </el-menu-item>
      </el-sub-menu>
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
  Monitor
} from '@element-plus/icons-vue'

defineProps<{
  collapse: boolean
}>()

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
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
