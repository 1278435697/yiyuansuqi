<template>
  <div class="acc-page-shell">
    <div class="paper-bg" aria-hidden="true"></div>
    <main id="accRoot" ref="root" class="acc-root"></main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import pageHtml from "@/sites/accessories/content.html?raw";
import pageCss from "@/sites/accessories/page.css?raw";
import dataUrl from "@/sites/accessories/data.js?url";
import appUrl from "@/sites/accessories/app.js?url";

const root = ref<HTMLElement | null>(null);
let styleEl: HTMLStyleElement | null = null;

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.async = false;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("加载失败 " + src));
    document.head.appendChild(s);
  });
}

onMounted(async () => {
  if (!root.value) return;
  // 正文一次性写入（内容是静态 HTML，交给原脚本渲染列表与详情）
  root.value.innerHTML = pageHtml;

  styleEl = document.createElement("style");
  styleEl.id = "acc-page-style";
  styleEl.textContent = pageCss;
  document.head.appendChild(styleEl);

  try {
    await loadScript(dataUrl);
    await loadScript(appUrl);
  } catch (e) {
    console.error("[衣冠] 脚本加载失败", e);
  }
});

onBeforeUnmount(() => {
  try {
    (window as any).__accAiGuideTeardown?.();
  } catch (e) {
    /* 忽略 */
  }
  try {
    (window as any).__accTeardown?.();
  } catch (e) {
    /* 忽略 */
  }
  styleEl?.remove();
  styleEl = null;
  try {
    delete (window as any).ACCESSORIES;
  } catch (e) {
    /* 忽略 */
  }
});
</script>

<style scoped>
.acc-page-shell {
  position: relative;
}
.acc-root {
  position: relative;
  z-index: 1;
}
</style>
