<script setup lang="ts">
import { ref } from 'vue'
import { Loading, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useTryOnStore } from '@/tryon/store/tryon'
import { formatKb } from '@/tryon/utils/compressImage'
import { describeError } from '@/tryon/api/client'

const store = useTryOnStore()
const inputRef = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const loading = ref(false)

const MAX_INPUT_MB = 10

// 示例人像按「真实质感优先」顺序尝试：register_garments.py 产出的真人像 > 内置示意图
const SAMPLE_PERSONS = ['person_real.png', 'person_demo.png']

async function handleFiles(files: FileList | File[] | null): Promise<void> {
  const list = files ? Array.from(files) : []
  const image = list.find((file) => file.type.startsWith('image/'))
  if (!image) {
    ElMessage.warning('请选择图片文件（JPG / PNG / WEBP / BMP）')
    return
  }
  loading.value = true
  try {
    await store.setPersonFile(image)
    const sizeText = `${store.person ? `${store.person.width}×${store.person.height}` : ''} ${
      store.person ? formatKb(store.person.bytes) : ''
    }`.trim()
    ElMessage.success(
      // 小尺寸 PNG 重编 JPEG 可能反而变大，文案不能一律写“已压缩”
      store.person && store.person.bytes >= store.person.originalBytes
        ? `已载入：${sizeText}（原图已足够小，未再缩小）`
        : `已压缩至长边 ≤1024：${sizeText}`,
    )
  } catch (error) {
    // 前端预检失败（格式/体积/分辨率）也走统一提示，不出现白屏
    ElMessage.error(describeError(error))
  } finally {
    loading.value = false
    if (inputRef.value) inputRef.value.value = ''
  }
}

function pick(): void {
  inputRef.value?.click()
}

function onDrop(event: DragEvent): void {
  dragging.value = false
  void handleFiles(event.dataTransfer?.files ?? null)
}

async function fetchSamplePerson(): Promise<File | null> {
  for (const name of SAMPLE_PERSONS) {
    const response = await fetch(`/static/samples/${name}`, { cache: 'no-store' })
    if (!response.ok) continue
    const blob = await response.blob()
    // blob 为空说明路由命中了目录页兜底，继续尝试下一个候选
    if (blob.size === 0) continue
    return new File([blob], name, { type: blob.type || 'image/png' })
  }
  return null
}

async function useSamplePerson(): Promise<void> {
  loading.value = true
  try {
    const file = await fetchSamplePerson()
    if (!file) {
      throw new Error('示例人像不存在，请先运行 python -m scripts.register_garments --person <图片> 或 --with-person')
    }
    await store.setPersonFile(file)
    ElMessage.success('已载入示例正身人像，可直接点击「一键试穿」')
  } catch (error) {
    ElMessage.error(describeError(error))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="uploader">
    <div
      class="drop-zone"
      :class="{ 'is-dragging': dragging, 'has-image': !!store.person }"
      @click="pick"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="inputRef"
        class="hidden-input"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/bmp"
        @change="handleFiles(($event.target as HTMLInputElement).files)"
      />

      <div v-if="store.person" class="preview">
        <img :src="store.person.dataUrl" alt="真人照片预览" />
        <div class="preview-meta">
          <span>{{ store.person.fileName }}</span>
          <span>{{ store.person.width }}×{{ store.person.height }}</span>
          <span>{{ formatKb(store.person.originalBytes) }} → {{ formatKb(store.person.bytes) }}</span>
          <span v-if="store.person.bytes >= store.person.originalBytes" class="grow-hint">
            原图已足够小（重编码略增大，不影响提交）
          </span>
        </div>
      </div>

      <div v-else class="placeholder">
        <el-icon :size="34"><Upload /></el-icon>
        <p class="placeholder-title">点击或拖拽上传真人照片</p>
        <p class="yisu-hint">
          正身、光线均匀、肩部完整的照片效果最佳；支持 JPG/PNG/WEBP/BMP，单张 ≤{{ MAX_INPUT_MB }}MB，
          前端自动压缩到长边 ≤1024 再以 Base64 提交
        </p>
      </div>

      <div v-if="loading" class="loading-mask">
        <el-icon class="is-loading" :size="22"><Loading /></el-icon>
        <span>正在压缩…</span>
      </div>
    </div>

    <div class="actions">
      <el-button v-if="store.person" type="danger" plain @click="store.clearPerson()">清除照片</el-button>
      <el-button :loading="loading" @click="useSamplePerson">使用示例人像</el-button>
    </div>
  </div>
</template>

<style scoped>
.uploader {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drop-zone {
  position: relative;
  border: 1px dashed var(--yisu-rice-deep);
  border-radius: var(--yisu-radius-lg);
  background: #fff;
  min-height: 300px;
  display: grid;
  place-items: center;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.drop-zone:hover,
.drop-zone.is-dragging {
  border-color: var(--yisu-vermilion);
  box-shadow: var(--yisu-shadow-hover);
}

.hidden-input {
  display: none;
}

.placeholder {
  text-align: center;
  padding: 28px 22px;
  color: var(--yisu-ink-soft);
  max-width: 360px;
}

.placeholder-title {
  font-family: var(--yisu-serif);
  font-size: 16px;
  margin: 10px 0 6px;
  color: var(--yisu-ink);
}

.preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview img {
  width: 100%;
  flex: 1;
  object-fit: contain;
  background: var(--yisu-rice);
  padding: 10px;
}

.preview-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--yisu-ink-soft);
  border-top: 1px solid var(--yisu-rice-deep);
  background: #fff;
}

.grow-hint {
  color: var(--yisu-vermilion);
}

.loading-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.82);
  color: var(--yisu-vermilion);
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
