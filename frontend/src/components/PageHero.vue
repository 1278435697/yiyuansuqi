<template>
  <!-- ============ 经典小横幅（AiQa / 社区 / 地图 / 时间轴 等沿用） ============ -->
  <section v-if="!grand" class="page-hero-full">
    <div class="ph-frame" aria-hidden="true"></div>
    <div class="ph-inner">
      <div class="ph-text">
        <span class="ph-kicker">{{ kicker }}</span>
        <RevealTitle :text="title" tag="h2" cls="ph-title" :delay="0.22" />
        <p class="ph-sub" style="animation-delay: .85s">{{ sub }}</p>
      </div>
      <div class="ph-seal" aria-hidden="true">{{ seal }}</div>
    </div>
    <div class="ph-fret" aria-hidden="true"></div>
  </section>

  <!-- ============ 大横幅 · 衣冠同款（档案 / 面料 / 纹样） ============ -->
  <section v-else class="gh-banner">
    <div class="gh-pattern" aria-hidden="true"></div>
    <div class="gh-inner">
      <div class="gh-copy">
        <div class="gh-eyebrow">
          <span class="gh-eyebrow-line"></span>
          {{ eyebrowEn }}<span class="gh-dot">·</span>{{ kicker }}
          <span class="gh-eyebrow-index">{{ eyebrowIndex }}</span>
        </div>
        <RevealTitle :text="title" tag="h1" cls="gh-title" :delay="0.3" :step="0.18" />
        <p class="gh-sub">{{ sub }}</p>
        <div class="gh-actions">
          <a class="gh-btn gh-btn-gold" :href="primaryHref">{{ primaryLabel }}<span>↘</span></a>
          <a class="gh-btn gh-btn-ghost" :href="secondaryHref">{{ secondaryLabel }}<span>↗</span></a>
        </div>
      </div>
      <div class="gh-art" aria-hidden="true">
        <div class="gh-orbit gh-orbit-a"></div>
        <div class="gh-orbit gh-orbit-b"></div>
        <div class="gh-orbit gh-orbit-c"></div>
        <div class="gh-seal">{{ seal }}</div>
        <div class="gh-vertical">{{ vertical }}</div>
      </div>
    </div>
    <div class="gh-stats">
      <div class="gh-stat" v-for="s in stats" :key="s.l"><b>{{ s.n }}</b><span>{{ s.l }}</span></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import RevealTitle from "./RevealTitle.vue";

withDefaults(defineProps<{
  title: string;
  kicker: string;
  sub: string;
  seal: string;
  /* grand 大横幅扩展 */
  grand?: boolean;
  eyebrowEn?: string;
  eyebrowIndex?: string;
  vertical?: string;
  primaryLabel?: string;
  primaryHref?: string;
  secondaryLabel?: string;
  secondaryHref?: string;
  stats?: Array<{ n: string; l: string }>;
}>(), {
  grand: false,
  eyebrowEn: "",
  eyebrowIndex: "",
  vertical: "",
  primaryLabel: "浏览本卷",
  primaryHref: "#catalog",
  secondaryLabel: "看出土地图",
  secondaryHref: "/geomap",
  stats: () => [
    { n: "09", l: "图谱大类" },
    { n: "93", l: "全量条目" },
    { n: "16", l: "本期服饰" },
    { n: "08", l: "阅读板块" },
  ],
});
</script>

