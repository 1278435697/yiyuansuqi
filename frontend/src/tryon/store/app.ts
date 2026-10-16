import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchGarments } from '@/tryon/api/garments'
import { fetchHealth } from '@/tryon/api/health'
import { describeError } from '@/tryon/api/client'
import type { Garment, GarmentCategory, HealthOut } from '@/tryon/types'

const ALL = '__all__'

// 在途请求句柄：避免首屏重复打后端
let garmentsPending: Promise<void> | null = null
let healthPending: Promise<void> | null = null

/** 全局素材库 / 运行状态：供 TryOnView 与 GalleryView 共用，避免重复请求。 */
export const useAppStore = defineStore('app', () => {
  const garments = ref<Garment[]>([])
  const garmentsLoading = ref(false)
  const garmentsError = ref<string | null>(null)
  const categoryFilter = ref<string>(ALL)
  const dynastyFilter = ref<string>(ALL)
  const keyword = ref('')
  const health = ref<HealthOut | null>(null)

  const categories = computed<string[]>(() => {
    const set = new Set(garments.value.map((g) => g.category))
    return Array.from(set).sort()
  })
  const dynasties = computed<string[]>(() => {
    const set = new Set(garments.value.map((g) => g.dynasty).filter(Boolean))
    return Array.from(set).sort()
  })
  const filteredGarments = computed<Garment[]>(() => {
    const text = keyword.value.trim().toLowerCase()
    return garments.value.filter((g) => {
      if (categoryFilter.value !== ALL && g.category !== categoryFilter.value) return false
      if (dynastyFilter.value !== ALL && g.dynasty !== dynastyFilter.value) return false
      if (!text) return true
      const haystack = [g.name, g.id, g.dynasty, ...g.tags].join(' ').toLowerCase()
      return haystack.includes(text)
    })
  })
  const backendLabel = computed<string>(() => {
    const resolved = health.value?.vton_backend_resolved
    if (!resolved) return '检测中'
    return resolved === 'hrviton' ? 'HR-VITON 高精度' : resolved === 'tps' ? 'TPS 几何兜底' : resolved
  })

  async function loadGarments(force = false): Promise<void> {
    if (garments.value.length && !force) return
    // 同一时刻多个组件（TryOnView / GarmentPicker）挂载时都会请求，复用在途 Promise
    if (garmentsPending) return garmentsPending
    garmentsPending = (async () => {
      garmentsLoading.value = true
      garmentsError.value = null
      try {
        garments.value = await fetchGarments()
      } catch (error) {
        garmentsError.value = describeError(error)
        garments.value = []
      } finally {
        garmentsLoading.value = false
        garmentsPending = null
      }
    })()
    return garmentsPending
  }

  async function refreshHealth(): Promise<void> {
    if (healthPending) return healthPending
    healthPending = (async () => {
      try {
        health.value = await fetchHealth()
      } catch (error) {
        health.value = null
        garmentsError.value = describeError(error)
      } finally {
        healthPending = null
      }
    })()
    return healthPending
  }

  function categoryLabel(category: GarmentCategory | string): string {
    return { top: '上襦/短衣', dress: '裙装', skirt: '下裳', robe: '袍服' }[String(category)] ?? String(category)
  }

  return {
    garments,
    garmentsLoading,
    garmentsError,
    categoryFilter,
    dynastyFilter,
    keyword,
    health,
    categories,
    dynasties,
    filteredGarments,
    backendLabel,
    loadGarments,
    refreshHealth,
    categoryLabel,
    ALL,
  }
})
