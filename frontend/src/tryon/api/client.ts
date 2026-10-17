import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiError } from '@/tryon/types'

export const API_PREFIX = import.meta.env?.VITE_API_BASE ?? '/api/v1'

/** 后端只读资产（素材图 / 示例图）的挂载前缀，与后端 settings.asset_url_prefix 保持一致。 */
export const ASSET_PREFIX = import.meta.env?.VITE_ASSET_BASE ?? '/tryon-assets'

/** 后端错误响应体形状（已脱敏，只有 error_code / message / request_id，detail 是 message 的同值别名）。 */
interface BackendErrorBody {
  error_code?: unknown
  message?: unknown
  request_id?: unknown
  detail?: unknown
}

const http = axios.create({
  baseURL: API_PREFIX,
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // 每次请求带一个前端 request_id，便于与后端日志对齐
  config.headers.set('X-Request-ID', config.headers.get('X-Request-ID') ?? randomId())
  return config
})

function randomId(): string {
  const buffer = new Uint8Array(8)
  crypto.getRandomValues(buffer)
  return Array.from(buffer, (b) => b.toString(16).padStart(2, '0')).join('')
}

function toApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const body = (error.response?.data ?? {}) as BackendErrorBody
    const status = error.response?.status ?? 0
    const headerRequestId = error.response?.headers?.['x-request-id']
    const message =
      typeof body.message === 'string' && body.message
        ? body.message
        : status === 0
          ? '无法连接后端服务，请确认 uvicorn 已启动（127.0.0.1:8000）'
          : error.message || '请求失败'
    return {
      status,
      errorCode: typeof body.error_code === 'string' ? body.error_code : `HTTP_${status || 'NETWORK'}`,
      message,
      requestId:
        typeof body.request_id === 'string'
          ? body.request_id
          : typeof headerRequestId === 'string'
            ? headerRequestId
            : null,
      detail: body.detail,
    }
  }
  return {
    status: 0,
    errorCode: 'UNKNOWN_ERROR',
    message: error instanceof Error ? error.message : '未知错误',
    requestId: null,
  }
}

export interface RequestOptions {
  /** 网络错误 / 5xx 时的最大重试次数（仅幂等的读接口开启） */
  retries?: number
  /** 指数退避基数（毫秒） */
  baseDelayMs?: number
  signal?: AbortSignal
  timeoutMs?: number
  /** 为 false 时不弹全局错误提示，由调用方自行处理 */
  notify?: boolean
}

const RETRYABLE_STATUS = new Set([0, 408, 429, 500, 502, 503, 504])

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

/** 指数退避 + 抖动，避免后端刚启动时前端把请求打满。 */
export async function withRetry<T>(
  task: (attempt: number) => Promise<T>,
  { retries = 0, baseDelayMs = 350, signal }: { retries?: number; baseDelayMs?: number; signal?: AbortSignal } = {},
): Promise<T> {
  let attempt = 0
  for (;;) {
    if (signal?.aborted) throw toApiError(new AxiosError('canceled', AxiosError.ERR_CANCELED))
    try {
      return await task(attempt)
    } catch (error) {
      const apiError = toApiError(error)
      const canRetry = attempt < retries && RETRYABLE_STATUS.has(apiError.status)
      if (!canRetry) throw apiError
      const delay = baseDelayMs * 2 ** attempt + Math.random() * baseDelayMs
      await sleep(delay)
      attempt += 1
    }
  }
}

export async function request<T>(
  config: AxiosRequestConfig,
  options: RequestOptions = {},
): Promise<T> {
  const { retries = 0, baseDelayMs, signal, timeoutMs, notify = true } = options
  try {
    const response: AxiosResponse<T> = await withRetry(
      () => http.request<T>({ ...config, signal, timeout: timeoutMs ?? config.timeout }),
      { retries, baseDelayMs, signal },
    )
    return response.data
  } catch (error) {
    const apiError = toApiError(error)
    if (notify) {
      ElMessage.error(`${apiError.message}${apiError.requestId ? `（#${apiError.requestId}）` : ''}`)
    }
    throw apiError
  }
}

export function get<T>(url: string, params?: unknown, options?: RequestOptions): Promise<T> {
  return request<T>({ method: 'GET', url, params }, { retries: 2, ...options })
}

export function post<T>(url: string, data?: unknown, options?: RequestOptions): Promise<T> {
  return request<T>({ method: 'POST', url, data }, { retries: 0, ...options })
}

export function del<T>(url: string, options?: RequestOptions): Promise<T> {
  return request<T>({ method: 'DELETE', url }, { retries: 0, ...options })
}

/** 渲染友好的错误文案。 */
export function describeError(error: unknown): string {
  const apiError = toApiError(error)
  return `${apiError.message}${apiError.requestId ? ` [request_id: ${apiError.requestId}]` : ''}`
}

export default http
