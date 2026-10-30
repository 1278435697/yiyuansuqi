<template>
  <div class="yisu-preloader" :class="{ 'is-exiting': exiting }">
    <!-- 宣纸纹样背底 -->
    <div class="pl-bg"></div>

    <!-- 背景层：水印大字 + 淡墨远山 + 顶部天光 -->
    <div class="pl-watermark">衣冠上国</div>
    <div class="pl-mountains" aria-hidden="true">
      <svg viewBox="0 0 1440 260" preserveAspectRatio="none">
        <path class="m-m1" d="M0,200 C160,120 320,150 470,90 C610,40 760,110 900,60 C1080,0 1250,90 1440,40 L1440,260 L0,260 Z" />
        <path class="m-m2" d="M0,230 C200,170 380,205 560,150 C740,95 920,180 1100,130 C1240,90 1360,150 1440,120 L1440,260 L0,260 Z" />
        <path class="m-m3" d="M0,250 C240,215 480,235 720,200 C960,170 1200,215 1440,190 L1440,260 L0,260 Z" />
      </svg>
    </div>
    <div class="pl-sun" aria-hidden="true"></div>

    <!-- 四角回纹装饰 -->
    <span class="pl-corner c-tl" aria-hidden="true"></span>
    <span class="pl-corner c-tr" aria-hidden="true"></span>
    <span class="pl-corner c-bl" aria-hidden="true"></span>
    <span class="pl-corner c-br" aria-hidden="true"></span>

    <!-- 顶部小字标题 -->
    <div class="pl-top-title">
      <span class="tt-cn">衣源溯起</span>
      <span class="tt-en">YISU · CHRONICLE OF CHINESE COSTUME</span>
    </div>

    <!-- 中央：圆环预加载器 -->
    <div class="pl-stage">
      <!-- 圆环轨道 + 进度圆环 -->
      <div class="pl-ring-wrap" :class="{ 'is-done': done, 'is-btn': canEnter }" @click="enter">
        <!-- 圆环外圈旋转装饰点（与圆环同心） -->
        <div class="pl-orbit" aria-hidden="true">
          <span class="orb-dot d1"></span>
          <span class="orb-dot d2"></span>
          <span class="orb-dot d3"></span>
          <span class="orb-dot d4"></span>
          <span class="orb-dot d5"></span>
          <span class="orb-dot d6"></span>
          <span class="orb-dot d7"></span>
          <span class="orb-dot d8"></span>
        </div>

        <svg class="pl-ring" viewBox="0 0 320 320" aria-hidden="true">
          <circle class="pl-track" cx="160" cy="160" r="146" />
          <circle class="pl-progress" cx="160" cy="160" r="146" :style="{ strokeDashoffset: progressOffset }" />
        </svg>
        <!-- 中心：加载中显示 logo 印章；完成后圆环变按钮 -->
        <div class="pl-center">
          <template v-if="!canEnter">
            <span class="pl-seal">衣源溯起</span>
            <span class="pl-pct">{{ pct }}<i>%</i></span>
          </template>
          <template v-else>
            <span class="pl-enter-cn">点击进入</span>
            <span class="pl-enter-en">ENGAGE</span>
          </template>
        </div>
      </div>

      <!-- 圆环上下的装饰短线 -->
      <span class="pl-rule r-top" aria-hidden="true"></span>
      <span class="pl-rule r-bottom" aria-hidden="true"></span>

      <!-- 底部文案：轮换传统服饰诗句（绝对定位，不参与撑高） -->
      <transition name="pl-fade">
        <p :key="lineIdx" class="pl-poem">{{ poem }}</p>
      </transition>
      <p class="pl-sub" v-if="canEnter">ACCESS GRANTED · 衣冠启程</p>
    </div>

    <!-- 扫描层：进入时从左向右擦除 -->
    <div class="pl-reveal" :class="{ 'is-active': exiting }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from "vue";

const emit = defineEmits<{ (e: "done"): void }>();

const pct = ref(0);
const done = ref(false);      // 进度满
const canEnter = ref(false);  // 变为按钮
const exiting = ref(false);   // 扫描退场
const lineIdx = ref(0);

