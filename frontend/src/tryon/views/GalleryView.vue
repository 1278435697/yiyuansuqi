<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import GarmentPicker from '@/tryon/components/GarmentPicker.vue'
import TraceCard from '@/tryon/components/TraceCard.vue'
import { useAppStore } from '@/tryon/store/app'
import { useTryOnStore } from '@/tryon/store/tryon'
import { fetchTraceCard } from '@/tryon/api/garments'
import { describeError } from '@/tryon/api/client'
import type { Garment, TraceCard as TraceCardType } from '@/tryon/types'

const app = useAppStore()
const tryOn = useTryOnStore()
const router = useRouter()

const active = ref<Garment | null>(null)
const activeCard = ref<TraceCardType | null>(null)
const drawer = ref(false)
const loadingCard = ref(false)

const keypointColors: Record<string, string> = {
  collar_center: '#b03a2e',
  shoulder_L: '#c8a45c',
  shoulder_R: '#c8a45c',
  sleeve_L_end: '#4b7f6e',
  sleeve_R_end: '#4b7f6e',
  waist_L: '#2f6f9e',
  waist_R: '#2f6f9e',
  hem_L: '#6b4b9e',
  hem_R: '#6b4b9e',
}

async function open(garment: Garment): Promise<void> {
  active.value = garment
  activeCard.value = null
  drawer.value = true
  loadingCard.value = true
  try {
    activeCard.value = await fetchTraceCard(garment.id)
  } catch (error) {
    // 素材本身带 source_text 时可直接降级展示，不阻塞抽屉
    activeCard.value = {
      garment_id: garment.id,
      name: garment.name,
      dynasty: garment.dynasty,
      category: app.categoryLabel(garment.category),
      source_text: garment.source_text,
      references: garment.references,
    }
    console.warn('[gallery] 溯源接口不可用，回落到列表数据', describeError(error))
  } finally {
    loadingCard.value = false
  }
}

function goTryOn(): void {
  if (!active.value) return
  tryOn.selectGarment(active.value.id)
  drawer.value = false
  void router.push({ name: 'tryon' })
}

const summary = computed(() => ({
  total: app.garments.length,
  dynasties: app.dynasties.length,
  categories: app.categories.length,
}))

onMounted(() => {
  void app.loadGarments()
})
</script>

<template>
  <div class="yisu-page">
    <div class="yisu-card head">
      <h2>馆藏古代服饰素材库</h2>
      <p class="yisu-hint">
        共 {{ summary.total }} 件素材 · {{ summary.dynasties }} 个朝代 · {{ summary.categories }} 个品类。
        元数据来自 <code>backend/data/garments/index.json</code> 与 SQLite 双通道（DB 优先、磁盘兜底），
        每件均标注 9 个形变关键点（衣领/双肩/两袖/腰左右/衣摆左右）。
      </p>
    </div>

    <div class="yisu-card">
      <h3 class="yisu-section-title">筛选与浏览</h3>
      <GarmentPicker :model-value="tryOn.selectedGarmentId" :height="210" @pick="open" />
    </div>

    <el-drawer v-model="drawer" size="520px" :title="active?.name ?? '素材详情'" direction="rtl">
      <div v-if="active" class="detail">
        <div class="overlay-box">
          <img :src="active.image_url" :alt="active.name" />
          <svg viewBox="0 0 1 1" preserveAspectRatio="none" class="overlay">
            <polyline
              v-if="active.keypoints.length >= 3"
              :points="active.keypoints.map((k) => `${k.x},${k.y}`).join(' ')"
              fill="none"
              stroke="rgba(176,58,46,0.55)"
              stroke-width="0.006"
            />
            <circle
              v-for="kp in active.keypoints"
              :key="kp.name"
              :cx="kp.x"
              :cy="kp.y"
              r="0.012"
              :fill="keypointColors[kp.name] ?? '#1a1a1a'"
            />
          </svg>
        </div>
        <p class="yisu-hint">
          圆点为 TPS 形变控制点；配色区分衣领（朱红）、肩线（金）、袖口（青）、腰线（蓝）、衣摆（紫）。
        </p>

        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="ID">{{ active.id }}</el-descriptions-item>
          <el-descriptions-item label="朝代">{{ active.dynasty }}</el-descriptions-item>
          <el-descriptions-item label="品类">{{ app.categoryLabel(active.category) }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ active.tags.join('、') || '—' }}</el-descriptions-item>
          <el-descriptions-item label="关键点数">{{ active.keypoints.length }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />
        <div v-loading="loadingCard">
          <TraceCard :card="activeCard" />
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="goTryOn">用这件去试穿</el-button>
          <el-button @click="drawer = false">关闭</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.head h2 {
  margin: 0 0 6px;
  font-family: var(--yisu-serif);
  font-size: 20px;
}

.detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.overlay-box {
  position: relative;
  background: var(--yisu-rice);
  border: 1px solid var(--yisu-rice-deep);
  border-radius: var(--yisu-radius);
  overflow: hidden;
}

.overlay-box img {
  display: block;
  width: 100%;
  max-height: 380px;
  object-fit: contain;
}

.overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.detail-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
</style>
