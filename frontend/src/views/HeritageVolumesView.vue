<template>
  <div class="her-page" ref="root"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import pageHtml from "@/sites/heritage/content.html?raw";
import pageCss from "@/sites/heritage/page.css?raw";
import dataUrl from "@/sites/heritage/data.js?url";
import sectionsUrl from "@/sites/heritage/sections.js?url";
import figsUrl from "@/sites/heritage/figs.js?url";
import scriptUrl from "@/sites/heritage/script.js?url";

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
  root.value.innerHTML = pageHtml;

  styleEl = document.createElement("style");
  styleEl.id = "her-page-style";
  styleEl.textContent = pageCss;
  document.head.appendChild(styleEl);

  try {
    // 顺序固定：三份数据 → 渲染脚本
    await loadScript(dataUrl);
    await loadScript(sectionsUrl);
    await loadScript(figsUrl);
    await loadScript(scriptUrl);
  } catch (e) {
    console.error("[传承] 脚本加载失败", e);
  }
});

onBeforeUnmount(() => {
  try {
    (window as any).__herTeardown?.();
  } catch (e) {
    /* 忽略 */
  }
  styleEl?.remove();
  styleEl = null;
});
</script>
