<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-icon 
        class="collapse-btn" 
        @click="$emit('toggle-sidebar')"
      >
        <Fold v-if="!collapse" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item 
          v-for="(item, index) in breadcrumbs" 
          :key="index"
        >
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <span class="app-title">KPI 可视化分析平台</span>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Fold, Expand } from '@element-plus/icons-vue'

defineProps<{
  collapse: boolean
}>()

defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const route = useRoute()

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    title: item.meta.title as string,
    path: item.path,
  }))
})
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
  .app-title {
    font-size: 16px;
    font-weight: 500;
    color: var(--primary-color);
  }
}

:deep(.el-breadcrumb) {
  font-size: 14px;
}
</style>
