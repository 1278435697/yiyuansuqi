<script setup lang="ts">
import { computed } from 'vue'
import { useTryOnStore } from '@/tryon/store/tryon'

const store = useTryOnStore()

const activeStep = computed<number>(() => {
  // 成功返回后 active 越过最后一步，全部节点转为 success 态
  if (store.result && !store.error) return store.steps.length
  if (!store.busy && !store.error) return -1
  const index = store.stageIndex
  return index >= 0 && index < store.steps.length ? index : -1
})

const BENIGN = new Set([
  'segmentation_vitongpu_unavailable',
  'segmentation_u2net_unavailable',
  'segmentation_fallback_to_mediapipe_selfie',
  'postprocess_skipped_no_warp_mask',
])
const warnings = computed<string[]>(() => (store.result?.warnings ?? []).filter((w) => !BENIGN.has(w)))
const fromCache = computed<boolean>(() => (store.result?.warnings ?? []).includes('result_from_cache'))

const progressHint = computed<string>(() => {
  if (store.busy) return store.isCloud ? '云端换装推理中（通常 3–10 秒）' : '推理中（CPU 兜底路径通常 1–5 秒，HD 模式更久）'
  if (store.error) return '本次未成功：可换一张正身、光线清晰的图片重试'
  if (store.result?.status === 'succeeded') {
    return fromCache.value
      ? '完成：命中磁盘缓存，返回的就是上次那张图（本次未重跑推理）'
      : '完成：结果已落盘并写入试穿记录，可下载或换一套继续'
  }
  return '等待提交'
})

const progressStatus = computed<'success' | 'exception' | 'warning' | undefined>(() => {
  if (store.error) return 'exception'
  if (store.progress >= 100) return 'success'
  return undefined
})

const timingRows = computed<{ stage: string; seconds: string }[]>(() => {
  const timings = store.result?.timings ?? {}
  const order = ['segmentation', 'pose', 'inference', 'postprocess', 'save', 'total']
  return order
    .filter((stage) => typeof timings[stage] === 'number')
    .map((stage) => ({ stage, seconds: (timings[stage] as number).toFixed(3) }))
})

/** 告警码 → 人话。原始 code 一并展示，方便对着后端日志排查。 */
const WARNING_LABELS: Record<string, string> = {
  segmentation_vitongpu_unavailable: 'VITON-GPU 分割权重缺失',
  segmentation_u2net_unavailable: 'U2-Net 分割权重缺失',
  segmentation_fallback_to_mediapipe_selfie: '人像分割降级到 MediaPipe Selfie',
  segmentation_fallback_to_heuristic: '人像分割降级到启发式 GrabCut',
  pose_fallback_to_mask_geometry: '姿态降级到掩码几何反推',
  edge_feather: '已做边缘羽化',
  background_preserved: '背景保持原样，未重绘',
  result_from_cache: '命中磁盘缓存：直接复用上次结果',
  cache_bypassed: '已按勾选跳过缓存，本次为真实重算',
  history_save_failed: '试穿记录入库失败（不影响出图）',
  aidge_cloud_backend: 'Aidge 云端引擎出图',
  aidge_cloth_trimmed: '服饰图已自动裁到主体（去掉多余留白）',
  aidge_cloth_flat_presentation: '本次使用该素材的云端平铺图',
  aidge_result_resized_to_source: '结果已缩放到与实拍原图同尺寸',
}

const WARNING_PREFIX_LABELS: Record<string, string> = {
  vton_fallback: '推理后端降级',
  batch_item_failed: '批量中某件失败',
}

function labelOf(code: string): string {
  const exact = WARNING_LABELS[code]
  if (exact) return exact
  if (code.startsWith('aidge_usage=')) return `云端用量：${code.slice('aidge_usage='.length)}`
  const index = code.indexOf(':')
  if (index > 0) {
    const prefix = code.slice(0, index)
    const label = WARNING_PREFIX_LABELS[prefix]
    if (label) return `${label}：${code.slice(index + 1)}`
  }
  return code
}
</script>

<template>
  <div class="stepper">
    <div class="progress-row">
      <el-progress
        :percentage="store.progress"
        :status="progressStatus"
        :indeterminate="store.busy && store.progress < 5"
        :duration="1.2"
        striped
        striped-flow
      />
      <span class="progress-hint">{{ progressHint }}</span>
    </div>

    <el-alert
      v-if="fromCache"
      type="warning"
      show-icon
      :closable="false"
      title="结果与上次完全相同（命中磁盘缓存）"
      :description="
        store.isCloud
          ? '云端每次换装都会消耗一次额度，所以同一照片 + 同一服饰默认直接复用缓存。想要新结果请勾选「跳过缓存强制重算」（会再次调用云端，且出图可能有细微差异）。下方阶段耗时是首次真实推理的记录值。'
          : '管线是确定性的：同一照片 + 同一服饰 + 同一画质必然得到同一张图。换一件素材、切 HD、换照片，或勾选「跳过缓存强制重算」才会重跑。下方阶段耗时是首次真实推理的记录值。'
      "
    />

    <el-steps :active="activeStep" align-center finish-status="success" class="steps">
      <el-step v-for="(step, index) in store.steps" :key="index" :title="step" />
    </el-steps>

    <el-collapse v-if="timingRows.length || warnings.length" class="detail">
      <el-collapse-item name="timings">
        <template #title>
          <span class="detail-title">阶段耗时（后端 timings 回填）</span>
        </template>
        <el-table :data="timingRows" size="small" border>
          <el-table-column prop="stage" label="阶段" min-width="140" />
          <el-table-column prop="seconds" label="秒" width="90" />
        </el-table>
      </el-collapse-item>
      <el-collapse-item v-if="warnings.length" name="warnings">
        <template #title>
          <span class="detail-title">降级 / 告警（{{ warnings.length }} 条，全部可见，绝不静默）</span>
        </template>
        <ul class="warnings">
          <li v-for="item in warnings" :key="item">
            <span class="warning-label">{{ labelOf(item) }}</span>
            <code>{{ item }}</code>
          </li>
        </ul>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<style scoped>
.stepper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-hint {
  font-size: 12px;
  color: var(--yisu-ink-soft);
}

.steps {
  padding: 6px 0 2px;
}

.steps :deep(.el-step__title) {
  font-size: 12px;
  line-height: 1.4;
}

.detail-title {
  font-size: 13px;
  color: var(--yisu-ink-soft);
}

.warnings {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.warnings code {
  background: var(--yisu-rice);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.warnings li {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.warning-label {
  font-size: 12px;
  color: var(--yisu-ink-soft);
}
</style>
