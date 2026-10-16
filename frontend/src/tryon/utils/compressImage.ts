/** 前端图片压缩：长边 ≤ 1024、JPEG quality 0.85，输出 Base64 供 POST /tryon。 */

export const DEFAULT_MAX_LONG_SIDE = 1024
export const DEFAULT_QUALITY = 0.85

export interface CompressOptions {
  maxLongSide?: number
  quality?: number
  /** 超过该体积（MB）直接拒绝，与后端 max_upload_mb 对齐 */
  maxInputMb?: number
}

export interface CompressedImage {
  /** 含 data:image/jpeg;base64, 前缀，可直接放进请求体 */
  dataUrl: string
  base64: string
  width: number
  height: number
  bytes: number
  originalBytes: number
  mime: string
}

const ACCEPTED_MIME = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']

export function assertImageFile(file: File, maxInputMb = 10): void {
  if (!ACCEPTED_MIME.includes(file.type)) {
    throw new Error(`不支持的图片格式：${file.type || file.name}（仅支持 JPG/PNG/WEBP/BMP）`)
  }
  if (file.size > maxInputMb * 1024 * 1024) {
    throw new Error(`图片体积超过 ${maxInputMb}MB 限制`)
  }
  if (file.size === 0) {
    throw new Error('图片内容为空')
  }
}

function readAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('图片读取失败'))
    reader.readAsDataURL(file)
  })
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('图片解码失败，可能已损坏'))
    image.src = src
  })
}

function base64Body(dataUrl: string): string {
  const comma = dataUrl.indexOf(',')
  return comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl
}

function approxBytes(base64: string): number {
  return Math.round((base64.length * 3) / 4)
}

/** EXIF Orientation 由浏览器 createImageBitmap 处理；这里用 canvas 重绘统一抹平。 */
export async function compressImage(file: File, options: CompressOptions = {}): Promise<CompressedImage> {
  const maxLongSide = options.maxLongSide ?? DEFAULT_MAX_LONG_SIDE
  const quality = options.quality ?? DEFAULT_QUALITY
  assertImageFile(file, options.maxInputMb ?? 10)

  const originDataUrl = await readAsDataUrl(file)
  const image = await loadImage(originDataUrl)
  const originWidth = image.naturalWidth || image.width
  const originHeight = image.naturalHeight || image.height
  if (originWidth < 64 || originHeight < 64) {
    throw new Error('图片分辨率过低（长边至少 64px），无法进行姿态估计')
  }

  const scale = Math.min(1, maxLongSide / Math.max(originWidth, originHeight))
  const width = Math.max(1, Math.round(originWidth * scale))
  const height = Math.max(1, Math.round(originHeight * scale))

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('当前浏览器不支持 Canvas 2D，无法压缩图片')
  // 白底填充，避免 PNG 透明区域在 JPEG 中变黑
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, width, height)
  context.drawImage(image, 0, 0, width, height)

  const dataUrl = canvas.toDataURL('image/jpeg', quality)
  const base64 = base64Body(dataUrl)
  return {
    dataUrl,
    base64,
    width,
    height,
    bytes: approxBytes(base64),
    originalBytes: file.size,
    mime: 'image/jpeg',
  }
}

export function formatKb(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 KB'
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(2)} MB` : `${(bytes / 1024).toFixed(1)} KB`
}
