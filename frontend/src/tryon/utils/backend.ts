export type BackendTagType = 'success' | 'primary' | 'warning' | 'info'

export interface BackendBadge {
  label: string
  tagType: BackendTagType
}

const BACKENDS: Record<string, BackendBadge> = {
  aidge: { label: 'Aidge 云端换装', tagType: 'success' },
  hrviton: { label: 'HR-VITON 高精度', tagType: 'success' },
  tps: { label: 'TPS 几何兜底', tagType: 'primary' },
  mock: { label: 'Mock 贴图（联调）', tagType: 'warning' },
}

/** 未知后端原样显示，方便对着日志排查，不做静默替换。 */
export function backendBadge(backend: string | null | undefined, emptyLabel = '未产出'): BackendBadge {
  const key = String(backend ?? '').trim()
  if (!key) return { label: emptyLabel, tagType: 'info' }
  return BACKENDS[key] ?? { label: key, tagType: 'info' }
}
