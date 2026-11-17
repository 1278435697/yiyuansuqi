<script setup lang="ts">
/**
 * 数字馆 · 华夏服饰数字馆（第一人称漫游版）
 * 原独立交付的 React + three.js 馆舍（museum.html，WASD 行走 / 点展品看档案），
 * 已收进主工程 public/mus3d（assets + pic 素材 + audio 讲解，路径前缀 /mus3d/），
 * 构建后部署为 dist/mus3d，由本组件以 iframe 承载，路由 /museum。
 * 用 iframe 而不迁源码：它自带 three.js 渲染循环与键盘/指针锁定监听，整页隔离比混编稳定。
 *
 * 语音导游：交付包本身只有文字问答（不发声），这里补一层厅级录音讲解。
 * 三段讲解词按馆内真实布陈撰写，离线生成 mp3 放在 public/mus3d/audio，
 * 由本组件的 <audio> 播放；切厅时（iframe 的 hall 参数变化）自动换到对应音轨。
 * 旧的三维子站（MuseumAppView）保留在 /museum-app。
 */
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

/** 馆内返回：优先回上一页，没有历史就回首页（按钮必须画在 iframe 之上，故由本组件出，不用全局 fixed） */
function goBack() {
  if (window.history.length > 1) router.back();
  else router.push("/");
}

const shell = ref<HTMLElement | null>(null);
const frame = ref<HTMLIFrameElement | null>(null);
const audio = ref<HTMLAudioElement | null>(null);
let ro: ResizeObserver | null = null;
let timer: number | null = null;

/** AI 识纹样：页面原本只在旧图录馆（/museum-app#/identify）里，这里以覆盖层挂回新馆 */
const identifyOpen = ref(false);
const identifyFrame = ref<HTMLIFrameElement | null>(null);
const IDENT_PATCH_ID = "mh-ident-patch";

/** 覆盖层里是整站页面，去掉它自带的主站顶栏与旧馆入口，只留识纹样本体 */
function patchIdentifyFrame() {
  try {
    const doc = identifyFrame.value?.contentDocument;
    if (!doc || !doc.head || doc.getElementById(IDENT_PATCH_ID)) return;
    const style = doc.createElement("style");
    style.id = IDENT_PATCH_ID;
    style.textContent =
      ".app-header{display:none!important}.m3d-entry{display:none!important}.mus-shell{height:100vh!important}";
    doc.head.appendChild(style);
  } catch (e) {
    /* 跨域或未就绪时忽略 */
  }
}

function openIdentify() {
  identifyOpen.value = true;
  window.setTimeout(patchIdentifyFrame, 900);
}
function closeIdentify() {
  identifyOpen.value = false;
}

/** 让馆舍刚好从主站顶栏下沿铺满，顶栏换行（窄屏两行）时也不会被压住 */
function applyTop() {
  if (!shell.value) return;
  const header = document.querySelector(".app-header") as HTMLElement | null;
  const top = header ? Math.round(header.getBoundingClientRect().height) : 65;
  shell.value.style.top = `${top}px`;
}

/* ---------------- 语音导游 ---------------- */
type HallId = "costume" | "fabric" | "pattern";
const AUDIO_SRC: Record<HallId, string> = {
  costume: "/mus3d/audio/hall-costume.mp3",
  fabric: "/mus3d/audio/hall-fabric.mp3",
  pattern: "/mus3d/audio/hall-pattern.mp3",
};
const HALL_NAME: Record<HallId, string> = { costume: "服饰厅", fabric: "面料厅", pattern: "纹样厅" };

const hall = ref<HallId>("costume");
const playing = ref(false);
const failed = ref(false);

/* ---- 字幕与播放控制：字幕时间轴由讲解音轨转写得到（/mus3d/audio/hall-*.json） ---- */
type Cue = { s: number; e: number; t: string };
const cues = ref<Cue[]>([]);
const total = ref(0);
const cur = ref(0);
let ticker: number | null = null;

const pct = computed(() =>
  total.value > 0 ? Math.max(0, Math.min(100, (cur.value / total.value) * 100)) : 0,
);

/** 当前时间落在第几句（-1 表示还没到第一句） */
const cueIdx = computed(() => {
  let i = -1;
  for (let k = 0; k < cues.value.length; k += 1) if (cues.value[k].s <= cur.value + 0.02) i = k;
  return i;
});
const cueText = computed(() => cues.value[cueIdx.value]?.t || "");

