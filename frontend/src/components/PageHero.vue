<template>
  <section class="page-hero-full">
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
</template>

<script setup lang="ts">
import RevealTitle from "./RevealTitle.vue";

withDefaults(defineProps<{
  title: string;
  kicker: string;
  sub: string;
  seal: string;
}>(), {});
</script>

<style scoped>
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
@media (max-width: 640px) {
  .page-hero-full { padding: 22px 20px 26px; }
  .ph-title { font-size: 22px; }
  .ph-seal { width: 52px; height: 52px; font-size: 24px; }
}
</style>