const POEMS = [
  "黄帝尧舜垂衣裳而天下治",
  "衣冠楚楚，华夏之仪",
  "交领右衽，天地之象",
  "罗衣何飘飘，轻裾随风还",
  "缃绮为下裙，紫绮为上襦",
];

let raf = 0;
let timer = 0;

const RING = 2 * Math.PI * 146; // 周长
const progressOffset = computed(() => String(RING * (1 - pct.value / 100)));

const poem = computed(() => POEMS[lineIdx.value]);

/* 进度用 setTimeout 驱动（切到后台标签页也继续走，不会卡住） */
function tick() {
  const start = Date.now();
  const dur = 2200;
  const step = () => {
    const t = Math.min((Date.now() - start) / dur, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    pct.value = Math.round(eased * 100);
    if (t < 1) {
      timer = window.setTimeout(step, 40);
    } else {
      finishLoad();
    }
  };
  step();
}

function finishLoad() {
  done.value = true;
  // logo 淡出 → 圆环变按钮
  timer = window.setTimeout(() => {
    canEnter.value = true;
    // 按钮出现后 3 秒自动进入，避免停在原地等点击
    timer = window.setTimeout(enter, 3000);
  }, 450);
}

function enter() {
  if (!canEnter.value || exiting.value) return;
  exiting.value = true;
  timer = window.setTimeout(() => emit("done"), 950);
}

function cyclePoem() {
  lineIdx.value = (lineIdx.value + 1) % POEMS.length;
  timer = window.setTimeout(cyclePoem, 1500);
}

onMounted(() => {
  tick();
  timer = window.setTimeout(cyclePoem, 700);
  // 兜底：加载超时也放行
  timer = window.setTimeout(() => {
    if (!done.value) {
      pct.value = 100;
      finishLoad();
    }
  }, 8000);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(raf);
  clearTimeout(timer);
});</script>

<style scoped>
/* ---------- 遮罩层 ---------- */
.yisu-preloader {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.pl-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 50% 38%, rgba(255, 252, 245, 0.98), rgba(247, 240, 227, 0.97) 70%),
    linear-gradient(180deg, #f7f0e3 0%, #efe4d2 100%);
}
/* 极淡回纹底纹 */
.pl-bg::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(178, 132, 86, 0.14) 1px, transparent 1px);
  background-size: 26px 26px;
}
.pl-bg::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 50%;
  width: 640px;
  height: 640px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(200, 164, 110, 0.16) 0%, transparent 62%);
  pointer-events: none;
}

/* ---------- 背景层装饰 ---------- */
.pl-watermark {
  position: absolute;
  right: -14px;
  top: 50%;
  transform: translateY(-50%);
  writing-mode: vertical-rl;
  font-family: "KaiTi", "STKaiti", serif;
  font-size: 150px;
  letter-spacing: 30px;
  color: rgba(168, 50, 42, 0.05);
  user-select: none;
  pointer-events: none;
}
.pl-mountains {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 30vh;
  min-height: 180px;
  pointer-events: none;
}
.pl-mountains svg {
  width: 100%;
  height: 100%;
}
.m-m1 { fill: rgba(140, 118, 92, 0.10); }
.m-m2 { fill: rgba(140, 118, 92, 0.16); }
.m-m3 { fill: rgba(120, 96, 72, 0.22); }
.pl-sun {
  position: absolute;
  left: 50%;
  top: 13vh;
  width: 190px;
  height: 190px;
  transform: translateX(-50%);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240, 214, 168, 0.5) 0%, rgba(240, 214, 168, 0) 70%);
  pointer-events: none;
}

