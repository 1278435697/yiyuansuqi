/** 与后端 app/schemas.py 一一对应的前端类型定义。 */

export type Quality = 'fast' | 'hd'
export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type GarmentCategory = 'top' | 'dress' | 'skirt' | 'robe'

export interface Keypoint {
  name: string
  x: number
  y: number
  visibility?: number
}

export interface TraceCard {
  garment_id: string
  name: string
  dynasty: string
  category: string
  source_text: string
  references: string[]
}

export interface Garment {
  id: string
  name: string
  dynasty: string
  category: GarmentCategory
  tags: string[]
  image_url: string
  thumb_url: string
  keypoints: Keypoint[]
  source_text: string
  references: string[]
}

export interface TryOnRequest {
  person_image: string
  garment_id?: string | null
  garment_image?: string | null
  quality?: Quality
  keep_source_pose?: boolean
  force_refresh?: boolean
}

export interface TryOnResult {
  task_id: string
  status: TaskStatus
  result_url: string | null
  person_mask_url: string | null
  pose_overlay_url: string | null
  garment_warp_url: string | null
  backend_used: string
  warnings: string[]
  timings: Record<string, number>
  trace_card: TraceCard | null
  error_code: string | null
  message: string | null
}

export interface TryOnRecord {
  id: number
  task_id: string
  garment_id: string | null
  garment_name: string | null
  person_url: string
  result_url: string
  backend_used: string
  quality: string
  warnings: string[]
  created_at: string
}

export interface HistoryPage {
  items: TryOnRecord[]
  total: number
  limit: number
  offset: number
}

export interface HealthOut {
  status: 'ok' | 'degraded'
  version: string
  vton_backend_configured: string
  vton_backend_resolved: string
  fallback_reason: string | null
  gpu_available: boolean
  components: Record<string, unknown>
  garments_count: number
}

/** 归一化后的错误对象：后端只回 error_code + 中文 message + request_id。 */
export interface ApiError {
  status: number
  errorCode: string
  message: string
  requestId: string | null
  detail?: unknown
}

export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as ApiError).errorCode === 'string' &&
    typeof (value as ApiError).message === 'string'
  )
}
