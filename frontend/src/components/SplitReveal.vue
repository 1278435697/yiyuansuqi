<template>
  <Teleport to="body">
    <div v-if="visible" class="sr-mask" @click.self="close">
      <div class="sr-head">
        <span class="sr-title">{{ title }}</span>
        <button class="sr-close" @click="close" aria-label="关闭">✕</button>
      </div>
      <div class="sr-stage" ref="stageRef">
        <div
          v-for="(card, i) in cards"
          :key="i"
          class="sr-card"
          ref="cardRefs"
          @click="pick(i)"
        >
          <div class="sr-img">
            <img v-if="card.image" :src="card.image" :alt="card.title" loading="lazy" />
            <div v-else class="sr-noimg">{{ card.kicker }}</div>
            <span class="sr-kicker">{{ card.kicker }}</span>
          </div>
          <div class="sr-body">
            <h3>{{ card.title }}</h3>
            <p>{{ card.text }}</p>
            <ul v-if="card.list?.length" class="sr-list">
              <li v-for="(it, k) in card.list.slice(0, 4)" :key="k">
                <b>{{ it.label }}</b>{{ it.value }}
              </li>
            </ul>
            <span class="sr-enter">查看详情 ↗</span>
          </div>
        </div>
      </div>
      <p class="sr-tip">点击任意一张卡片，查看该素材详情</p>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import gsap from "gsap";

const props = defineProps<{
  visible: boolean;
  title?: string;
  cards: any[];
}>();
const emit = defineEmits<{ (e: "close"): void; (e: "select", index: number): void }>();

const stageRef = ref<HTMLElement | null>(null);
const cardRefs = ref<HTMLElement[]>([]);

function close() {
  emit("close");
}
function pick(i: number) {
  emit("select", i);
}

/* 打开：图片从中心放大、卡片分裂翻转入场 */
watch(
  () => props.visible,
  async (v) => {
    if (!v) return;
    await nextTick();
    const cards = cardRefs.value.filter(Boolean);
    if (!cards.length) return;
    gsap.killTweensOf(cards);
    cards.forEach((card, i) => {
      const img = card.querySelector(".sr-img img");
      gsap.fromTo(
        card,
        { clipPath: "inset(0 50% 0 50%)", scale: 0.62, opacity: 0, rotationY: -24 },
        {
          clipPath: "inset(0 0% 0 0%)",
          scale: 1,
          opacity: 1,
          rotationY: 0,
          duration: 0.7,
          ease: "power3.inOut",
          delay: i * 0.13,
        }
      );
      if (img) {
        gsap.fromTo(img, { scale: 1.22 }, { scale: 1, duration: 1.1, ease: "power2.out", delay: i * 0.13 });
      }
    });
  }
);
</script>

<style scoped>
.sr-mask {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(24, 16, 8, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 24px;
}
.sr-head {
  width: min(1080px, 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sr-title {
  color: #f5efe4;
  font-size: 20px;
  letter-spacing: 3px;
  font-family: "Songti SC", "SimSun", serif;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}
.sr-close {
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.08);
  color: #f5efe4;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.25s;
}
.sr-close:hover {
  background: rgba(255, 255, 255, 0.22);
  transform: rotate(90deg);
}
.sr-stage {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  width: min(1080px, 100%);
  perspective: 1200px;
}
.sr-card {
  position: relative;
  background: linear-gradient(160deg, #fbf6ec, #f1e7d6);
  border: 1px solid rgba(120, 80, 40, 0.25);
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  will-change: transform, clip-path;
  transform-style: preserve-3d;
}
.sr-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 26px 56px rgba(0, 0, 0, 0.45);
}
.sr-img {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #e8dcc8;
}
.sr-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.sr-noimg {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8a6d46;
  background:
    radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.55), transparent 60%),
    repeating-linear-gradient(45deg, rgba(150, 110, 60, 0.06) 0 8px, transparent 8px 16px);
  font-size: 15px;
  letter-spacing: 4px;
}
.sr-kicker {
  position: absolute;
  left: 12px;
  bottom: 10px;
  color: #fff;
  font-size: 12px;
  letter-spacing: 2px;
  background: rgba(122, 34, 24, 0.82);
  padding: 3px 10px;
  border-radius: 20px;
}
.sr-body {
  padding: 14px 16px 18px;
  color: #3c2a18;
}
.sr-body h3 {
  font-size: 17px;
  margin: 0 0 8px;
  font-family: "Songti SC", "SimSun", serif;
  letter-spacing: 1px;
}
.sr-body p {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.7;
  color: #6b5640;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.sr-list {
  margin: 0 0 10px;
  padding: 0;
  list-style: none;
}
.sr-list li {
  font-size: 12.5px;
  line-height: 1.8;
  color: #6b5640;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sr-list b {
  color: #a1231a;
  margin-right: 6px;
}
.sr-enter {
  display: inline-block;
  font-size: 12.5px;
  color: #a1231a;
  border-bottom: 1px solid rgba(161, 35, 26, 0.5);
  padding-bottom: 1px;
}
.sr-tip {
  color: rgba(245, 239, 228, 0.75);
  font-size: 13px;
  letter-spacing: 1px;
  margin: 0;
}
@media (max-width: 768px) {
  .sr-stage {
    grid-template-columns: 1fr;
    gap: 16px;
    overflow-y: auto;
    max-height: 78vh;
  }
}
</style>