/* ---------- 四角回纹 ---------- */
.pl-corner {
  position: absolute;
  width: 74px;
  height: 74px;
  pointer-events: none;
  opacity: 0.85;
}
.c-tl { left: 26px; top: 26px; border-left: 2px solid rgba(168, 50, 42, 0.5); border-top: 2px solid rgba(168, 50, 42, 0.5); }
.c-tl::before {
  content: "";
  position: absolute;
  left: 8px; top: 8px;
  width: 26px; height: 26px;
  border-left: 1px solid rgba(168, 50, 42, 0.3);
  border-top: 1px solid rgba(168, 50, 42, 0.3);
}
.c-tr { right: 26px; top: 26px; border-right: 2px solid rgba(168, 50, 42, 0.5); border-top: 2px solid rgba(168, 50, 42, 0.5); }
.c-tr::before {
  content: "";
  position: absolute;
  right: 8px; top: 8px;
  width: 26px; height: 26px;
  border-right: 1px solid rgba(168, 50, 42, 0.3);
  border-top: 1px solid rgba(168, 50, 42, 0.3);
}
.c-bl { left: 26px; bottom: 26px; border-left: 2px solid rgba(168, 50, 42, 0.5); border-bottom: 2px solid rgba(168, 50, 42, 0.5); }
.c-bl::before {
  content: "";
  position: absolute;
  left: 8px; bottom: 8px;
  width: 26px; height: 26px;
  border-left: 1px solid rgba(168, 50, 42, 0.3);
  border-bottom: 1px solid rgba(168, 50, 42, 0.3);
}
.c-br { right: 26px; bottom: 26px; border-right: 2px solid rgba(168, 50, 42, 0.5); border-bottom: 2px solid rgba(168, 50, 42, 0.5); }
.c-br::before {
  content: "";
  position: absolute;
  right: 8px; bottom: 8px;
  width: 26px; height: 26px;
  border-right: 1px solid rgba(168, 50, 42, 0.3);
  border-bottom: 1px solid rgba(168, 50, 42, 0.3);
}

/* ---------- 顶部标题 ---------- */
.pl-top-title {
  position: absolute;
  left: 50%;
  top: 7vh;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
}
.tt-cn {
  font-family: "KaiTi", "STKaiti", serif;
  font-size: 17px;
  letter-spacing: 10px;
  text-indent: 10px;
  color: #6b563c;
}
.tt-en {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: var(--ys-fs-micro);
  letter-spacing: 3px;
  text-transform: uppercase;
  color: rgba(107, 86, 60, 0.65);
}

/* ---------- 中央舞台 ---------- */
.pl-stage {
  position: relative;
  width: 240px;               /* 高度由圆环固定，诗句/副标题绝对定位不再撑高 */
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateY(-3vh);
}

/* 圆环外圈旋转装饰点（相对圆环容器同心定位） */
.pl-orbit {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 320px;
  height: 320px;
  margin: -160px 0 0 -160px;
  animation: pl-spin 26s linear infinite;
  pointer-events: none;
  z-index: 0;
}
.orb-dot {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 6px;
  height: 6px;
  margin: -3px 0 0 -3px;
  border-radius: 50%;
  background: rgba(168, 50, 42, 0.55);
}
.d1 { transform: rotate(0deg) translateX(160px); }
.d2 { transform: rotate(45deg) translateX(160px); background: rgba(178, 132, 86, 0.6); }
.d3 { transform: rotate(90deg) translateX(160px); }
.d4 { transform: rotate(135deg) translateX(160px); background: rgba(178, 132, 86, 0.6); }
.d5 { transform: rotate(180deg) translateX(160px); }
.d6 { transform: rotate(225deg) translateX(160px); background: rgba(178, 132, 86, 0.6); }
.d7 { transform: rotate(270deg) translateX(160px); }
.d8 { transform: rotate(315deg) translateX(160px); background: rgba(178, 132, 86, 0.6); }

.pl-ring-wrap {
  position: relative;
  width: 240px;
  height: 240px;
  cursor: default;
  z-index: 1;
}
.pl-ring-wrap.is-btn { cursor: pointer; }
.pl-ring {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.pl-track {
  fill: none;
  stroke: rgba(178, 132, 86, 0.28);
  stroke-width: 3;
}
.pl-progress {
  fill: none;
  stroke: #a8322a;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 917;
  transition: stroke-dashoffset 0.1s linear;
  filter: drop-shadow(0 0 4px rgba(168, 50, 42, 0.35));
}
/* 圆环内部 */
.pl-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: opacity 0.45s ease;
}
.pl-seal {
  font-family: "KaiTi", "STKaiti", "SimSun", serif;
  font-size: 46px;
  font-weight: 700;
  letter-spacing: 10px;
  text-indent: 10px;
  color: #a8322a;
  animation: pl-breathe 3.2s ease-in-out infinite;
}
.pl-pct {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 26px;
  color: #5c4a35;
  font-variant-numeric: tabular-nums;
  animation: pl-breathe 3.2s ease-in-out infinite;
}
.pl-pct i { font-style: normal; font-size: 14px; margin-left: 1px; }

