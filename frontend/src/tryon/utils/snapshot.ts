/** 截图落盘：浏览器原生 canvas.toDataURL()，不引入 Playwright/html2canvas。
 *
 * 产物按 `oneoff/stepN_描述.png` 命名，由 README 的表格索引；
 * 同时把 /api/v1/debug/skeleton 的运行环境 JSON 一起下载，作为答辩证据链。
 */

export const SNAPSHOT_DIR_HINT = 'oneoff/'

export interface SnapshotCaption {
  title: string
  subtitle?: string
  taskId?: string
  backend?: string
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error(`图片加载失败：${src}`))
    image.src = src
  })
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  // 留一点时间给浏览器启动下载
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export function dataUrlToBlob(dataUrl: string): Blob {
  const comma = dataUrl.indexOf(',')
  const meta = dataUrl.slice(0, comma)
  const base64 = dataUrl.slice(comma + 1)
  const mime = meta.includes(':') ? meta.split(':')[1].split(';')[0] : 'image/png'
  const binary = atob(base64)
  const buffer = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) buffer[i] = binary.charCodeAt(i)
  return new Blob([buffer], { type: mime })
}

export function buildSnapshotName(step: number, description: string, ext = 'png'): string {
  const safe = description
    .trim()
    .replace(/[\\/:*?"<>|\s]+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 48)
  return `step${String(step).padStart(2, '0')}_${safe || 'snapshot'}.${ext}`
}

/** 给结果图加上页脚说明条，截图直接可用于项目书排版。 */
export async function snapshotImage(imageUrl: string, filename: string, caption: SnapshotCaption): Promise<void> {
  const image = await loadImage(imageUrl)
  const barHeight = Math.max(56, Math.round(image.naturalWidth * 0.06))
  const canvas = document.createElement('canvas')
  canvas.width = image.naturalWidth
  canvas.height = image.naturalHeight + barHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('当前浏览器不支持 Canvas 2D')

  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(image, 0, 0)

  ctx.fillStyle = '#1a1a1a'
  ctx.fillRect(0, image.naturalHeight, canvas.width, barHeight)
  ctx.fillStyle = '#b03a2e'
  ctx.fillRect(0, image.naturalHeight, Math.max(6, barHeight * 0.08), barHeight)

  const pad = barHeight * 0.28
  ctx.fillStyle = '#f6f1e7'
  ctx.font = `600 ${Math.round(barHeight * 0.32)}px "PingFang SC", "Microsoft YaHei", sans-serif`
  ctx.textBaseline = 'middle'
  ctx.fillText(caption.title, pad, image.naturalHeight + barHeight * 0.38)
  ctx.font = `${Math.round(barHeight * 0.22)}px "PingFang SC", "Microsoft YaHei", sans-serif`
  ctx.fillStyle = '#c9c2b2'
  const meta = [
    caption.subtitle,
    caption.backend ? `backend=${caption.backend}` : '',
    caption.taskId ? `task=${caption.taskId}` : '',
  ]
    .filter(Boolean)
    .join('  |  ')
  ctx.fillText(meta, pad, image.naturalHeight + barHeight * 0.72)

  const dataUrl = canvas.toDataURL('image/png')
  triggerDownload(dataUrlToBlob(dataUrl), filename)
}

export async function downloadRemoteImage(imageUrl: string, filename: string): Promise<void> {
  const response = await fetch(imageUrl, { cache: 'no-store' })
  if (!response.ok) throw new Error(`下载失败：HTTP ${response.status}`)
  const blob = await response.blob()
  triggerDownload(blob, filename)
}

export function dumpJson(payload: unknown, filename: string): void {
  const text = JSON.stringify(payload, null, 2)
  triggerDownload(new Blob([text], { type: 'application/json;charset=utf-8' }), filename)
}
