import { del, get, request } from '@/tryon/api/client'
import {
  asArray,
  asOptionalString,
  asOptionalUrl,
  asRecord,
  asString,
} from '@/tryon/utils/guards'
import type { HistoryPage, Quality, TraceCard, TryOnRecord, TryOnRequest, TryOnResult } from '@/tryon/types'

/** /tryon 是重计算接口：CPU 兜底路径也可能跑到十几秒，客户端超时给到 120s。 */
export const TRYON_TIMEOUT_MS = 120_000

function normalizeTrace(raw: unknown): TraceCard | null {
  if (raw === null || typeof raw !== 'object') return null
  const item = raw as Record<string, unknown>
  try {
    return {
      garment_id: asString(item.garment_id, 'trace.garment_id'),
      name: asString(item.name, 'trace.name'),
      dynasty: asOptionalString(item.dynasty, 'trace.dynasty') || '未知',
      category: asOptionalString(item.category, 'trace.category'),
      source_text: asOptionalString(item.source_text, 'trace.source_text'),
      references: asArray<string>(item.references ?? [], 'trace.references').map((ref) => String(ref)),
    }
  } catch (error) {
    console.warn('[tryon] 溯源卡片字段不完整', error)
    return null
  }
}

/** 后端响应字段先校验再落地，缺字段直接抛错，避免渲染阶段崩溃。 */
export function normalizeTryOnResult(raw: unknown): TryOnResult {
  const item = (raw ?? {}) as Record<string, unknown>
  const status = asString(item.status, 'tryon.status')
  if (!['pending', 'running', 'succeeded', 'failed'].includes(status)) {
    throw new TypeError(`tryon.status 非法：${status}`)
  }
  return {
    task_id: asString(item.task_id, 'tryon.task_id'),
    status: status as TryOnResult['status'],
    result_url: asOptionalUrl(item.result_url),
    person_mask_url: asOptionalUrl(item.person_mask_url),
    pose_overlay_url: asOptionalUrl(item.pose_overlay_url),
    garment_warp_url: asOptionalUrl(item.garment_warp_url),
    backend_used: asOptionalString(item.backend_used, 'tryon.backend_used') || 'unknown',
    warnings: asArray<string>(item.warnings ?? [], 'tryon.warnings').map((w) => String(w)),
    timings: asRecord(item.timings ?? {}, 'tryon.timings'),
    trace_card: normalizeTrace(item.trace_card),
    error_code: typeof item.error_code === 'string' ? item.error_code : null,
    message: typeof item.message === 'string' ? item.message : null,
  }
}

export function submitTryOn(payload: TryOnRequest, signal?: AbortSignal): Promise<TryOnResult> {
  return request<TryOnResult>(
    { method: 'POST', url: '/tryon', data: payload, timeout: TRYON_TIMEOUT_MS },
    { notify: false, signal, timeoutMs: TRYON_TIMEOUT_MS },
  ).then(normalizeTryOnResult)
}

export function batchTryOn(
  personImage: string,
  garmentIds: string[],
  quality: Quality = 'fast',
  forceRefresh = false,
  signal?: AbortSignal,
): Promise<TryOnResult[]> {
  return request<unknown[]>(
    {
      method: 'POST',
      url: '/tryon/batch',
      data: { person_image: personImage, garment_ids: garmentIds, quality, force_refresh: forceRefresh },
      timeout: TRYON_TIMEOUT_MS * Math.max(1, garmentIds.length),
    },
    { notify: false, signal, timeoutMs: TRYON_TIMEOUT_MS * Math.max(1, garmentIds.length) },
  ).then((raw) => asArray<unknown>(raw, 'POST /tryon/batch').map(normalizeTryOnResult))
}

/** multipart 形式（等价接口，便于 curl 复现与项目书演示）。 */
export async function uploadTryOn(
  personFile: File,
  garmentId: string,
  quality: Quality = 'fast',
  signal?: AbortSignal,
): Promise<TryOnResult> {
  const form = new FormData()
  form.append('person_file', personFile)
  form.append('garment_id', garmentId)
  form.append('quality', quality)
  const result = await request<unknown>(
    { method: 'POST', url: '/tryon/upload', data: form, timeout: TRYON_TIMEOUT_MS },
    { notify: false, signal, timeoutMs: TRYON_TIMEOUT_MS },
  )
  return normalizeTryOnResult(result)
}

export async function fetchTask(taskId: string, signal?: AbortSignal): Promise<TryOnResult> {
  const raw = await get<unknown>(`/tryon/${encodeURIComponent(taskId)}`, undefined, { signal, retries: 1 })
  return normalizeTryOnResult(raw)
}

export async function fetchHistory(
  limit = 20,
  offset = 0,
  signal?: AbortSignal,
): Promise<HistoryPage> {
  const raw = (await get<unknown>('/history', { limit, offset }, { signal })) as Record<string, unknown>
  const items = asArray<unknown>(raw.items ?? [], 'history.items').map((entry) => {
    const item = (entry ?? {}) as Record<string, unknown>
    return {
      id: Number(item.id) || 0,
      task_id: asString(item.task_id, 'history.task_id'),
      garment_id: typeof item.garment_id === 'string' ? item.garment_id : null,
      garment_name: typeof item.garment_name === 'string' ? item.garment_name : null,
      person_url: asOptionalString(item.person_url, 'history.person_url'),
      result_url: asOptionalString(item.result_url, 'history.result_url'),
      backend_used: asOptionalString(item.backend_used, 'history.backend_used'),
      quality: asOptionalString(item.quality, 'history.quality'),
      warnings: asArray<string>(item.warnings ?? [], 'history.warnings').map((w) => String(w)),
      created_at: asOptionalString(item.created_at, 'history.created_at'),
    } satisfies TryOnRecord
  })
  return {
    items,
    total: Number(raw.total) || items.length,
    limit: Number(raw.limit) || limit,
    offset: Number(raw.offset) || offset,
  }
}

export function deleteHistoryRecord(taskId: string, signal?: AbortSignal): Promise<void> {
  return del<void>(`/history/${encodeURIComponent(taskId)}`, { signal })
}

/** 分割 Provider 链元数据，用于「管线中间图」面板展示当前生效算法。 */
export async function fetchSegmentationMeta(signal?: AbortSignal): Promise<Record<string, unknown>> {
  return (await get<Record<string, unknown>>('/tryon/meta/segmentation', undefined, {
    signal,
  })) as Record<string, unknown>
}
