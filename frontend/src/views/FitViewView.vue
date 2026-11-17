﻿<script setup lang="ts">
/**
 * 虚拟试穿 · AI 换装 + 3D 建模（新版）
 * 原独立交付的 React 应用（FitView：三视图换装 → 生成 GLB），已收进主工程资源包
 * public/fitview，构建产物部署为 dist/fitview，由本组件以 iframe 承载，路由 /fitview。
 * 用 iframe 而不是迁源码：该项目是 React + Vite 独立栈，自带三维渲染循环与键盘监听，
 * 整页隔离比混编进 Vue 更稳；接口走 /fitview-api/*，由 nginx 反代到 8787 端口的 node 代理。
 * 经典版（MediaPipe 版）仍保留在 /tryon，本页不叠浮动控件，避免压住应用内的主按钮。
 */
import { onBeforeUnmount, onMounted, ref } from "vue";

const shell = ref<HTMLElement | null>(null);
let ro: ResizeObserver | null = null;

/** 让应用刚好从主站顶栏下沿铺满，顶栏换行（窄屏两行）时也不会被压住 */
function applyTop() {
  if (!shell.value) return;
  const header = document.querySelector(".app-header") as HTMLElement | null;
  const top = header ? Math.round(header.getBoundingClientRect().height) : 65;
  shell.value.style.top = `${top}px`;
}

onMounted(() => {
  applyTop();
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
  window.removeEventListener("resize", applyTop);
});
</script>

<template>
  <div ref="shell" class="fv-shell">
    <iframe class="fv-frame" src="/fitview/index.html" title="虚拟试穿 · 换装与三维建模" allow="fullscreen" />
  </div>
</template>

<style scoped>
.fv-shell {
  /* 铺满顶栏以下的可视区，避免被主内容区的内边距挤出白边 */
  position: fixed;
  top: 65px;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  background: #0f0c0a;
  z-index: 1;
}

.fv-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}
</style>
