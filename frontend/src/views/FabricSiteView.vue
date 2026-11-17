<template>
  <div class="fab-page" ref="wrap"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import pageHtml from "@/sites/fabric/content.html?raw";
import cssUrl from "@/sites/fabric/page.css?url";
import scriptUrl from "@/sites/fabric/script.js?url";

const wrap = ref<HTMLElement | null>(null);
let linkEl: HTMLLinkElement | null = null;

function loadCss(href: string): Promise<void> {
  return new Promise((resolve) => {
    const l = document.createElement("link");
    l.rel = "stylesheet";
    l.href = href;
    l.onload = () => resolve();
    l.onerror = () => resolve(); // 样式失败也继续渲染内容
    linkEl = l;
    document.head.appendChild(l);
  });
}

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
  if (!wrap.value) return;
  await loadCss(cssUrl); // 493KB 样式单独加载，避免拖大主 chunk
  wrap.value.innerHTML = pageHtml;
  try {
    await loadScript(scriptUrl);
  } catch (e) {
    console.error("[面料] 脚本加载失败", e);
  }
});

onBeforeUnmount(() => {
  try {
    (window as any).__fabTeardown?.();
  } catch (e) {
    /* 忽略 */
  }
  linkEl?.remove();
  linkEl = null;
});
</script>