/* 圆环上下装饰短线 */
.pl-rule {
  position: absolute;
  left: 50%;
  width: 120px;
  height: 1px;
  transform: translateX(-50%);
  background: linear-gradient(90deg, transparent, rgba(168, 50, 42, 0.45), transparent);
  pointer-events: none;
}
.pl-rule::after {
  content: "";
  position: absolute;
  left: 50%;
  top: -3px;
  width: 7px;
  height: 7px;
  transform: translateX(-50%) rotate(45deg);
  background: rgba(168, 50, 42, 0.6);
}
.r-top { top: -22px; }
.r-bottom { bottom: -22px; }

/* 完成后 → 按钮态 */
.pl-ring-wrap.is-btn .pl-center {
  animation: none;
}
.pl-enter-cn {
  font-size: 20px;
  letter-spacing: 8px;
  text-indent: 8px;
  color: #fff;
  background: #a8322a;
  padding: 10px 22px;
  border-radius: 999px;
  animation: pl-pulse 1.6s ease-in-out infinite;
}
.pl-enter-en {
  margin-top: 2px;
  font-family: "Georgia", serif;
  font-size: var(--ys-fs-micro);
  letter-spacing: 4px;
  color: #a8322a;
  opacity: 0.85;
}

/* 底部诗句：绝对定位固定于圆环下方，不参与撑高（圆环不再上下跳） */
.pl-poem {
  position: absolute;
  left: 50%;
  top: calc(100% + 34px);
  transform: translateX(-50%);
  margin: 0;
  font-family: "KaiTi", "STKaiti", serif;
  font-size: 18px;
  letter-spacing: 4px;
  color: #6b563c;
  white-space: nowrap;
}
.pl-sub {
  position: absolute;
  left: 50%;
  top: calc(100% + 66px);
  transform: translateX(-50%);
  margin: 0;
  font-family: "Georgia", serif;
  font-size: var(--ys-fs-micro);
  letter-spacing: 5px;
  text-transform: uppercase;
  color: #a8322a;
  opacity: 0.9;
  white-space: nowrap;
}
.pl-fade-enter-active, .pl-fade-leave-active { transition: opacity 0.5s ease; }
.pl-fade-enter-from, .pl-fade-leave-to { opacity: 0; }

/* 扫描退场层 */
.pl-reveal {
  position: absolute;
  inset: 0;
  z-index: 10;
  background: linear-gradient(90deg, #f7f0e3 0%, #fdf9f0 30%, #f4ead9 100%);
  background-image:
    linear-gradient(90deg, rgba(178, 132, 86, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, #f7f0e3 0%, #fdf9f0 30%, #f4ead9 100%);
  background-size: 40px 40px, 100% 100%;
  clip-path: inset(0 100% 0 0);
  pointer-events: none;
}
.pl-reveal.is-active {
  animation: pl-scan 0.95s cubic-bezier(0.65, 0, 0.25, 1) forwards;
}

/* ---------- 动画 ---------- */
@keyframes pl-breathe {
  0%, 100% { transform: translateY(0); opacity: 1; }
  50% { transform: translateY(-3px); opacity: 0.82; }
}
@keyframes pl-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(168, 50, 42, 0.35); }
  50% { transform: scale(1.04); box-shadow: 0 0 0 14px rgba(168, 50, 42, 0); }
}
@keyframes pl-scan {
  0% { clip-path: inset(0 100% 0 0); }
  100% { clip-path: inset(0 0 0 0); }
}
@keyframes pl-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
