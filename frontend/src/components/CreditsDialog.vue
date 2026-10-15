<script setup>
import { computed } from 'vue';

const props = defineProps({
  open: { type: Boolean, default: false },
  entries: { type: Array, default: () => [] },
});
const emit = defineEmits(['close']);

const grouped = computed(() => {
  const map = new Map();
  for (const e of props.entries) {
    if (!map.has(e.museum)) map.set(e.museum, []);
    map.get(e.museum).push(e);
  }
  return [...map.entries()].map(([museum, items]) => ({ museum, items }));
});
</script>

<template>
  <div v-if="open" class="mask" @click.self="emit('close')">
    <div class="dialog">
      <div class="head">
        <div class="t">图片来源与版权说明</div>
        <button class="close" @click="emit('close')">×</button>
      </div>
      <div class="body">
        <p class="intro">
          本展厅陈列影像均采集自权威博物馆官方网站，已下载至本地并标注来源，仅用于教学与竞赛演示，不作商用。
          如需引用，请以各馆官网发布信息为准。
        </p>
        <div v-for="g in grouped" :key="g.museum" class="group">
          <div class="museum">{{ g.museum }}</div>
          <ul>
            <li v-for="it in g.items" :key="it.url + it.text">
              <span class="name">{{ it.text }}</span>
              <span class="exh">{{ it.exhibition }}</span>
              <a :href="it.url" target="_blank" rel="noreferrer">{{ it.url }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: absolute;
  inset: 0;
  z-index: 34;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(8, 6, 5, 0.66);
  backdrop-filter: blur(3px);
}

.dialog {
  width: min(720px, 94vw);
  max-height: 84vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #241a14, #1b120e);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.45);
  border-radius: 8px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(var(--silk-gold-rgb), 0.24);
}

.t {
  font-size: 15px;
  letter-spacing: 2px;
  color: var(--silk-gold-soft);
}

.close {
  width: 28px;
  height: 28px;
  font-size: 19px;
  color: #d8c8a8;
  background: transparent;
  border: none;
}

.body {
  overflow-y: auto;
  padding: 16px 18px;
  font-size: 12.5px;
  color: #b8ac96;
}

.intro {
  margin: 0 0 16px;
  line-height: 1.9;
  color: #cbbfa9;
  text-align: justify;
}

.group + .group {
  margin-top: 14px;
}

.museum {
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--silk-gold);
  letter-spacing: 1px;
}

.group ul {
  margin: 0;
  padding-left: 16px;
}

.group li {
  margin-bottom: 8px;
  line-height: 1.7;
  word-break: break-all;
}

.name {
  color: #ded2b8;
  margin-right: 6px;
}

.exh {
  color: #8f8571;
  margin-right: 6px;
}
</style>
