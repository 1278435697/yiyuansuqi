<script setup lang="ts">
import { computed } from 'vue'
import type { TraceCard } from '@/tryon/types'

const props = defineProps<{ card: TraceCard | null }>()

const referenceList = computed<string[]>(() =>
  Array.isArray(props.card?.references) ? props.card.references.filter((item) => typeof item === 'string' && item) : [],
)

const hasContent = computed<boolean>(() => Boolean(props.card && (props.card.source_text || referenceList.value.length)))
</script>

<template>
  <div v-if="props.card" class="trace-card">
    <div class="trace-head">
      <span class="trace-seal">溯</span>
      <div>
        <strong>{{ props.card.name }}</strong>
        <span class="trace-sub">{{ props.card.dynasty }} · {{ props.card.category }}</span>
      </div>
    </div>

    <div v-if="props.card.source_text" class="trace-text">
      <p class="trace-label">文献溯源</p>
      <p class="quote">{{ props.card.source_text }}</p>
    </div>

    <div v-if="referenceList.length" class="trace-refs">
      <p class="trace-label">参考文献 / 图源</p>
      <ol>
        <li v-for="ref in referenceList" :key="ref">{{ ref }}</li>
      </ol>
    </div>

    <p v-if="!hasContent" class="yisu-hint">该素材暂无史料记载，可在 index.json 补充 source_text / references。</p>
  </div>
  <div v-else class="yisu-empty">选择素材库中的馆藏服饰后，这里会显示对应的史料溯源卡片。</div>
</template>

<style scoped>
.trace-card {
  border: 1px solid var(--yisu-rice-deep);
  border-left: 4px solid var(--yisu-gold);
  border-radius: var(--yisu-radius);
  background: linear-gradient(180deg, #fffdf8 0%, var(--yisu-rice) 100%);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trace-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trace-head strong {
  font-family: var(--yisu-serif);
  font-size: 17px;
  display: block;
}

.trace-sub {
  font-size: 12px;
  color: var(--yisu-ink-soft);
}

.trace-seal {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: var(--yisu-gold);
  color: #fff;
  font-family: var(--yisu-serif);
}

.trace-label {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 1px;
  color: var(--yisu-vermilion-dark);
}

.quote {
  margin: 0;
  font-family: var(--yisu-serif);
  font-size: 14px;
  line-height: 1.9;
  color: var(--yisu-ink);
  padding-left: 10px;
  border-left: 2px solid var(--yisu-rice-deep);
}

.trace-refs ol {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: var(--yisu-ink-soft);
  line-height: 1.8;
}
</style>
