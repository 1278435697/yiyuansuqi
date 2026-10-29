import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { batchTryOn, submitTryOn, TRYON_TIMEOUT_MS } from '@/tryon/api/tryon'
import { compressImage, type CompressedImage } from '@/tryon/utils/compressImage'
import { describeError } from '@/tryon/api/client'
import { useAppStore } from '@/tryon/store/app'
import type { Quality, TryOnResult } from '@/tryon/types'

export const PIPELINE_STEPS_LOCAL = [
  '前端压缩上传',
  '人像分割（Provider 链）',
  '人体姿态 17 关键点',
  '服饰 9 关键点 → TPS/HR-VITON 变形',
  '遮挡还原 + 光影匹配 + 边缘羽化',
  '结果落盘 + 记录入库',
] as const

/** 云端引擎只做一次换装调用，本地那套分割/姿态/形变过程图它不返回。 */
export const PIPELINE_STEPS_CLOUD = [
  '前端压缩上传',
  '服饰图自动裁边',
  'Aidge 云端换装推理',
  '结果落盘 + 记录入库',
] as const

/** 各阶段耗时（秒）经验值，仅用于视觉进度插值；真实耗时以后端 timings 为准。 */
const STAGE_BUDGET_LOCAL_FAST = [0.4, 1.2, 0.3, 3.0, 1.0, 0.3]
const STAGE_BUDGET_LOCAL_HD = [0.4, 2.0, 0.5, 9.0, 2.5, 0.5]
const STAGE_BUDGET_CLOUD = [0.4, 0.8, 4.0, 0.4]

export interface PersonState {
  fileName: string
  dataUrl: string
  width: number
  height: number
  bytes: number
  originalBytes: number
}

