<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  exhibit: { type: Object, default: null },
});
const emit = defineEmits(['close', 'tryon', 'ask']);

const activeIndex = ref(0);
watch(
  () => props.exhibit,
  () => {
    activeIndex.value = 0;
  },
);

const activeImage = computed(() => (props.exhibit ? props.exhibit.images[activeIndex.value] : null));
</script>

<template>
  <div v-if="exhibit" class="mask" @click.self="emit('close')">
    <div class="card">
      <button class="close" @click="emit('close')">×</button>

      <div class="card-body">
        <!-- 真实文物图 -->
        <div class="media">
          <div class="main-image">
            <img :src="activeImage.src" :alt="activeImage.caption" />
          </div>
          <div class="thumbs">
            <button
              v-for="(img, i) in exhibit.images"
              :key="img.src"
              :class="{ on: i === activeIndex }"
              @click="activeIndex = i"
            >
              <img :src="img.src" :alt="img.caption" />
            </button>
          </div>
          <div class="caption">{{ activeImage.caption }}</div>
          <div class="real-note">真实文物影像 · 来源：{{ exhibit.credits[0].museum }}</div>
        </div>

        <!-- 史料信息 -->
        <div class="info">
          <div class="dynasty">{{ exhibit.dynasty }}</div>
          <h2>{{ exhibit.name }}</h2>
          <div class="chips">
            <span>{{ exhibit.category }}</span>
            <span v-for="c in exhibit.colors" :key="c" class="swatch" :style="{ background: c }" />
          </div>

          <dl class="meta">
            <div><dt>纹样</dt><dd>{{ exhibit.pattern }}</dd></div>
            <div><dt>材质</dt><dd>{{ exhibit.material }}</dd></div>
          </dl>

          <p class="history">{{ exhibit.history }}</p>

          <ul class="highlights">
            <li v-for="h in exhibit.highlights" :key="h">{{ h }}</li>
          </ul>

          <div class="credits">
            <div class="ct">图片来源</div>
            <div v-for="c in exhibit.credits" :key="c.url" class="credit-item">
              {{ c.text }} ｜ {{ c.museum }}<br />
              <span class="exh">{{ c.exhibition }}</span><br />
              <a :href="c.url" target="_blank" rel="noreferrer">{{ c.url }}</a>
            </div>
            <div class="license">仅用于教学 / 竞赛演示，不作商用。</div>
          </div>

          <div class="actions">
            <button v-if="exhibit.tryonId" class="primary" @click="emit('tryon', exhibit)">试穿此服饰</button>
            <button class="secondary" @click="emit('ask', exhibit)">问 AI 关于它</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: absolute;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 6, 5, 0.66);
  backdrop-filter: blur(3px);
  padding: 24px;
}

.card {
  position: relative;
  width: min(880px, 94vw);
  max-height: 88vh;
  overflow: auto;
  background: linear-gradient(180deg, #241a14, #1b120e);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.45);
  border-radius: 8px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}

.close {
  position: absolute;
  top: 8px;
  right: 12px;
  z-index: 2;
  width: 30px;
  height: 30px;
  font-size: 20px;
  line-height: 1;
  color: #d8c8a8;
  background: transparent;
  border: none;
}

.card-body {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 22px;
  padding: 22px;
}

.media {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.main-image {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f0c0a;
  border: 1px solid rgba(var(--silk-gold-rgb), 0.28);
  border-radius: 6px;
  overflow: hidden;
}

.main-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.thumbs {
  display: flex;
  gap: 8px;
}

.thumbs button {
  flex: 1;
  height: 58px;
  padding: 0;
  background: #0f0c0a;
  border: 1px solid rgba(var(--silk-gold-rgb), 0.25);
  border-radius: 4px;
  overflow: hidden;
}

.thumbs button.on {
  border-color: var(--silk-gold);
  box-shadow: 0 0 0 1px var(--silk-gold);
}

.thumbs img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.caption {
  font-size: 12px;
  color: #cfc1a6;
}

.real-note {
  font-size: 11px;
  color: #8e8471;
}

.info h2 {
  margin: 2px 0 10px;
  font-size: 26px;
  letter-spacing: 3px;
  color: var(--silk-gold-soft);
}

.dynasty {
  display: inline-block;
  padding: 2px 10px;
  font-size: 12px;
  letter-spacing: 2px;
  color: #f7edd9;
  background: var(--ink-red);
  border-radius: 3px;
}

.chips {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0 14px;
}

.chips span {
  padding: 2px 8px;
  font-size: 12px;
  color: #cfc1a6;
  background: rgba(var(--silk-gold-rgb), 0.12);
  border-radius: 3px;
}

.swatch {
  width: 16px;
  height: 16px;
  padding: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin: 0 0 12px;
}

.meta dt {
  font-size: 12px;
  color: #93876f;
}

.meta dd {
  margin: 2px 0 0;
  font-size: 13px;
  color: #e3d8c2;
}

.history {
  margin: 0 0 12px;
  font-size: 13.5px;
  line-height: 1.85;
  color: #cdc0a8;
  text-align: justify;
}

.highlights {
  margin: 0 0 16px;
  padding-left: 18px;
  font-size: 13px;
  color: #d6c9ae;
  line-height: 1.8;
}

.credits {
  padding: 10px 12px;
  margin-bottom: 16px;
  font-size: 11.5px;
  line-height: 1.7;
  color: #a89b83;
  background: rgba(var(--silk-gold-rgb), 0.06);
  border-left: 2px solid rgba(var(--silk-gold-rgb), 0.5);
  border-radius: 3px;
  word-break: break-all;
}

.ct {
  margin-bottom: 4px;
  font-size: 12px;
  color: #d8c8a8;
  letter-spacing: 1px;
}

.credit-item + .credit-item {
  margin-top: 6px;
}

.exh {
  color: #93876f;
}

.license {
  margin-top: 8px;
  color: #7e7462;
}

.actions {
  display: flex;
  gap: 12px;
}

.actions button {
  flex: 1;
  padding: 11px 0;
  font-size: 14px;
  letter-spacing: 2px;
  border-radius: 4px;
}

.primary {
  color: #1a1310;
  background: linear-gradient(180deg, var(--silk-gold-soft), var(--silk-gold));
  border: 1px solid var(--silk-gold);
  font-weight: 600;
}

.secondary {
  color: var(--silk-gold-soft);
  background: transparent;
  border: 1px solid rgba(var(--silk-gold-rgb), 0.55);
}

@media (max-width: 720px) {
  .card-body {
    grid-template-columns: 1fr;
  }
  .main-image {
    height: 220px;
  }
}
</style>