function fmt(sec: number) {
  const s = Math.max(0, Math.floor(sec || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

async function loadSubs(h: HallId) {
  cues.value = [];
  cur.value = 0;
  total.value = 0;
  try {
    const r = await fetch(`/mus3d/audio/hall-${h}.json`);
    if (!r.ok) return;
    const j = (await r.json()) as { duration?: number; cues?: Cue[] };
    cues.value = Array.isArray(j.cues) ? j.cues : [];
    total.value = Number(j.duration || 0);
  } catch (e) {
    /* 字幕缺失时退化为纯播放 */
  }
}

function seekTo(sec: number) {
  const a = audio.value;
  if (!a) return;
  const max = a.duration && !Number.isNaN(a.duration) ? a.duration : total.value || 0;
  const t = Math.max(0, Math.min(sec, max || sec));
  a.currentTime = t;
  cur.value = t;
}

function seekClick(ev: MouseEvent) {
  const el = ev.currentTarget as HTMLElement | null;
  if (!el) return;
  const r = el.getBoundingClientRect();
  const max = audio.value?.duration || total.value || 0;
  if (!max) return;
  seekTo(((ev.clientX - r.left) / Math.max(1, r.width)) * max);
}

/** 上一句 / 下一句：直接跳到该句起点 */
function stepCue(delta: number) {
  if (!cues.value.length) {
    seekTo(cur.value + delta * 5);
    return;
  }
  const i = cueIdx.value + delta;
  if (i < 0) {
    seekTo(0);
    return;
  }
  const c = cues.value[Math.min(i, cues.value.length - 1)];
  seekTo(c.s + 0.02);
  if (!playing.value) startNarration();
}

function onTime() {
  const a = audio.value;
  if (a) cur.value = a.currentTime;
}

function onMeta() {
  const a = audio.value;
  if (a && a.duration && !Number.isNaN(a.duration)) total.value = a.duration;
}

/** 读 iframe 的 hall 参数（同源可直接读 location）；没参数时默认服饰厅 */
function readHall(): HallId {
  try {
    const search = frame.value?.contentWindow?.location?.search || "";
    const m = /hall=(costume|fabric|pattern)/.exec(search);
    if (m) return m[1] as HallId;
  } catch (e) {
    /* 跨域或未就绪时忽略 */
  }
  return "costume";
}

function startNarration() {
  const a = audio.value;
  if (!a) return;
  failed.value = false;
  const src = AUDIO_SRC[hall.value];
  if (!a.src.endsWith(src)) {
    a.src = src;
    a.currentTime = 0;
    cur.value = 0;
  }
  a.play().then(
    () => (playing.value = true),
    () => (playing.value = false), // 浏览器拦截自动播放时保持待机，等用户再点
  );
}

function stopNarration() {
  audio.value?.pause();
  playing.value = false;
}

/** 播放/暂停：同一条音轨中断后继续，播完或换厅才从头起 */
function toggleNarration() {
  const a = audio.value;
  if (!a) return;
  if (playing.value) {
    stopNarration();
    return;
  }
  const sameTrack = a.src.endsWith(AUDIO_SRC[hall.value]);
  if (!sameTrack || a.ended) {
    a.src = AUDIO_SRC[hall.value];
    a.currentTime = 0;
    cur.value = 0;
  }
  startNarration();
}

/** 每 800ms 比对一次当前展厅，切厅后自动切到该厅音轨（正在播时无缝续播） */
function pollHall() {
  const now = readHall();
  if (now !== hall.value) {
    hall.value = now;
    loadSubs(now);
    if (playing.value) startNarration();
  }
}

/**
 * 馆内底部左侧有一排操作提示（拖拽环视 / WASD 行走 / Shift 加速 …），
 * 会与本组件的语音导游胶囊压在同一角落，这里往 iframe 里补一条样式把它右让。
 * 窄屏（≤860px）馆内自己的 hint 是隐藏的，不需要让位。
 */
const HUD_PATCH_ID = "mh-hud-patch";
const AI_GUIDE_ID = "mh-ai-guide";

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
      "@media (min-width:861px){.hud-bottom{left:400px !important;}.timeline{bottom:96px;}}";
    doc.head.appendChild(style);
  } catch (e) {
    /* 跨域或未就绪时忽略 */
  }
}

onMounted(() => {
  applyTop();
  patchHud();
  injectAiGuide();
  loadSubs(hall.value);
  ticker = window.setInterval(onTime, 120);
  frame.value?.addEventListener("load", patchHud);
  frame.value?.addEventListener("load", injectAiGuide);
  const header = document.querySelector(".app-header") as HTMLElement | null;
  if (header && typeof ResizeObserver !== "undefined") {
    ro = new ResizeObserver(applyTop);
    ro.observe(header);
  }
  window.addEventListener("resize", applyTop);
  timer = window.setInterval(() => {
    pollHall();
    patchHud();
    injectAiGuide();
    if (identifyOpen.value) patchIdentifyFrame();
  }, 800);
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
  timer = null;
  if (ticker) window.clearInterval(ticker);
  ticker = null;
  frame.value?.removeEventListener("load", patchHud);
  frame.value?.removeEventListener("load", injectAiGuide);
  stopNarration();
  ro?.disconnect();
  ro = null;
  window.removeEventListener("resize", applyTop);
});
</script>

<template>
  <div ref="shell" class="mh-shell">
    <iframe
      ref="frame"
      class="mh-frame"
      src="/mus3d/museum.html"
      title="数字馆 · 华夏服饰漫游"
      allow="fullscreen"
    />

    <!-- 返回：压在左下语音讲解卡正上方（馆内舞台是 WebGL 画布，全局浮动按钮会被画布盖住） -->
    <button class="mh-back" type="button" title="返回上一页" @click="goBack">
      <span class="mh-back-ico" aria-hidden="true">←</span>
      <span>返回</span>
    </button>

    <!-- 语音导游：厅级录音讲解 + 同步字幕 + 播放/暂停/拖动/切句 -->
    <div class="mh-voice" :class="{ 'is-on': playing, 'is-failed': failed }">
      <div class="mh-voice-row">
        <button class="mh-voice-play" type="button" :aria-pressed="playing" @click="toggleNarration">
          <span class="mh-voice-ico" aria-hidden="true">{{ playing ? "❚❚" : "▶" }}</span>
        </button>
        <span class="mh-voice-title">语音导游 · {{ HALL_NAME[hall] }}</span>
        <span class="mh-voice-time">{{ fmt(cur) }} / {{ fmt(total || 0) }}</span>
      </div>

      <div
        class="mh-voice-bar"
        role="slider"
        tabindex="0"
        aria-label="讲解播放进度"
        :aria-valuenow="Math.round(pct)"
        @click="seekClick"
      >
        <i :style="{ width: pct + '%' }"></i>
        <b :style="{ left: pct + '%' }"></b>
      </div>

      <div class="mh-voice-sub">
        <button class="mh-voice-step" type="button" title="上一句" @click="stepCue(-1)">◀</button>
        <span class="mh-voice-subtext">{{ cueText || "点播放，讲解字幕会跟着念" }}</span>
        <button class="mh-voice-step" type="button" title="下一句" @click="stepCue(1)">▶</button>
      </div>
    </div>

    <audio
      ref="audio"
      preload="none"
      @timeupdate="onTime"
      @loadedmetadata="onMeta"
      @ended="(playing = false), onTime()"
      @error="(playing = false), (failed = true)"
    />

    <!-- AI 识纹样入口：原功能在旧图录馆里，这里挂回漫游馆右侧 -->
    <button class="mh-ident" type="button" title="拍照识纹样 · 读出朝代、形制、纹样与材质" @click="openIdentify">
      <span class="mh-ident-ico" aria-hidden="true">◈</span>
      <span>AI 识纹样</span>
    </button>

    <div v-if="identifyOpen" class="mh-mask" @click.self="closeIdentify">
      <div class="mh-panel">
        <div class="mh-panel-bar">
          <b>AI 识纹样 · 拍照识别</b>
          <div class="mh-panel-ops">
            <a href="/museum-app#/identify" target="_blank" rel="noopener">新窗口打开 ↗</a>
            <button type="button" @click="closeIdentify">关闭 ✕</button>
          </div>
        </div>
        <iframe ref="identifyFrame" class="mh-panel-frame" src="/museum-app#/identify" title="AI 识纹样" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.mh-shell {
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

.mh-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}

/* 返回：讲解卡上方 12px，同层绘制保证盖在 WebGL 画布之上 */
.mh-back {
  position: absolute;
  left: 20px;
  bottom: 128px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 15px;
  border-radius: 999px;
  border: 1px solid rgba(243, 213, 151, 0.62);
  background: rgba(122, 34, 28, 0.9);
  color: #f6e7bf;
  font-family: inherit;
  font-size: 13.5px;
  letter-spacing: 0.08em;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}
.mh-back:hover {
  background: rgba(150, 42, 32, 0.96);
  border-color: rgba(243, 213, 151, 0.95);
  transform: translateY(-1px);
}
.mh-back-ico {
  font-size: 15px;
  line-height: 1;
}

/* 讲解卡片：压在左下（馆内右下是导览面板、顶部是厅切换，都不挡） */
.mh-voice {
  position: absolute;
  left: 20px;
  bottom: 20px;
  z-index: 20;
  width: 352px;
  padding: 11px 14px 12px;
  border-radius: 14px;
  border: 1px solid rgba(201, 168, 106, 0.38);
  background: rgba(16, 10, 8, 0.74);
  color: rgba(240, 226, 198, 0.9);
  font-family: "Songti SC", "Noto Serif SC", "SimSun", serif;
  font-size: 12.5px;
  letter-spacing: 0.04em;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.mh-voice.is-on {
  border-color: rgba(243, 213, 151, 0.82);
  background: rgba(32, 20, 12, 0.86);
}

.mh-voice.is-failed {
  opacity: 0.6;
}

.mh-voice-row {
  display: flex;
  align-items: center;
  gap: 9px;
}

.mh-voice-play {
  width: 26px;
  height: 26px;
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid rgba(201, 168, 106, 0.5);
  background: rgba(201, 168, 106, 0.12);
  color: #f4d99f;
  font-size: 10px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.mh-voice-play:hover {
  background: rgba(201, 168, 106, 0.26);
  border-color: rgba(243, 213, 151, 0.85);
}

.mh-voice-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.mh-voice-time {
  flex: none;
  font-size: 11px;
  letter-spacing: 0.02em;
  color: rgba(201, 168, 106, 0.92);
  font-variant-numeric: tabular-nums;
}

/* 进度条：整条可点，点哪跳哪 */
.mh-voice-bar {
  position: relative;
  height: 14px;
  margin: 7px 0 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.mh-voice-bar:before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 2px;
  background: rgba(201, 168, 106, 0.22);
}

.mh-voice-bar i {
  position: absolute;
  left: 0;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(201, 168, 106, 0.7), #f0c96a);
  pointer-events: none;
}

.mh-voice-bar b {
  position: absolute;
  width: 9px;
  height: 9px;
  margin-left: -4.5px;
  border-radius: 50%;
  background: #f4d99f;
  box-shadow: 0 0 6px rgba(240, 201, 106, 0.55);
  pointer-events: none;
  transform: translateY(0);
}

.mh-voice-sub {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mh-voice-step {
  flex: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid rgba(201, 168, 106, 0.35);
  background: transparent;
  color: rgba(201, 168, 106, 0.9);
  font-size: 9px;
  line-height: 1;
  cursor: pointer;
}

.mh-voice-step:hover {
  color: #f4d99f;
  border-color: rgba(243, 213, 151, 0.7);
}

.mh-voice-subtext {
  flex: 1;
  min-width: 0;
  font-size: 12.5px;
  line-height: 1.5;
  color: rgba(244, 226, 190, 0.86);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes mhPulse {
  0% { box-shadow: 0 0 0 0 rgba(240, 201, 106, 0.55); }
  100% { box-shadow: 0 0 0 10px rgba(240, 201, 106, 0); }
}

/* AI 识纹样：右侧竖排入口 + 覆盖层面板 */
.mh-ident {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 4;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 16px;
  border-radius: 999px;
  border: 1px solid rgba(243, 213, 151, 0.62);
  background: rgba(122, 34, 28, 0.88);
  color: #f6e7bf;
  font-family: inherit;
  font-size: 13.5px;
  letter-spacing: 0.08em;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}
.mh-ident:hover {
  background: rgba(150, 42, 32, 0.96);
  border-color: rgba(243, 213, 151, 0.95);
  transform: translateY(-50%) translateX(-2px);
}
.mh-ident-ico { font-size: 15px; line-height: 1; color: #f0c96a; }

.mh-mask {
  position: absolute;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 26px;
  background: rgba(12, 7, 5, 0.72);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
.mh-panel {
  width: min(1080px, 96vw);
  height: min(760px, 92vh);
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(201, 168, 106, 0.5);
  background: #f7f1e6;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
}
.mh-panel-bar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: linear-gradient(140deg, #7a221c, #a93226);
  color: #f6e7bf;
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 13.5px;
  letter-spacing: 0.08em;
}
.mh-panel-ops { display: flex; align-items: center; gap: 10px; }
.mh-panel-ops a {
  color: rgba(250, 235, 205, 0.9);
  text-decoration: none;
  font-size: 12.5px;
  border-bottom: 1px dashed rgba(250, 235, 205, 0.5);
}
.mh-panel-ops a:hover { color: #fff8e7; }
.mh-panel-ops button {
  cursor: pointer;
  font-family: inherit;
  font-size: 12.5px;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid rgba(243, 213, 151, 0.55);
  background: rgba(255, 255, 255, 0.1);
  color: #f6e7bf;
}
.mh-panel-ops button:hover { background: rgba(255, 255, 255, 0.2); }
.mh-panel-frame { flex: 1; width: 100%; border: 0; background: #f7f1e6; }

@media (max-width: 640px) {
  .mh-back {
    left: 12px;
    bottom: 138px;
    padding: 7px 13px;
    font-size: 13px;
  }
  .mh-voice {
    left: 12px;
    bottom: 12px;
    width: calc(100vw - 24px);
    max-width: 352px;
    padding: 10px 12px 11px;
  }
  .mh-voice-subtext {
    font-size: 12px;
    -webkit-line-clamp: 1;
  }
}
</style>
