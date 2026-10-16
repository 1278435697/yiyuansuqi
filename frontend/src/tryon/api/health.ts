import { get } from '@/tryon/api/client'
import { asArray, asOptionalString, asString } from '@/tryon/utils/guards'
import type { HealthOut } from '@/tryon/types'

export async function fetchHealth(signal?: AbortSignal): Promise<HealthOut> {
  const raw = (await get<unknown>('/health', undefined, {
    signal,
    retries: 1,
    notify: false,
  })) as Record<string, unknown>
  const status = asString(raw.status, 'health.status')
  return {
    status: status === 'ok' ? 'ok' : 'degraded',
    version: asOptionalString(raw.version, 'health.version'),
    vton_backend_configured: asOptionalString(raw.vton_backend_configured, 'health.vton_backend_configured'),
    vton_backend_resolved: asOptionalString(raw.vton_backend_resolved, 'health.vton_backend_resolved') || 'unknown',
    fallback_reason: typeof raw.fallback_reason === 'string' ? raw.fallback_reason : null,
    gpu_available: raw.gpu_available === true,
    components: (typeof raw.components === 'object' && raw.components !== null ? raw.components : {}) as Record<
      string,
      unknown
    >,
    garments_count: Number(raw.garments_count) || 0,
  }
}

export interface SkeletonInfo {
  app: { name: string; version: string }
  runtime: Record<string, unknown>
  pipelineSteps: string[]
  raw: Record<string, unknown>
}

/** 答辩截图时一并落盘的运行环境元数据。 */
export async function fetchSkeleton(signal?: AbortSignal): Promise<SkeletonInfo> {
  const raw = (await get<unknown>('/debug/skeleton', undefined, { signal, notify: false })) as Record<string, unknown>
  const app = (raw.app ?? {}) as Record<string, unknown>
  const steps = raw.pipeline_steps
  return {
    app: { name: asOptionalString(app.name, 'skeleton.app.name'), version: asOptionalString(app.version, 'skeleton.app.version') },
    runtime: (raw.runtime ?? {}) as Record<string, unknown>,
    pipelineSteps: Array.isArray(steps) ? asArray<unknown>(steps, 'skeleton.pipeline_steps').map((s) => String(s)) : [],
    raw,
  }
}
