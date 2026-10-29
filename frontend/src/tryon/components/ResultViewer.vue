<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import TraceCard from '@/tryon/components/TraceCard.vue'
import type { TryOnResult } from '@/tryon/types'
import { buildSnapshotName, downloadRemoteImage, snapshotImage } from '@/tryon/utils/snapshot'
import { describeError } from '@/tryon/api/client'
import { backendBadge } from '@/tryon/utils/backend'

const props = defineProps<{ result: TryOnResult | null; personPreview: string | null }>()

const compareMode = ref<'result' | 'source' | 'side'>('result')
const snapshotStep = ref(5)

const intermediates = computed<{ key: string; label: string; url: string | null; hint: string }[]>(() => [
  {
    key: 'person_mask_url',
    label: '① 人像分割掩码',
    url: props.result?.person_mask_url ?? null,
    hint: 'Provider 链：VitonGPCI → U2Net → MediaPipe → GrabCut',
  },
  {
    key: 'pose_overlay_url',
    label: '② 姿态 17 关键点',
    url: props.result?.pose_overlay_url ?? null,
    hint: 'COCO-17 骨架 + 肩线/腰线/衣摆锚点',
  },
  {
    key: 'garment_warp_url',
    label: '③ 服饰形变结果',
    url: props.result?.garment_warp_url ?? null,
    hint: '9 关键点 TPS 控制点求解后的贴图',
  },
])

const isCloudResult = computed<boolean>(() => props.result?.backend_used === 'aidge')

const backendTag = computed(() => {
  const badge = backendBadge(props.result?.backend_used)
  return { type: badge.tagType, text: badge.label }
})

async function downloadResult(): Promise<void> {
  const url = props.result?.result_url
  if (!url) return
  try {
    await downloadRemoteImage(url, `yisu_tryon_${props.result?.task_id ?? 'task'}.jpg`)
    ElMessage.success('结果图已下载')
  } catch (error) {
    ElMessage.error(describeError(error))
  }
}

async function takeSnapshot(): Promise<void> {
  const url = props.result?.result_url
  if (!url) return
  try {
    const name = buildSnapshotName(
      snapshotStep.value,
      `tryon_${props.result?.trace_card?.name ?? props.result?.task_id ?? 'result'}`,
    )
    await snapshotImage(url, name, {
      title: `衣溯 · 华夏衣冠志 · ${props.result?.trace_card?.name ?? '虚拟试穿效果'}`,
      subtitle: props.result?.trace_card ? `${props.result.trace_card.dynasty} / ${props.result.trace_card.category}` : undefined,
      taskId: props.result?.task_id ?? undefined,
      backend: props.result?.backend_used ?? undefined,
    })
    ElMessage.success(`已生成 ${name}，请放入仓库根目录 oneoff/`)
  } catch (error) {
    ElMessage.error(describeError(error))
  }
}
</script>

<template>
  <div class="viewer">
    <div v-if="props.result?.result_url" class="stage">
      <div class="stage-tools">
        <el-radio-group v-model="compareMode" size="small">
          <el-radio-button value="result">效果图</el-radio-button>
          <el-radio-button value="source">原图</el-radio-button>
          <el-radio-button value="side">对比</el-radio-button>
        </el-radio-group>
        <div class="stage-tags">
          <el-tag :type="backendTag.type" effect="dark" size="small">{{ backendTag.text }}</el-tag>
          <el-tag v-if="props.result.status !== 'succeeded'" type="danger" size="small">
            {{ props.result.status }}
          </el-tag>
        </div>
      </div>

      <div class="images" :class="{ 'is-side': compareMode === 'side' }">
        <figure v-if="compareMode !== 'source'" class="image-box">
          <img :src="props.result.result_url" alt="试穿效果图" />
          <figcaption>试穿效果图</figcaption>
        </figure>
        <figure v-if="compareMode === 'source' || compareMode === 'side'" class="image-box">
          <img v-if="props.personPreview" :src="props.personPreview" alt="原始照片" />
          <div v-else class="yisu-empty">原图预览已清除，可在「试穿记录」查看留档</div>
          <figcaption>原始照片</figcaption>
        </figure>
      </div>

      <div class="actions">
        <el-button type="primary" @click="downloadResult">下载效果图</el-button>
        <el-button @click="takeSnapshot">生成答辩截图 PNG</el-button>
        <el-input-number v-model="snapshotStep" :min="1" :max="99" size="small" controls-position="right" style="width: 108px" />
        <span class="yisu-hint">截图命名 oneoff/step{{ String(snapshotStep).padStart(2, '0') }}_…</span>
      </div>
    </div>

    <div v-else class="yisu-empty">
      {{ props.result ? '本次试穿未产出结果图，请检查告警或更换更清晰的正身照片。' : '上传真人照片并选择服饰后，点击「一键试穿」生成效果图。' }}
    </div>

    <el-collapse v-if="props.result && !isCloudResult" class="pipeline">
      <el-collapse-item title="管线中间图（答辩展示：几何变形 → 渲染 → 合成）" name="pipe">
        <div class="pipe-grid">
          <div v-for="item in intermediates" :key="item.key" class="pipe-item">
            <p class="pipe-title">{{ item.label }}</p>
            <img v-if="item.url" :src="item.url" :alt="item.label" />
            <div v-else class="yisu-empty">该阶段未产出</div>
            <p class="yisu-hint">{{ item.hint }}</p>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <p v-if="isCloudResult" class="yisu-hint">
      本次由 Aidge 云端引擎出图，云端只返回最终效果图，不提供人像分割 / 姿态 / 服饰形变的中间图。
    </p>

    <TraceCard v-if="props.result" :card="props.result.trace_card" />
  </div>
</template>

<style scoped>
.viewer {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.stage {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-tools,
.stage-tags {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.stage-tags {
  margin-left: auto;
}

.images {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr);
}

.images.is-side {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.image-box {
  margin: 0;
  border: 1px solid var(--yisu-rice-deep);
  border-radius: var(--yisu-radius);
  overflow: hidden;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.image-box img {
  width: 100%;
  max-height: 60vh;
  object-fit: contain;
  background: var(--yisu-rice);
}

.image-box figcaption {
  padding: 6px 10px;
  font-size: 12px;
  color: var(--yisu-ink-soft);
  border-top: 1px solid var(--yisu-rice-deep);
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.pipe-item img {
  width: 100%;
  border: 1px solid var(--yisu-rice-deep);
  border-radius: 6px;
  background: var(--yisu-rice);
}

.pipe-title {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
}
</style>