<style scoped>
/* ================= 经典小横幅（原样保留） ================= */
.page-hero-full {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background:
    radial-gradient(1100px 360px at 85% -60%, rgba(185, 138, 47, .34), transparent 62%),
    linear-gradient(135deg, #7e2418 0%, #a93226 55%, #b98a2f 130%);
  color: #fff;
  padding: 30px 34px 34px;
  margin-bottom: 18px;
  box-shadow: 0 10px 26px rgba(122, 58, 32, .22);
}
.ph-frame {
  position: absolute;
  inset: 8px;
  z-index: 2;
  pointer-events: none;
  border: 1px solid rgba(255, 244, 214, .38);
  border-radius: 10px;
}
.ph-frame::before,
.ph-frame::after {
  content: "";
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(246, 231, 191, .9);
}
.ph-frame::before { top: -1px; left: -1px; border-right: none; border-bottom: none; border-top-left-radius: 10px; }
.ph-frame::after { bottom: -1px; right: -1px; border-left: none; border-top: none; border-bottom-right-radius: 10px; }
.page-hero-full::after {
  content: "";
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(246, 231, 191, .75), transparent);
}
.ph-inner {
  position: relative; z-index: 2;
  display: flex; justify-content: space-between; align-items: center; gap: 20px;
}
.ph-kicker {
  display: inline-block; font-size: 12px; letter-spacing: 3px; opacity: 0;
  animation: phKickerIn .7s ease-out forwards;
}
@keyframes phKickerIn {
  from { opacity: 0; letter-spacing: 10px; }
  to { opacity: .85; letter-spacing: 3px; }
}
.ph-title {
  margin: 8px 0 6px; font-size: 30px; letter-spacing: 2px; font-weight: 800; line-height: 1.35; color: inherit;
}
.ph-sub {
  margin: 0; font-size: 13.5px; opacity: 0; transform: translateY(10px);
  animation: phSubIn .7s ease-out forwards; color: rgba(255, 255, 255, .9);
}
@keyframes phSubIn {
  to { opacity: .92; transform: translateY(0); }
}
.ph-seal {
  flex: none; width: 64px; height: 64px; border: 3px solid rgba(255, 255, 255, .85);
  display: grid; place-items: center; border-radius: 10px; font-size: 30px; font-weight: 800;
  transform: rotate(8deg); color: #ffe9c9; background: rgba(126, 36, 24, .35);
  opacity: 0; animation: phSealIn .8s cubic-bezier(.3, 1.4, .5, 1) .25s forwards, phSealFloat 5s ease-in-out 1.4s infinite;
}
@keyframes phSealIn {
  0% { opacity: 0; transform: scale(.5) rotate(-24deg); }
  60% { opacity: 1; transform: scale(1.12) rotate(12deg); }
  100% { opacity: 1; transform: scale(1) rotate(8deg); }
}
@keyframes phSealFloat {
  0%, 100% { transform: rotate(8deg); }
  50% { transform: rotate(11deg) translateY(-3px); }
}
.ph-fret {
  position: absolute; inset: -40px; z-index: 1; pointer-events: none; opacity: .16;
  background-image:
    repeating-linear-gradient(45deg, transparent 0 18px, rgba(255, 255, 255, .5) 18px 20px),
    repeating-linear-gradient(-45deg, transparent 0 18px, rgba(255, 255, 255, .5) 18px 20px);
  mask-image: linear-gradient(to bottom, transparent, #000 40%);
  animation: phFretDrift 26s linear infinite;
}
@keyframes phFretDrift {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(40px, 40px, 0); }
}

