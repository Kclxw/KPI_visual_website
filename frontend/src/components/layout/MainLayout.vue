<template>
  <el-container class="main-layout">
    <AppSidebar :collapse="isCollapse" />
    <el-container class="main-container">
      <AppHeader @toggle-sidebar="toggleSidebar" :collapse="isCollapse" />
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const isCollapse = ref(false)

const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
  width: 100%;
}

.main-container {
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  padding: 0;
  overflow-y: auto;
  background-color: var(--bg-color);
}
</style>
