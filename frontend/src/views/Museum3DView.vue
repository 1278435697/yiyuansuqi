<script setup lang="ts">
/**
 * 三维数字馆：原独立交付的 Three.js 第一人称展厅（衣冠志 · 华夏服饰数字馆），
 * 已收进主工程资源包 public/mus3d，由本组件以 iframe 承载，路由 /museum3d。
 * 用 iframe 而不是直接注入脚本：展厅自带 rAF 循环与全局键盘监听，离开路由时整页销毁更干净。
 * 展厅自身已有三个厅的切换栏，本组件只补一个返回图录的入口，不叠加控件。
 */
import { onBeforeUnmount, onMounted, ref } from "vue";

const shell = ref<HTMLElement | null>(null);
let ro: ResizeObserver | null = null;

/** 让展厅刚好从主站顶栏下沿铺满，顶栏换行（窄屏两行）时也不会被压住 */
function applyTop() {
  if (!shell.value) return;
  const header = document.querySelector(".app-header") as HTMLElement | null;
  const top = header ? Math.round(header.getBoundingClientRect().height) : 65;
  shell.value.style.top = `${top}px`;
}

/**
 * 馆内底部左侧有一排操作提示，会和本组件左下「返回图录」压在同一角落，
 * 往 iframe 里补一条样式把提示条右让；窄屏下馆内自己就隐藏了提示，无需处理。
 */
const HUD_PATCH_ID = "m3d-hud-patch";
const AI_GUIDE_ID = "m3d-ai-guide";
const frame = ref<HTMLIFrameElement | null>(null);

/** 馆内「问导览」原本只把展品档案拼成固定答案，引一份脚本把它接成真大模型 */
function injectAiGuide() {
  try {
    const doc = frame.value?.contentDocument;
    if (!doc || !doc.body || doc.getElementById(AI_GUIDE_ID)) return;
    const s = doc.createElement("script");
    s.id = AI_GUIDE_ID;
    s.src = "/mus3d/ai-guide.js?v=" + Date.now();
    s.async = true;
    doc.body.appendChild(s);
  } catch (e) {
    /* 跨域或未就绪时忽略 */
  }
}

function patchHud() {
  try {
    const doc = frame.value?.contentDocument;
    if (!doc || !doc.head || doc.getElementById(HUD_PATCH_ID)) return;
    const style = doc.createElement("style");
    style.id = HUD_PATCH_ID;
    style.textContent =
      "@media (min-width:861px){.hud-bottom{left:212px !important;}.timeline{bottom:92px;}}";
    doc.head.appendChild(style);
  } catch (e) {
    /* 跨域或未就绪时忽略 */
  }
}

onMounted(() => {
  applyTop();
  patchHud();
  injectAiGuide();
  frame.value?.addEventListener("load", patchHud);
  frame.value?.addEventListener("load", injectAiGuide);
  const header = document.querySelector(".app-header") as HTMLElement | null;
  if (header && typeof ResizeObserver !== "undefined") {
    ro = new ResizeObserver(applyTop);
    ro.observe(header);
  }
  window.addEventListener("resize", applyTop);
});

onBeforeUnmount(() => {
  ro?.disconnect();
  ro = null;
  frame.value?.removeEventListener("load", patchHud);
  frame.value?.removeEventListener("load", injectAiGuide);
  window.removeEventListener("resize", applyTop);
});
</script>

<template>
  <div ref="shell" class="m3d-shell">
    <iframe ref="frame" class="m3d-frame" src="/mus3d/museum.html?hall=costume" title="衣冠志 · 华夏服饰数字馆" allow="fullscreen" />
    <router-link class="m3d-back" to="/museum">← 返回图录</router-link>
  </div>
</template>

<style scoped>
.m3d-shell {
  /* 铺满顶栏以下的可视区，避免被主内容区的内边距挤出白边 */
  position: fixed;
  top: 65px;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  background: #080605;
  z-index: 1;
}

.m3d-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}

.m3d-back {
  position: absolute;
  left: 22px;
  bottom: 22px;
  z-index: 20;
  display: inline-flex;
  align-items: center;
  padding: 9px 16px;
  border-radius: 999px;
  border: 1px solid rgba(214, 178, 106, 0.4);
  background: rgba(16, 10, 8, 0.66);
  color: rgba(242, 225, 190, 0.82);
  font-size: 12.5px;
  letter-spacing: 0.08em;
  text-decoration: none;
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
}

.m3d-back:hover {
  color: #f4d99f;
  background: rgba(243, 213, 151, 0.14);
  border-color: rgba(243, 213, 151, 0.7);
}
</style>