/* ================= 大横幅 · 衣冠同款（1:1 复刻配饰 hero-banner） ================= */
.gh-banner {
  position: relative;
  min-height: 320px;
  padding: 36px 50px 78px;
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(260px, 0.75fr);
  gap: 24px;
  overflow: hidden;
  color: #f8e7c8;
  border-radius: 16px;
  background:
    radial-gradient(circle at 82% 34%, rgba(218, 170, 90, 0.22), transparent 24%),
    linear-gradient(120deg, #58130f 0%, #762019 48%, #9b3725 100%);
  box-shadow: 0 24px 70px rgba(86, 34, 20, 0.2);
  margin-bottom: 22px;
}
/* 斜纹暗格 */
.gh-banner::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(30deg, rgba(246, 216, 160, 0.05) 12%, transparent 12.5%, transparent 87%, rgba(246, 216, 160, 0.05) 87.5%, rgba(246, 216, 160, 0.05)),
    linear-gradient(150deg, rgba(246, 216, 160, 0.05) 12%, transparent 12.5%, transparent 87%, rgba(246, 216, 160, 0.05) 87.5%, rgba(246, 216, 160, 0.05));
  background-size: 64px 112px;
  opacity: 0.65;
  pointer-events: none;
}
/* 内嵌金线框 */
.gh-banner::after {
  content: "";
  position: absolute;
  inset: 12px;
  border: 1px solid rgba(236, 205, 143, 0.18);
  border-radius: 10px;
  pointer-events: none;
}
.gh-pattern {
  position: absolute;
  right: -90px;
  top: -120px;
  width: 460px;
  height: 460px;
  border: 1px solid rgba(236, 205, 143, 0.13);
  border-radius: 50%;
  box-shadow:
    0 0 0 42px rgba(236, 205, 143, 0.035),
    0 0 0 86px rgba(236, 205, 143, 0.025);
  pointer-events: none;
}
.gh-copy {
  position: relative;
  z-index: 2;
  align-self: center;
}
.gh-eyebrow {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(249, 231, 199, 0.7);
}
.gh-eyebrow-line {
  width: 34px;
  height: 1px;
  background: currentColor;
  opacity: 0.55;
}
.gh-dot { opacity: 0.5; margin: 0 2px; }
.gh-eyebrow-index {
  margin-left: 4px;
  padding-left: 12px;
  border-left: 1px solid currentColor;
  opacity: 0.62;
}
.gh-title {
  margin: 12px 0 14px;
  font-family: "KaiTi", "STKaiti", "Kaiti SC", "SimSun", serif;
  font-size: clamp(60px, 6vw, 92px);
  font-weight: 400;
  line-height: 0.84;
  letter-spacing: 0.06em;
  color: #f4d99f;
  text-shadow: 0 10px 30px rgba(38, 8, 4, 0.22);
}
.gh-title :deep(.rt-ch) {
  font-family: inherit;
}
.gh-sub {
  max-width: 620px;
  margin: 0;
  font-size: 15px;
  line-height: 2.05;
  letter-spacing: 0.08em;
  color: rgba(255, 241, 217, 0.78);
}
.gh-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}
.gh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 42px;
  padding: 0 22px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 13.5px;
  letter-spacing: 0.12em;
  cursor: pointer;
  text-decoration: none;
  transition: all .2s ease;
}
.gh-btn-gold {
  background: linear-gradient(135deg, #e0bd6c, #c9a227);
  color: #4f130e;
  border-color: rgba(255, 232, 184, 0.4);
}
.gh-btn-gold:hover { background: #f0d28c; transform: translateY(-1px); }
.gh-btn-ghost {
  border-color: rgba(243, 213, 151, 0.38);
  color: #f4dfb9;
}
.gh-btn-ghost:hover {
  background: rgba(255, 238, 205, 0.1);
  border-color: rgba(243, 213, 151, 0.7);
}
/* 右侧圆环艺术区 */
.gh-art {
  position: relative;
  z-index: 1;
  min-height: 200px;
  color: rgba(238, 205, 139, 0.62);
}
.gh-orbit {
  position: absolute;
  border: 1px solid rgba(238, 205, 139, 0.14);
  border-radius: 50%;
  pointer-events: none;
}
.gh-orbit-a { width: 280px; height: 280px; right: 38px; top: -18px; }
.gh-orbit-b { width: 214px; height: 214px; right: 70px; top: 16px; border-style: dashed; }
.gh-orbit-c { width: 340px; height: 340px; right: 8px; top: -48px; opacity: 0.55; }
.gh-seal {
  position: absolute;
  right: 70px;
  top: 24px;
  display: grid;
  place-items: center;
  width: 130px;
  height: 130px;
  border: 1px solid rgba(237, 205, 142, 0.52);
  border-radius: 50%;
  background: rgba(63, 15, 11, 0.18);
  box-shadow:
    inset 0 0 0 8px rgba(237, 205, 142, 0.06),
    0 0 0 1px rgba(237, 205, 142, 0.08);
  font-family: "KaiTi", "STKaiti", "Kaiti SC", "SimSun", serif;
  font-size: 64px;
  color: #f4d99f;
  text-shadow: 0 6px 24px rgba(38, 8, 4, 0.3);
}
.gh-seal::before,
.gh-seal::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(238, 205, 139, 0.2);
}
.gh-seal::before { inset: -18px; }
.gh-seal::after { inset: 18px; border-style: dashed; opacity: 0.6; }
.gh-vertical {
  position: absolute;
  right: 20px;
  top: 42px;
  writing-mode: vertical-rl;
  font-size: 9px;
  letter-spacing: 0.32em;
  color: rgba(246, 223, 184, 0.46);
}
/* 底部统计条 */
.gh-stats {
  position: absolute;
  left: 58px;
  right: 58px;
  bottom: 24px;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid rgba(236, 205, 143, 0.2);
  padding-top: 15px;
}
.gh-stat {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding-left: 20px;
  border-left: 1px solid rgba(236, 205, 143, 0.18);
}
.gh-stat:first-child { padding-left: 0; border-left: 0; }
.gh-stat b {
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif;
  font-size: 28px;
  font-weight: 400;
  line-height: 1;
  color: #f3d28d;
}
.gh-stat span {
  font-size: 10px;
  letter-spacing: 0.16em;
  color: rgba(255, 241, 217, 0.55);
}

@media (max-width: 900px) {
  .gh-banner {
    grid-template-columns: 1fr;
    padding: 36px 26px 90px;
  }
  .gh-art { min-height: 220px; opacity: .55; }
  .gh-stats { left: 26px; right: 26px; }
}
@media (max-width: 640px) {
  .page-hero-full { padding: 22px 20px 26px; }
  .ph-title { font-size: 22px; }
  .ph-seal { width: 52px; height: 52px; font-size: 24px; }
  .gh-banner { padding: 28px 20px 100px; }
  .gh-title { font-size: 64px; }
  .gh-stats { grid-template-columns: repeat(2, 1fr); row-gap: 14px; left: 20px; right: 20px; }
}
</style>