export const useTryOnStore = defineStore('tryon', () => {
  const person = ref<PersonState | null>(null)
  const compressed = ref<CompressedImage | null>(null)
  const selectedGarmentId = ref<string | null>(null)
  const quality = ref<Quality>('fast')
  const keepSourcePose = ref(true)
  // 后端磁盘缓存的键是（人像像素, 服饰图+mask, 素材id, quality），
  // 同一组合再点必然返回同一张图，所以给 UI 留一个显式跳缓存的口子。
  const forceRefresh = ref(false)

  const busy = ref(false)
  const progress = ref(0)
  const stageIndex = ref(-1)
  const result = ref<TryOnResult | null>(null)
  const batchResults = ref<TryOnResult[]>([])
  const error = ref<string | null>(null)

  const app = useAppStore()
  const isCloud = computed<boolean>(() => app.health?.vton_backend_resolved === 'aidge')
  const steps = computed<readonly string[]>(() => (isCloud.value ? PIPELINE_STEPS_CLOUD : PIPELINE_STEPS_LOCAL))

  let controller: AbortController | null = null
  let ticker: number | null = null

  const canSubmit = computed<boolean>(() => Boolean(person.value && selectedGarmentId.value && !busy.value))
  const hasResult = computed<boolean>(() => Boolean(result.value?.result_url))

  function stopTicker(): void {
    if (ticker !== null) {
      window.clearInterval(ticker)
      ticker = null
    }
  }

  /**
   * 后端 /tryon 是一次性返回的重计算接口，拿不到逐阶段回调，
   * 因此这里用「阶段耗时预算」做时间插值（最多推进到 92%），
   * 响应返回后再用 timings 精确回填每个阶段的真实耗时。
   */
  function startTicker(): void {
    const budget = isCloud.value
      ? STAGE_BUDGET_CLOUD
      : quality.value === 'hd'
        ? STAGE_BUDGET_LOCAL_HD
        : STAGE_BUDGET_LOCAL_FAST
    const totalMs = budget.reduce((sum, s) => sum + s, 0) * 1000
    const startedAt = Date.now()
    stopTicker()
    ticker = window.setInterval(() => {
      const elapsed = Date.now() - startedAt
      let acc = 0
      let index = -1
      for (let i = 0; i < budget.length; i += 1) {
        acc += budget[i] * 1000
        if (elapsed < acc) {
          index = i
          break
        }
      }
      stageIndex.value = index === -1 ? budget.length - 1 : index
      const ratio = Math.min(0.92, elapsed / (totalMs * 1.6))
      progress.value = Math.round(Math.min(92, ratio * 100))
    }, 200)
  }

  async function setPersonFile(file: File): Promise<void> {
    error.value = null
    const image = await compressImage(file, { quality: quality.value === 'hd' ? 0.92 : 0.85 })
    compressed.value = image
    person.value = {
      fileName: file.name,
      dataUrl: image.dataUrl,
      width: image.width,
      height: image.height,
      bytes: image.bytes,
      originalBytes: image.originalBytes,
    }
  }

  function clearPerson(): void {
    person.value = null
    compressed.value = null
    result.value = null
    batchResults.value = []
    progress.value = 0
    stageIndex.value = -1
  }

  function selectGarment(id: string | null): void {
    selectedGarmentId.value = id
    if (!busy.value) result.value = null
  }

  function setQuality(value: Quality): void {
    quality.value = value
  }

  function cancel(): void {
    controller?.abort()
    controller = null
    stopTicker()
    busy.value = false
    error.value = '已取消本次试穿'
  }

  async function run(): Promise<TryOnResult | null> {
    if (!person.value || !selectedGarmentId.value) {
      error.value = '请先上传真人照片并选择一件服饰素材'
      return null
    }
    error.value = null
    busy.value = true
    progress.value = 3
    stageIndex.value = 0
    result.value = null
    startTicker()
    controller = new AbortController()
    try {
      const payload = {
        person_image: person.value.dataUrl,
        garment_id: selectedGarmentId.value,
        quality: quality.value,
        keep_source_pose: keepSourcePose.value,
        force_refresh: forceRefresh.value,
      }
      const data = await submitTryOn(payload, controller.signal)
      result.value = data
      progress.value = 100
      stageIndex.value = steps.value.length - 1
      if (data.status === 'failed') {
        error.value = data.message ?? '试穿合成失败，请更换正身、光线清晰的图片重试'
      }
      return data
    } catch (err) {
      error.value = describeError(err)
      return null
    } finally {
      stopTicker()
      busy.value = false
      controller = null
    }
  }

  async function runBatch(garmentIds: string[]): Promise<TryOnResult[]> {
    if (!person.value || garmentIds.length === 0) {
      error.value = '批量试穿需要先上传真人照片并勾选素材'
      return []
    }
    error.value = null
    busy.value = true
    progress.value = 3
    stageIndex.value = 0
    batchResults.value = []
    startTicker()
    controller = new AbortController()
    try {
      const list = await batchTryOn(
        person.value.dataUrl,
        garmentIds,
        quality.value,
        forceRefresh.value,
        controller.signal,
      )
      batchResults.value = list
      progress.value = 100
      stageIndex.value = steps.value.length - 1
      result.value = list.find((item) => item.status === 'succeeded') ?? list[0] ?? null
      if (result.value?.task_id) selectedGarmentId.value = result.value.trace_card?.garment_id ?? selectedGarmentId.value
      return list
    } catch (err) {
      error.value = describeError(err)
      return []
    } finally {
      stopTicker()
      busy.value = false
      controller = null
    }
  }

  return {
    person,
    compressed,
    selectedGarmentId,
    quality,
    keepSourcePose,
    forceRefresh,
    busy,
    progress,
    stageIndex,
    result,
    batchResults,
    error,
    canSubmit,
    hasResult,
    setPersonFile,
    clearPerson,
    selectGarment,
    setQuality,
    run,
    runBatch,
    cancel,
    timeoutMs: TRYON_TIMEOUT_MS,
    isCloud,
    steps,
  }
})
