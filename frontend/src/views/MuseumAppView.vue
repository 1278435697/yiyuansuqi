<script setup>
/**
 * 数字博物馆：原独立 three.js 展厅已收进主工程资源包（public/mus-app），
 * 由本组件承载，路由仍由主工程 /museum 提供，不再作为独立子站存在。
 */
import { onBeforeUnmount, onMounted } from 'vue';

const CSS_HREF = '/mus-app/assets/index-DGvvB6Qr.css';
const JS_BASE = '/mus-app/assets/index-CWinyng3v2.js';

let linkEl = null;
let scriptEl = null;

onMounted(() => {
  linkEl = document.createElement('link');
  linkEl.rel = 'stylesheet';
  linkEl.href = CSS_HREF;
  linkEl.dataset.museumApp = '1';
  document.head.appendChild(linkEl);

  scriptEl = document.createElement('script');
  scriptEl.type = 'module';
  scriptEl.src = `${JS_BASE}?t=${Date.now()}`;
  scriptEl.dataset.museumApp = '1';
  document.body.appendChild(scriptEl);
});

onBeforeUnmount(() => {
  if (scriptEl && scriptEl.parentNode) scriptEl.parentNode.removeChild(scriptEl);
  scriptEl = null;
  if (linkEl && linkEl.parentNode) linkEl.parentNode.removeChild(linkEl);
  linkEl = null;
});
</script>

<template>
  <div class="mus-shell">
    <div id="mus-app" class="mus-host" />
    <router-link class="m3d-entry" to="/museum3d">三维展厅 ↗</router-link>
  </div>
</template>

<style>
.mus-shell {
  position: relative;
  height: calc(100vh - 65px);
  overflow: hidden;
  background: #0c0b0e;
}

/* 通往三维展厅的入口（旧图录馆 → 新 3D 馆） */
.m3d-entry {
  position: absolute;
  right: 24px;
  bottom: 104px;
  z-index: 30;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 999px;
  border: 1px solid rgba(214, 178, 106, 0.5);
  background: rgba(16, 10, 8, 0.7);
  color: #f4d99f;
  font-size: 13px;
  letter-spacing: 0.1em;
  text-decoration: none;
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  transition: all 0.2s ease;
}

.m3d-entry:hover {
  background: linear-gradient(135deg, #e0bd6c, #c9a227);
  color: #4f130e;
  border-color: rgba(255, 232, 184, 0.6);
}

#mus-app {
  height: 100%;
}

#mus-app .app-shell {
  display: flex;
  flex-direction: column;
  height: 100% !important;
}

#mus-app .app-shell > main.stage {
  height: calc(100% - 56px) !important;
}

/* 展厅第二层顶栏沿用主站深朱红金字，与传承页双层结构一致 */
#mus-app .app-shell > header.topbar {
  background: rgba(110, 29, 24, 0.97) !important;
  border-bottom: 1px solid rgba(201, 162, 39, 0.5) !important;
  box-shadow: 0 2px 14px rgba(60, 20, 12, 0.25) !important;
}

#mus-app .app-shell > header.topbar .brand-text b {
  color: #ffe9a8 !important;
}

#mus-app .app-shell > header.topbar .brand-text i {
  color: rgba(255, 233, 168, 0.72) !important;
}

#mus-app .app-shell > header.topbar .nav a {
  color: #ffe9a8 !important;
}

#mus-app .app-shell > header.topbar .nav a.active {
  background: rgba(255, 233, 168, 0.22) !important;
  color: #fff9e8 !important;
  box-shadow: inset 0 -2px 0 #c9a227;
}

#mus-app .app-shell > header.topbar .seal {
  background: rgba(255, 233, 168, 0.14) !important;
  color: #ffe9a8 !important;
  border-color: rgba(201, 162, 39, 0.6) !important;
}

/* AI 识纹样（#/identify）：原子站是整片纯黑面板，与主站纸色氛围断裂，这里改回纸本浅色 */
#mus-app .identify {
  background:
    radial-gradient(circle at 50% 0%, rgba(169, 50, 42, 0.09), transparent 46%),
    radial-gradient(circle at 82% 16%, rgba(201, 162, 39, 0.12), transparent 42%),
    #f7f1e6 !important;
  box-shadow: inset 0 0 0 1px rgba(217, 203, 168, 0.6);
}

#mus-app .identify .eyebrow {
  color: #a93226 !important;
}

#mus-app .identify .hd h1 {
  color: #2b241d !important;
  font-family: "Noto Serif SC", "Source Han Serif SC", Songti SC, SimSun, serif;
}

#mus-app .identify .lede {
  color: #6a5c4a !important;
}

#mus-app .identify .drop {
  background: rgba(255, 253, 248, 0.92) !important;
  border-color: rgba(169, 50, 42, 0.28) !important;
  color: #8a7d6a !important;
}

#mus-app .identify .drop:hover,
#mus-app .identify .drop.over {
  border-color: #a93226 !important;
  background: #fffdf8 !important;
}

#mus-app .identify .drop.filled {
  border-color: rgba(201, 162, 39, 0.5) !important;
}

#mus-app .identify .drop p {
  color: #5b5044 !important;
}

#mus-app .identify .drop .hint {
  color: #8a7d6a !important;
}

#mus-app .identify .plus {
  color: #a93226 !important;
}

#mus-app .identify .btn.ghost {
  color: #5b5044 !important;
  background: #fffdf8 !important;
  border-color: #d9cba8 !important;
}

#mus-app .identify .btn.ghost:hover {
  color: #a93226 !important;
  border-color: #a93226 !important;
  background: rgba(169, 50, 42, 0.06) !important;
}

#mus-app .identify .btn.primary {
  color: #3a2a12 !important;
}

#mus-app .identify .err {
  color: #b3261e !important;
}

#mus-app .identify .col-right {
  background: #fffdf8 !important;
  border-color: #e3d8bf !important;
  box-shadow: 0 2px 14px rgba(120, 96, 60, 0.08) !important;
}

#mus-app .identify .state,
#mus-app .identify .state.idle {
  color: #7a6d5b !important;
}

#mus-app .identify .field {
  background: rgba(169, 50, 42, 0.05) !important;
  border-color: #e6dcc6 !important;
}

#mus-app .identify .field .k {
  color: #8a7d6a !important;
}

#mus-app .identify .field b {
  color: #2b241d !important;
}

#mus-app .identify .conf {
  color: #8a7d6a !important;
}

#mus-app .identify .bar {
  background: #e9dfc9 !important;
}

#mus-app .identify .conf em {
  color: #a93226 !important;
}

#mus-app .identify .note {
  color: #5b5044 !important;
}

#mus-app .identify .warn {
  color: #8a4a12 !important;
  background: rgba(201, 162, 39, 0.14) !important;
}

#mus-app .identify .sub {
  color: #a93226 !important;
}

#mus-app .identify .muted {
  color: #8a7d6a !important;
}

#mus-app .identify .cand {
  background: #fffdf8 !important;
  border-color: #e6dcc6 !important;
}

#mus-app .identify .cand .meta b {
  color: #2b241d !important;
}

#mus-app .identify .cand .meta i {
  color: #8a7d6a !important;
}
</style>
