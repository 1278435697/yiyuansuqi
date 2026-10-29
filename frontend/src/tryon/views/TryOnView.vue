<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ImageUploader from '@/tryon/components/ImageUploader.vue'
import GarmentPicker from '@/tryon/components/GarmentPicker.vue'
import PipelineStepper from '@/tryon/components/PipelineStepper.vue'
import ResultViewer from '@/tryon/components/ResultViewer.vue'
import { useAppStore } from '@/tryon/store/app'
import { useTryOnStore } from '@/tryon/store/tryon'
import { backendBadge } from '@/tryon/utils/backend'

const route = useRoute()
const app = useAppStore()
const store = useTryOnStore()

const batchMode = ref(false)
const batchIds = ref<string[]>([])

const selectedGarment = computed(() => app.garments.find((item) => item.id === store.selectedGarmentId) ?? null)

const submitHint = computed<string>(() => {
  if (!store.person) return '请先上传真人照片'
  if (batchMode.value && batchIds.value.length === 0) return '批量模式请至少勾选 1 件素材'
  if (!batchMode.value && !store.selectedGarmentId) return '请在右侧素材库选择一件服饰'
  return ''
})

const CACHE_HIT = 'result_from_cache'

async function submit(): Promise<void> {
  if (submitHint.value) {
    ElMessage.warning(submitHint.value)
    return
  }
  if (batchMode.value) {
    const list = await store.runBatch(batchIds.value)
    const ok = list.filter((item) => item.status === 'succeeded').length
    const cached = list.filter((item) => item.warnings.includes(CACHE_HIT)).length
    ElMessage.success(
      cached > 0 && cached === ok
        ? `批量试穿完成：${ok} 套全部命中缓存（与上次同一张图），勾选「跳过缓存强制重算」才会重跑`
        : `批量试穿完成：成功 ${ok} / ${list.length} 套`,
    )
  } else {
    const data = await store.run()
    if (data && data.status === 'succeeded') {
      if (data.warnings.includes(CACHE_HIT)) {
        // 命中缓存时 timings 回传的是首次真实推理的耗时，不能当成“这次很快”
        ElMessage.info('命中磁盘缓存：结果与上次完全相同。换素材 / 切 HD / 换照片，或勾选「跳过缓存强制重算」才会重跑')
      } else {
        ElMessage.success(
          `试穿完成（${backendBadge(data.backend_used).label}，总耗时 ${data.timings.total?.toFixed(2) ?? '—'}s）`,
        )
      }
    }
  }
  void app.refreshHealth()
}

/** 博物馆展厅「试穿此服饰」会带 ?garment=<素材 slug>，命中素材库就直接预选中。 */
function applyMuseumGarment(): void {
  const wanted = String(route.query.garment ?? '')
  if (!wanted) return
  const hit = app.garments.find((item) => item.id === wanted)
  if (hit) {
    store.selectedGarmentId = hit.id
    ElMessage.success(`已选中展厅带来的「${hit.name}」`)
  } else {
    ElMessage.warning(`素材库中没有标识为 ${wanted} 的服饰，请手动选择`)
  }
}

onMounted(async () => {
  await app.loadGarments()
  void app.refreshHealth()
  applyMuseumGarment()
})
</script>

<template>
  <div class="yisu-page">
    <div class="hero yisu-card">
      <div>
        <h2>上传真人照片 · 选择馆藏汉服 · 一键试穿</h2>
        <p class="yisu-hint">
          <template v-if="store.isCloud">
            云端管线：前端压缩（长边≤1024）→ 服饰图自动裁边 → Aidge 云端换装 → 结果落盘入库（云端不返回中间过程图）。
          </template>
          <template v-else>
            管线：前端压缩（长边≤1024）→ 人像分割 → COCO-17 姿态 → 服饰 9 关键点 TPS/HR-VITON 形变 →
            遮挡还原 + 光影匹配 + 边缘羽化 → 结果入库。
          </template>
          当前推理后端：
          <strong>{{ app.backendLabel }}</strong>
          <span v-if="app.health?.fallback_reason" class="fallback-reason">（{{ app.health.fallback_reason }}）</span>
        </p>
      </div>
      <el-radio-group v-model="store.quality" size="small">
        <el-radio-button value="fast">快速（1024/0.85）</el-radio-button>
        <el-radio-button value="hd">高清 HD</el-radio-button>
      </el-radio-group>
    </div>

    <div class="yisu-split">
      <section class="yisu-card left">
        <h3 class="yisu-section-title">① 真人照片</h3>
        <ImageUploader />

        <h3 class="yisu-section-title step-gap">② 生成设置</h3>
        <div class="settings">
          <el-switch v-model="batchMode" active-text="批量连续试穿（加分项）" />
          <el-switch v-model="store.forceRefresh" active-text="跳过缓存强制重算" />
          <p v-if="store.forceRefresh" class="yisu-hint">
            <template v-if="store.isCloud">
              本次会跳过磁盘缓存重新调用云端（约 3–10 秒，消耗一次云端额度）；云端出图可能与上次有细微差异。
            </template>
            <template v-else>
              本次会忽略磁盘缓存重新跑一遍推理（CPU 兜底路径约 1–5 秒）。注意管线是确定性的，
              同一照片 + 同一服饰 + 同一画质重跑结果仍会一模一样。
            </template>
          </p>
          <p v-if="batchMode" class="yisu-hint">
            在右侧勾选多件素材，一次提交由后端顺序产出多套效果图（单次最多 8 件）。
          </p>
          <p v-else-if="selectedGarment" class="yisu-hint">
            已选：<strong>{{ selectedGarment.name }}</strong>（{{ selectedGarment.dynasty }} ·
            {{ app.categoryLabel(selectedGarment.category) }}）
          </p>
          <div class="submit-row">
            <el-button type="primary" size="large" :loading="store.busy" :disabled="!!submitHint" @click="submit">
              {{ batchMode ? `一键试穿 ${batchIds.length} 套` : '一键试穿' }}
            </el-button>
            <el-button v-if="store.busy" @click="store.cancel()">取消</el-button>
            <span v-if="submitHint" class="yisu-hint">{{ submitHint }}</span>
          </div>
          <el-alert v-if="store.error" type="error" show-icon :closable="false" :title="store.error" />
        </div>
      </section>

      <section class="yisu-card right">
        <h3 class="yisu-section-title">③ 效果输出</h3>
        <PipelineStepper />
        <el-divider style="margin: 6px 0" />
        <ResultViewer :result="store.result" :person-preview="store.person?.dataUrl ?? null" />
      </section>
    </div>

    <section class="yisu-card">
      <h3 class="yisu-section-title">
        服饰素材库
        <span class="title-note">
          {{ batchMode ? '多选模式：点击卡片加入批量队列' : '单选模式：点击卡片选择试穿目标' }}
        </span>
      </h3>
      <GarmentPicker
        v-model="store.selectedGarmentId"
        :multiple="batchMode"
        v-model:selected-ids="batchIds"
        :height="170"
      />
    </section>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.hero h2 {
  margin: 0 0 6px;
  font-family: var(--yisu-serif);
  font-size: 20px;
}

.fallback-reason {
  color: var(--yisu-ink-soft);
  font-size: 12px;
}

.left,
.right {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-gap {
  margin-top: 8px;
}

.settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.submit-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.title-note {
  font-size: 12px;
  font-weight: 400;
  color: var(--yisu-ink-soft);
  margin-left: 8px;
}
</style>
