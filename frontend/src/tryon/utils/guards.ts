/** 运行时契约守卫：后端字段一律先校验再渲染，杜绝 undefined.map / null.src 崩溃。 */

export function asArray<T>(value: unknown, field: string): T[] {
  if (!Array.isArray(value)) {
    throw new TypeError(`响应字段 ${field} 期望数组，实际 ${typeof value}`)
  }
  return value as T[]
}

export function asString(value: unknown, field: string): string {
  if (typeof value !== 'string' || !value) {
    throw new TypeError(`响应字段 ${field} 期望非空字符串，实际 ${String(value)}`)
  }
  return value
}

/** 可选字符串：null/undefined 归一为空串，非法类型抛错。 */
export function asOptionalString(value: unknown, field: string): string {
  if (value === null || value === undefined) return ''
  if (typeof value !== 'string') {
    throw new TypeError(`响应字段 ${field} 期望字符串或 null，实际 ${String(value)}`)
  }
  return value
}

/** 可选 URL：仅当是非空字符串时返回，否则返回 null（供 v-if 使用）。 */
export function asOptionalUrl(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null
}

export function asRecord(value: unknown, field: string): Record<string, number> {
  if (typeof value !== 'object' || value === null) {
    throw new TypeError(`响应字段 ${field} 期望对象，实际 ${typeof value}`)
  }
  const out: Record<string, number> = {}
  for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
    out[key] = typeof item === 'number' && Number.isFinite(item) ? item : Number(item) || 0
  }
  return out
}

export function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}
