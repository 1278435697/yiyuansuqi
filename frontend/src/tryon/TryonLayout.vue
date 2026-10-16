<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/tryon/store/app'
import '@/tryon/styles/tryon.css'

const route = useRoute()
const app = useAppStore()

const tabs = [
  { name: 'tryon', label: '一键试穿' },
  { name: 'tryon-gallery', label: '服饰素材库' },
  { name: 'tryon-history', label: '试穿记录' },
]

const healthTag = computed(() => {
  const info = app.health
  if (!info) return { type: 'info' as const, text: '试穿服务未连接' }
  if (info.status === 'ok') return { type: 'success' as const, text: `试穿服务正常 · ${app.backendLabel}` }
  return { type: 'warning' as const, text: `试穿服务降级 · ${app.backendLabel}` }
})

// 独立运行时健康标签在站点头部，并入平台后挪到这里，所以布局自己拉一次
onMounted(() => {
  void app.refreshHealth()
})
</script>

<template>
  <div class="tryon-layout">
    <div class="layout-bar">
      <el-breadcrumb separator="/" class="crumb">
        <el-breadcrumb-item :to="{ path: '/museum' }">数字博物馆</el-breadcrumb-item>
        <el-breadcrumb-item>虚拟试穿</el-breadcrumb-item>
        <el-breadcrumb-item v-if="typeof route.meta.title === 'string' && route.meta.title !== '虚拟试穿'">
          {{ route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>

      <nav class="tabs">
        <RouterLink v-for="tab in tabs" :key="tab.name" :to="{ name: tab.name }">{{ tab.label }}</RouterLink>
      </nav>

      <el-tag :type="healthTag.type" effect="plain" size="small">{{ healthTag.text }}</el-tag>
    </div>

    <RouterView />
  </div>
</template>

<style scoped>
.tryon-layout {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 0 32px;
  color: var(--yisu-ink);
}

.layout-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  padding: 10px 16px;
  background: var(--ys-card, rgba(255, 253, 248, 0.92));
  border: 1px solid var(--ys-line, #e4dcc8);
  border-radius: var(--yisu-radius-lg);
}

.tabs {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.tabs a {
  padding: 6px 14px;
  border-radius: var(--yisu-radius);
  color: var(--yisu-ink-soft);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.18s ease;
}

.tabs a:hover {
  background: var(--yisu-vermilion-soft);
  color: var(--yisu-vermilion-dark);
}

.tabs a.router-link-active {
  background: var(--yisu-vermilion);
  color: #fff;
}
</style>
