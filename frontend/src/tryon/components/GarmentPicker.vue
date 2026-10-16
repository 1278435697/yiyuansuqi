<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Check, PictureFilled, Search } from '@element-plus/icons-vue'
import { useAppStore } from '@/tryon/store/app'
import type { Garment } from '@/tryon/types'

const props = withDefaults(
  defineProps<{
    modelValue: string | null
    /** 批量模式：允许多选，配合「连续试穿」加分项 */
    multiple?: boolean
    selectedIds?: string[]
    height?: number
  }>(),
  { modelValue: null, multiple: false, selectedIds: () => [], height: 190 },
)

const emit = defineEmits<{
  (event: 'update:modelValue', value: string | null): void
  (event: 'update:selectedIds', value: string[]): void
  (event: 'pick', garment: Garment): void
}>()

const app = useAppStore()
const brokenThumbs = ref<Set<string>>(new Set())

const selectedSet = computed(() => new Set(props.multiple ? props.selectedIds : props.modelValue ? [props.modelValue] : []))

function toggle(garment: Garment): void {
  if (props.multiple) {
    const next = new Set(selectedSet.value)
    if (next.has(garment.id)) next.delete(garment.id)
    else next.add(garment.id)
    emit('update:selectedIds', Array.from(next))
  } else {
    emit('update:modelValue', garment.id)
  }
  emit('pick', garment)
}

function onThumbError(garment: Garment): void {
  // 缩略图加载失败时显示占位，而不是留下破图图标
  brokenThumbs.value = new Set([...brokenThumbs.value, garment.id])
}

const hasResults = computed(() => app.filteredGarments.length > 0)

onMounted(() => {
  void app.loadGarments()
})
</script>

<template>
  <div class="picker">
    <div class="filters">
      <el-input v-model="app.keyword" placeholder="搜索名称 / 标签 / 朝代" clearable class="filter-search">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="app.categoryFilter" placeholder="品类" class="filter-select">
        <el-option label="全部品类" :value="app.ALL" />
        <el-option v-for="item in app.categories" :key="item" :label="app.categoryLabel(item)" :value="item" />
      </el-select>
      <el-select v-model="app.dynastyFilter" placeholder="朝代" class="filter-select">
        <el-option label="全部朝代" :value="app.ALL" />
        <el-option v-for="item in app.dynasties" :key="item" :label="item" :value="item" />
      </el-select>
      <el-button text :loading="app.garmentsLoading" @click="app.loadGarments(true)">刷新</el-button>
    </div>

    <el-alert
      v-if="app.garmentsError"
      type="warning"
      show-icon
      :closable="false"
      :title="`素材库读取失败：${app.garmentsError}`"
      description="请确认后端已启动，且已执行 python -m scripts.gen_sample_garments 生成示例素材"
    />

    <div v-if="!app.garmentsLoading && !hasResults" class="yisu-empty">
      暂无匹配的素材。可运行 <code>python -m scripts.gen_sample_garments</code> 生成 6 件内置汉服，
      或把馆藏图片放入 <code>backend/data/garments/</code> 并在 <code>index.json</code> 里补 9 个关键点。
    </div>

    <div v-loading="app.garmentsLoading" class="grid" :style="{ '--thumb-height': `${height}px` }">
      <button
        v-for="garment in app.filteredGarments"
        :key="garment.id"
        type="button"
        class="garment-card"
        :class="{ 'is-active': selectedSet.has(garment.id) }"
        @click="toggle(garment)"
      >
        <div class="thumb">
          <img
            v-if="!brokenThumbs.has(garment.id)"
            :src="garment.thumb_url"
            :alt="garment.name"
            loading="lazy"
            @error="onThumbError(garment)"
          />
          <div v-else class="thumb-fallback">
            <el-icon :size="26"><PictureFilled /></el-icon>
            <span>缩略图缺失</span>
          </div>
          <span v-if="garment.dynasty" class="dynasty-tag">{{ garment.dynasty }}</span>
        </div>
        <div class="card-body">
          <strong>{{ garment.name }}</strong>
          <span class="card-sub">{{ app.categoryLabel(garment.category) }} · {{ garment.keypoints.length }} 关键点</span>
          <div v-if="garment.tags.length" class="tags">
            <el-tag v-for="tag in garment.tags.slice(0, 3)" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
          </div>
        </div>
        <el-icon v-if="selectedSet.has(garment.id)" class="check"><Check /></el-icon>
      </button>
    </div>
  </div>
</template>

<style scoped>
.picker {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.filter-search {
  width: 240px;
}

.filter-select {
  width: 140px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 14px;
  min-height: 120px;
}

.garment-card {
  position: relative;
  text-align: left;
  padding: 0;
  border: 1px solid var(--yisu-rice-deep);
  border-radius: var(--yisu-radius);
  background: #fff;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
  font-family: inherit;
  color: inherit;
}

.garment-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--yisu-shadow-hover);
}

.garment-card.is-active {
  border-color: var(--yisu-vermilion);
  box-shadow: 0 0 0 2px var(--yisu-vermilion-soft);
}

.thumb {
  position: relative;
  height: var(--thumb-height);
  background:
    repeating-linear-gradient(45deg, #faf7f0 0 10px, #f2ece0 10px 20px);
  display: grid;
  place-items: center;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.thumb-fallback {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  color: var(--yisu-ink-soft);
  font-size: 12px;
}

.dynasty-tag {
  position: absolute;
  left: 8px;
  top: 8px;
  background: rgba(26, 26, 26, 0.72);
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px 12px;
}

.card-body strong {
  font-family: var(--yisu-serif);
  font-size: 15px;
}

.card-sub {
  font-size: 12px;
  color: var(--yisu-ink-soft);
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.check {
  position: absolute;
  right: 8px;
  top: 8px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--yisu-vermilion);
  color: #fff;
  display: grid;
  place-items: center;
}
</style>
