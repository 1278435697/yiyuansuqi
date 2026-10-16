import { get } from '@/tryon/api/client'
import { asArray, asOptionalString, asString } from '@/tryon/utils/guards'
import type { Garment, GarmentCategory, Keypoint, TraceCard } from '@/tryon/types'

const CATEGORIES: GarmentCategory[] = ['top', 'dress', 'skirt', 'robe']

function toKeypoint(raw: unknown): Keypoint {
  const item = (raw ?? {}) as Record<string, unknown>
  return {
    name: asString(item.name, 'keypoint.name'),
    x: Number(item.x) || 0,
    y: Number(item.y) || 0,
    visibility: Number(item.visibility ?? 1),
  }
}

/** 逐条校验素材，任何一条字段异常只丢弃该条并告警，不让整页白屏。 */
function normalizeGarment(raw: unknown): Garment | null {
  try {
    const item = (raw ?? {}) as Record<string, unknown>
    const category = asString(item.category, 'garment.category') as GarmentCategory
    return {
      id: asString(item.id, 'garment.id'),
      name: asString(item.name, 'garment.name'),
      dynasty: asOptionalString(item.dynasty, 'garment.dynasty') || '未知',
      category: CATEGORIES.includes(category) ? category : 'top',
      tags: asArray<string>(item.tags ?? [], 'garment.tags').map((tag) => String(tag)),
      image_url: asString(item.image_url, 'garment.image_url'),
      thumb_url: asOptionalString(item.thumb_url, 'garment.thumb_url') || asString(item.image_url, 'garment.image_url'),
      keypoints: asArray<unknown>(item.keypoints ?? [], 'garment.keypoints').map(toKeypoint),
      source_text: asOptionalString(item.source_text, 'garment.source_text'),
      references: asArray<string>(item.references ?? [], 'garment.references').map((ref) => String(ref)),
    }
  } catch (error) {
    console.warn('[garments] 素材数据不完整已跳过', raw, error)
    return null
  }
}

export async function fetchGarments(signal?: AbortSignal): Promise<Garment[]> {
  const raw = await get<unknown>('/garments', undefined, { signal })
  return asArray<unknown>(raw ?? [], 'GET /garments').map(normalizeGarment).filter((g): g is Garment => g !== null)
}

export async function fetchGarment(id: string, signal?: AbortSignal): Promise<Garment> {
  const raw = await get<unknown>(`/garments/${encodeURIComponent(id)}`, undefined, { signal })
  const garment = normalizeGarment(raw)
  if (!garment) throw new TypeError(`素材 ${id} 响应不完整`)
  return garment
}

export async function fetchTraceCard(id: string, signal?: AbortSignal): Promise<TraceCard> {
  const raw = (await get<unknown>(`/garments/${encodeURIComponent(id)}/trace`, undefined, { signal })) as Record<
    string,
    unknown
  >
  return {
    garment_id: asString(raw.garment_id, 'trace.garment_id'),
    name: asString(raw.name, 'trace.name'),
    dynasty: asOptionalString(raw.dynasty, 'trace.dynasty') || '未知',
    category: asOptionalString(raw.category, 'trace.category'),
    source_text: asOptionalString(raw.source_text, 'trace.source_text'),
    references: asArray<string>(raw.references ?? [], 'trace.references').map((ref) => String(ref)),
  }
}

export async function fetchGarmentBlob(id: string, signal?: AbortSignal): Promise<Blob> {
  // 下载素材原图（项目书演示 / 答辩留档用）
  const garment = await fetchGarment(id, signal)
  const response = await fetch(garment.image_url, { signal })
  if (!response.ok) throw new Error(`素材图片下载失败：${response.status}`)
  return response.blob()
}
