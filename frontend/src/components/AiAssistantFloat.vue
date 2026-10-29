<template>
  <!-- 全局悬浮 AI 助手：可拖动的印章球 + 跟随球开合的对话面板 -->
  <div class="ai-float" :class="{ 'is-snapping': snapping }" :style="floatStyle">
    <!-- 对话面板 -->
    <transition name="af-pop">
      <div v-if="open" class="af-panel" :class="panelClass" :style="panelStyle"
           role="dialog" aria-label="衣溯 · 华夏衣冠志 助手">
        <div class="af-head">
          <span class="af-head-seal">问</span>
          <div class="af-head-text">
            <b>衣溯 · 华夏衣冠志</b>
            <i>溯源 · 复原 · 传承</i>
          </div>
          <button class="af-close" title="收起" aria-label="收起助手面板" @click="open = false">×</button>
        </div>

        <!-- 消息区（无对话时先给引导 + 快捷问题，同一块滚动区，不留空白带） -->
        <div ref="listEl" class="af-msgs">
          <div v-if="!msgs.length" class="af-welcome">
            <p class="af-hello">你好，我是<b>衣溯</b>。服饰形制、纹样源流、出土实证，都可以问我。</p>
            <p class="af-quick-tip">可以从这里开始问，或直接<b>粘贴截图</b>让我看图识服饰：</p>
            <div class="af-chips">
              <button v-for="q in quickQs" :key="q" class="af-chip" @click="ask(q)">{{ q }}</button>
            </div>
          </div>

          <div v-for="(m, i) in msgs" :key="i" class="af-row" :class="m.role">
            <div class="af-bubble">
              <img v-if="m.image" class="af-thumb" :src="m.image" alt="截图" />
              <p>{{ m.content }}</p>
              <span v-if="m.imageNote" class="af-img-note">图：{{ m.imageNote }}</span>
              <span v-if="m.ref" class="af-ref">引用：{{ m.ref }}</span>
              <button v-if="m.failed" class="af-retry" @click="retry(i)">重试</button>
            </div>
          </div>
          <div v-if="loading" class="af-row assistant">
            <div class="af-bubble af-typing"><span></span><span></span><span></span></div>
          </div>
          <div v-if="note" class="af-note">{{ note }}</div>
        </div>

        <!-- 待发图片预览 -->
        <div v-if="pendingImage" class="af-pending">
          <img :src="pendingImage" alt="待发截图" />
          <button class="af-pending-clear" @click="pendingImage = ''" title="移除">×</button>
        </div>

        <!-- 输入区 -->
        <div class="af-input">
          <button class="af-attach" title="上传截图/照片" :disabled="loading" @click="pickImage">📎</button>
          <button class="af-attach" title="截取当前网页" :disabled="loading || shotting" @click="takeScreenshot">{{ shotting ? '⏳' : '📷' }}</button>
          <input ref="fileInput" type="file" accept="image/*" hidden @change="onPick" />
          <el-input ref="inputEl" v-model="input" placeholder="问我任何服饰溯源问题，可粘贴截图…" clearable
                    @keyup.enter="send" :disabled="loading" />
          <button class="af-send" :disabled="loading" @click="send">发送</button>
        </div>
      </div>
    </transition>

    <!-- 悬浮球：按住可拖，单击开合 -->
    <button ref="ballEl" class="af-ball" :class="{ active: open, dragging, 'tip-right': onLeft }"
            title="衣溯 · 华夏衣冠志 助手（可拖动）" :aria-expanded="open ? 'true' : 'false'"
            aria-label="衣溯助手，可拖动，回车展开对话"
            @pointerdown="onPointerDown" @click="onBallClick">
      <span class="af-ball-seal">问</span>
      <span class="af-ball-tip">衣溯 · 华夏衣冠志 助手</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import { fetchAiChat } from "@/api/modules";

const open = ref(false);
const input = ref("");
const loading = ref(false);
const note = ref("");
const listEl = ref<HTMLElement | null>(null);

/* ===== 拖动 ===== */
const BALL = 58; // 悬浮球直径，与 CSS 保持一致
const EDGE = 12; // 拖动时允许贴到视口边的最小间距
const GAP = 12; // 面板与球之间的留白

function viewport() {
  return {
    w: document.documentElement.clientWidth,
    h: document.documentElement.clientHeight,
  };
}

// 吸边内缩：窄屏贴得近些，和原来 14px 的观感一致
function inset() {
  return viewport().w < 480 ? 14 : 24;
}

function clampPos(p: { x: number; y: number }) {
  const { w, h } = viewport();
  return {
    x: Math.max(EDGE, Math.min(w - BALL - EDGE, p.x)),
    y: Math.max(EDGE, Math.min(h - BALL - EDGE, p.y)),
  };
}

function defaultPos() {
  const { w, h } = viewport();
  return { x: w - BALL - inset(), y: h - BALL - inset() };
}

const pos = ref(defaultPos());
const dragging = ref(false);
const snapping = ref(false);
// 用户是否拖过：没拖过就一直贴右下角（和原来的 CSS 表现一致），拖过才记住坐标
const dragged = ref(false);
const onLeft = computed(() => pos.value.x + BALL / 2 < viewport().w / 2);

const floatStyle = computed(() => ({ left: `${pos.value.x}px`, top: `${pos.value.y}px` }));

// 面板几何：高度固定（不随内容跳变），开在空间更大的一侧
const panelGeom = computed(() => {
  const { w, h } = viewport();
  const pw = Math.min(380, w - inset() * 2);
  const spaceAbove = pos.value.y - GAP;
  const spaceBelow = h - (pos.value.y + BALL) - GAP;
  const ceiling = w < 480 ? Math.round(h * 0.62) : 520;
  const up = spaceAbove >= ceiling || spaceAbove >= spaceBelow;
  const fit = up ? spaceAbove : spaceBelow;
  return { pw, up, left: onLeft.value ? 0 : BALL - pw, ph: Math.max(200, Math.min(ceiling, fit)) };
});

const panelStyle = computed(() => {
  const { pw, up, left, ph } = panelGeom.value;
  const vertical = up ? { bottom: `${BALL + GAP}px`, top: "auto" } : { top: `${BALL + GAP}px`, bottom: "auto" };
  return { width: `${pw}px`, height: `${ph}px`, left: `${left}px`, ...vertical };
});

const panelClass = computed(() => ({ "is-down": !panelGeom.value.up, "is-side-left": onLeft.value }));

let downX = 0;
let downY = 0;
let originX = 0;
let originY = 0;
let moved = false;
let suppressClick = false;
let snapTimer = 0;
let suppressTimer = 0;

function onPointerMove(e: PointerEvent) {
  const dx = e.clientX - downX;
  const dy = e.clientY - downY;
  if (!moved && Math.hypot(dx, dy) <= 4) return;
  moved = true;
  dragged.value = true;
  dragging.value = true;
  snapping.value = false;
  pos.value = clampPos({ x: originX + dx, y: originY + dy });
}

function onPointerUp() {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("pointercancel", onPointerUp);
  dragging.value = false;
  if (!moved) return;
  suppressClick = true;
  // 万一这次没有派发 click（部分触摸路径），别把抑制状态留给下一次点击
  window.clearTimeout(suppressTimer);
  suppressTimer = window.setTimeout(() => (suppressClick = false), 350);
  snapToEdge();
}

// 松手后横向吸到最近的左/右边缘，纵向留在你放的高度
function snapToEdge() {
  const { w } = viewport();
  const m = inset();
  const targetX = pos.value.x + BALL / 2 < w / 2 ? m : w - BALL - m;
  snapping.value = true;
  pos.value = clampPos({ x: targetX, y: pos.value.y });
  window.clearTimeout(snapTimer);
  snapTimer = window.setTimeout(() => (snapping.value = false), 220);
}

function onPointerDown(e: PointerEvent) {
  if (e.button !== 0) return;
  downX = e.clientX;
  downY = e.clientY;
  originX = pos.value.x;
  originY = pos.value.y;
  moved = false;
  const el = e.currentTarget as HTMLElement;
  el.setPointerCapture?.(e.pointerId);
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", onPointerUp);
}

function onBallClick() {
  if (suppressClick) {
    suppressClick = false;
    return;
  }
  open.value = !open.value;
}

// 视口变了就重新贴一次：没拖过 → 回真·右下角；拖过 → 只保证不出屏
// 用 ResizeObserver 而不是只听 window resize：内容加载完才出现的滚动条不会触发 resize
function syncLayout() {
  pos.value = dragged.value ? clampPos(pos.value) : clampPos(defaultPos());
}

let ro: ResizeObserver | null = null;

onMounted(() => {
  syncLayout();
  window.addEventListener("resize", syncLayout);
  window.addEventListener("paste", onPaste);
  if (typeof ResizeObserver !== "undefined") {
    ro = new ResizeObserver(syncLayout);
    ro.observe(document.documentElement);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", syncLayout);
  window.removeEventListener("paste", onPaste);
  ro?.disconnect();
  ro = null;
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("pointercancel", onPointerUp);
  window.clearTimeout(snapTimer);
  document.removeEventListener("keydown", onEsc);
});

interface Msg {
  role: "user" | "assistant";
  content: string;
  ref?: string;
  failed?: boolean;
}

const msgs = ref<Msg[]>([]);
const ballEl = ref<HTMLElement | null>(null);
const inputEl = ref<{ focus: () => void } | null>(null);

const quickQs = [
  "深衣的形制有什么特点？",
  "马王堆素纱单衣有多轻？",
  "回纹最早出现在什么时候？",
  "曲裾深衣属于哪个朝代？",
];

function scrollBottom() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight;
  });
}

// ===== 截图/图片 =====
const pendingImage = ref("");       // dataURL，待发送
const fileInput = ref<HTMLElement | null>(null);
const shotting = ref(false);

function pickImage() {
  (fileInput.value as HTMLInputElement | null)?.click();
}

// 截取当前网页：用 html2canvas 渲染当前 DOM 为图片
async function takeScreenshot() {
  if (shotting.value) return;
  shotting.value = true;
  note.value = "正在截取页面…";
  try {
    // 动态加载 html2canvas
    if (!(window as any).html2canvas) {
      await new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
      });
    }
    // 临时隐藏对话面板自身，避免截进去
    const panel = document.querySelector(".af-panel") as HTMLElement;
    const float = document.querySelector(".ai-float") as HTMLElement;
    const prevPanel = panel?.style.display;
    const prevFloat = float?.style.display;
    if (panel) panel.style.display = "none";
    if (float) float.style.display = "none";
    await new Promise((r) => setTimeout(r, 100));
    const canvas = await (window as any).html2canvas(document.body, {
      useCORS: true,
      logging: false,
      scale: Math.min(1, 1280 / window.innerWidth),
      backgroundColor: "#f5efe4",
    });
    // 恢复
    if (panel) panel.style.display = prevPanel || "";
    if (float) float.style.display = prevFloat || "";
    pendingImage.value = canvas.toDataURL("image/jpeg", 0.82);
    note.value = "已截取当前页面，可补充问题后发送。";
  } catch (e: any) {
    note.value = "截图失败：" + (e?.message || "请重试");
  } finally {
    shotting.value = false;
  }
}

function onPick(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0];
  if (!f) return;
  readImageFile(f);
  (e.target as HTMLInputElement).value = "";
}

function readImageFile(f: File) {
  const reader = new FileReader();
  reader.onload = () => { pendingImage.value = String(reader.result); };
  reader.readAsDataURL(f);
}

// 面板打开时监听粘贴
function onPaste(e: ClipboardEvent) {
  if (!open.value) return;
  const item = [...(e.clipboardData?.items || [])].find((it) => it.type.startsWith("image/"));
  if (!item) return;
  const f = item.getAsFile();
  if (f) { readImageFile(f); e.preventDefault(); }
}

function ask(q: string) {
  input.value = q;
  send();
}

// 约定：调用前 msgs 末尾必须正好是那条用户提问
async function request(q: string, imageB64 = "") {
  loading.value = true;
  note.value = "";
  scrollBottom();
  // 占位 assistant 气泡，流式往里追加
  const aiMsg: any = { role: "assistant", content: "", ref: "", imageNote: "" };
  msgs.value.push(aiMsg);
  const ai = msgs.value[msgs.value.length - 1]; // 取响应式代理
  try {
    const history = msgs.value.slice(0, -2).map((m) => ({ role: m.role, content: m.content }));
    const resp = await fetch("/api/aiqa/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, history, image_base64: imageB64 }),
    });
    if (!resp.ok || !resp.body) throw new Error("stream fail");
    const reader = resp.body.getReader();
    const dec = new TextDecoder("utf-8");
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const raw = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        let event = "message"; let data = "";
        for (const line of raw.split("\n")) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (event === "meta") {
          try {
            const m = JSON.parse(data);
            if (m.source_ref) ai.ref = m.source_ref;
            if (m.image_note) ai.imageNote = m.image_note;
          } catch {}
        } else if (event === "delta") {
          try {
            const piece = JSON.parse(data);
            if (piece && !ai.content) loading.value = false; // 首字到达：撤下思考动画
            ai.content += piece;
          } catch {}
          scrollBottom();
        } else if (event === "done") {
          // 结束
        }
      }
    }
    if (!ai.content) ai.content = "（未获取到回答）";
  } catch {
    aiMsg.content = "（服务暂不可用，请稍后再试）";
    aiMsg.failed = true;
  } finally {
    loading.value = false;
    scrollBottom();
  }
}

async function send() {
  const q = (input.value || "").trim();
  if (loading.value) return;
  if (!q && !pendingImage.value) return;
  msgs.value.push({ role: "user", content: q || "（看图识服饰）", image: pendingImage.value || "" });
  const b64 = pendingImage.value;
  pendingImage.value = "";
  input.value = "";
  await request(q, b64);
}

function retry(i: number) {
  if (loading.value) return;
  const q = msgs.value[i - 1]?.content;
  if (!q) return;
  msgs.value.splice(i, 1);
  request(q);
}

function onEsc() {
  if (!open.value) return;
  open.value = false;
  ballEl.value?.focus();
}

// 打开：聚焦输入框 + 挂 Esc；关闭：摘掉监听
watch(open, (v) => {
  if (v) {
    document.addEventListener("keydown", onEsc);
    nextTick(() => {
      inputEl.value?.focus();
      scrollBottom();
    });
  } else {
    document.removeEventListener("keydown", onEsc);
  }
});
</script>

<style scoped>
.ai-float {
  position: fixed;
  /* JS 起来前的兜底；挂载后由 left/top 驱动（过约束时 right 被忽略） */
  right: 24px;
  bottom: 24px;
  width: 58px;
  height: 58px;
  z-index: 200;
}
.ai-float.is-snapping {
  transition: left 0.18s ease, top 0.18s ease;
}

/* ===== 悬浮球 ===== */
.af-ball {
  position: absolute;
  inset: 0;
  width: 58px;
  height: 58px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  touch-action: none;
  display: grid;
  place-items: center;
  background: linear-gradient(150deg, #a93226, #7a221c 60%, #5d1a15);
  box-shadow:
    inset 0 0 0 2px rgba(255, 244, 214, 0.6),
    inset 0 0 0 4px rgba(122, 34, 28, 0.55),
    0 6px 20px rgba(90, 24, 18, 0.45);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.af-ball::before {
  content: "";
  position: absolute;
  inset: -7px;
  border-radius: 50%;
  border: 1px solid rgba(201, 162, 39, 0.55);
  animation: afPulse 2.6s ease-out infinite;
  pointer-events: none;
}
@keyframes afPulse {
  0% { transform: scale(0.9); opacity: 0.9; }
  70% { transform: scale(1.15); opacity: 0; }
  100% { transform: scale(1.15); opacity: 0; }
}
.af-ball:hover { transform: translateY(-2px) scale(1.05); }
.af-ball.active { transform: rotate(45deg) scale(0.96); }
.af-ball.dragging {
  cursor: grabbing;
  transform: scale(1.08);
  transition: none;
}
.af-ball.dragging::before { animation: none; opacity: 0; }
.af-ball-seal {
  color: #ffe9c9;
  font-size: 24px;
  font-weight: 800;
  font-family: "Songti SC", "Noto Serif SC", serif;
  text-shadow: 0 1px 3px rgba(60, 12, 8, 0.6);
  user-select: none;
}
.af-ball-tip {
  position: absolute;
  right: 66px;
  top: 50%;
  transform: translateY(-50%) translateX(6px);
  white-space: nowrap;
  font-size: 12px;
  color: #fff;
  background: rgba(90, 24, 18, 0.92);
  border: 1px solid rgba(201, 162, 39, 0.5);
  border-radius: 6px;
  padding: 4px 10px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.af-ball:not(.active):hover .af-ball-tip { opacity: 1; transform: translateY(-50%) translateX(0); }
/* 球吸在左边缘时，提示翻到右侧，避免被裁掉 */
.af-ball.tip-right .af-ball-tip {
  right: auto;
  left: 66px;
  transform: translateY(-50%) translateX(-6px);
}
.af-ball.tip-right:hover .af-ball-tip { transform: translateY(-50%) translateX(0); }
.af-ball.dragging .af-ball-tip { opacity: 0; }

/* ===== 对话面板 ===== */
.af-panel {
  position: absolute;
  left: 0;
  bottom: 70px;
  width: 380px;
  height: 520px;
  display: flex;
  flex-direction: column;
  background: var(--ys-card);
  border: 1px solid #e6dcc8;
  border-radius: 14px;
  box-shadow: 0 18px 48px rgba(60, 24, 12, 0.28), 0 4px 14px rgba(90, 60, 30, 0.12);
  transform-origin: bottom right;
}
.af-panel.is-side-left { transform-origin: bottom left; }
.af-panel.is-down { transform-origin: top right; }
.af-panel.is-down.is-side-left { transform-origin: top left; }
/* 指向悬浮球的小三角：面板在球上方时朝下，翻转时朝上（贴在深红头部上） */
.af-panel::after {
  content: "";
  position: absolute;
  right: 23px;
  bottom: -6px;
  width: 12px;
  height: 12px;
  background: #fffdf8;
  border-right: 1px solid #e6dcc8;
  border-bottom: 1px solid #e6dcc8;
  transform: rotate(45deg);
}
.af-panel.is-side-left::after { right: auto; left: 23px; }
.af-panel.is-down::after {
  bottom: auto;
  top: -6px;
  background: #7e2418;
  border-color: transparent;
}
.af-pop-enter-active { transition: opacity 0.28s ease, transform 0.28s cubic-bezier(0.22, 0.9, 0.3, 1.2); }
.af-pop-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.af-pop-enter-from, .af-pop-leave-to { opacity: 0; transform: translateY(16px) scale(0.97); }
.af-panel.is-down.af-pop-enter-from, .af-panel.is-down.af-pop-leave-to { transform: translateY(-16px) scale(0.97); }

.af-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #7e2418, #a93226 60%, #b98a2f 140%);
  color: #fff;
  position: relative;
  flex: none;
  border-radius: 13px 13px 0 0;
}
.af-head::after {
  content: "";
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(246, 231, 191, 0.8), transparent);
}
.af-head-seal {
  width: 30px;
  height: 30px;
  flex: none;
  display: grid;
  place-items: center;
  border: 2px solid rgba(255, 244, 214, 0.85);
  border-radius: 8px;
  font-size: 15px;
  font-weight: 800;
  color: #ffe9c9;
  transform: rotate(-6deg);
}
.af-head-text { flex: 1; min-width: 0; }
.af-head-text b { display: block; font-size: 15px; letter-spacing: 2px; }
.af-head-text i { display: block; font-style: normal; font-size: var(--ys-fs-micro); color: rgba(255, 255, 255, 0.75); letter-spacing: 2px; margin-top: 2px; }
.af-close {
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.2s;
}
.af-close:hover { background: rgba(255, 255, 255, 0.15); }

/* 空态引导 */
.af-welcome { padding: 2px 0 4px; }
.af-hello { margin: 0 0 12px; font-size: 13.5px; line-height: 1.8; color: var(--ys-ink-2); }
.af-hello b { color: var(--ys-red-deep); font-weight: 700; }
.af-quick-tip { margin: 0 0 8px; font-size: 12px; color: var(--ys-ink-3); }
.af-chips { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.af-chip {
  padding: 8px 10px;
  font-size: 12.5px;
  line-height: 1.5;
  text-align: left;
  color: var(--ys-ink-2);
  background: #f8f1e2;
  border: 1px solid var(--ys-line);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.af-chip:hover { color: var(--ys-red-deep); border-color: rgba(201, 162, 39, 0.6); background: #fdf6e6; transform: translateY(-1px); }
@media (max-width: 480px) {
  .af-chips { grid-template-columns: 1fr; }
}

/* 消息区 */
.af-msgs {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(180deg, #fbf6ec, #f5efe4);
}
.af-row { display: flex; }
.af-row.user { justify-content: flex-end; }
.af-row.assistant { justify-content: flex-start; }
.af-bubble {
  max-width: 84%;
  padding: 9px 13px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}
.af-row.user .af-bubble {
  background: linear-gradient(135deg, #8f2f23, #7a221c);
  color: #fff4dd;
  border-bottom-right-radius: 4px;
}
.af-row.assistant .af-bubble {
  background: #fffdf8;
  border: 1px solid #e6dcc8;
  color: var(--ys-ink);
  border-bottom-left-radius: 4px;
}
.af-ref {
  display: block;
  margin-top: 6px;
  font-size: var(--ys-fs-micro);
  color: var(--ys-ink-3);
}
.af-note {
  margin-top: 2px;
  font-size: var(--ys-fs-micro);
  color: var(--ys-ink-3);
  line-height: 1.6;
}
.af-retry {
  margin-top: 8px;
  padding: 3px 12px;
  font-size: 12px;
  color: var(--ys-red-deep);
  background: #fdf6e6;
  border: 1px solid rgba(201, 162, 39, 0.55);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
}
.af-retry:hover { background: #f8eccf; border-color: var(--ys-red-deep); }
.af-typing { display: inline-flex; gap: 4px; padding: 12px 14px; }
.af-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c9a227;
  animation: afBlink 1.2s infinite;
}
.af-typing span:nth-child(2) { animation-delay: 0.2s; }
.af-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes afBlink {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-3px); }
}

/* 输入区 */
.af-input {
  display: flex;
  align-items: stretch;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid var(--ys-line);
  background: #fffdf8;
  flex: none;
  border-radius: 0 0 13px 13px;
}
.af-input :deep(.el-input__wrapper) {
  background-color: #fbf6ec !important;
  border-radius: 10px;
}
.af-send {
  flex: none;
  border: none;
  padding: 0 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8f2f23, #7a221c);
  color: #fff4dd;
  font-size: 13px;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.2s;
}
.af-send:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(122, 34, 28, 0.35); }
.af-send:disabled { opacity: 0.5; cursor: not-allowed; }

/* 截图问答 */
.af-attach {
  flex: none; border: 1px solid var(--ys-line); background: #fbf6ec;
  border-radius: 10px; padding: 0 12px; cursor: pointer; font-size: 16px;
  display: flex; align-items: center; transition: all .2s;
}
.af-attach:hover:not(:disabled) { background: #f3e6c8; }
.af-attach:disabled { opacity: .5; cursor: not-allowed; }
.af-pending {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; background: #fff8ec; border-top: 1px dashed var(--ys-line);
  flex: none;
}
.af-pending img { width: 46px; height: 46px; object-fit: cover; border-radius: 8px; border: 1px solid var(--ys-line); }
.af-pending-clear { border: none; background: #7a221c; color: #fff; width: 20px; height: 20px; border-radius: 50%; cursor: pointer; line-height: 1; }
.af-thumb {
  max-width: 160px; max-height: 160px; border-radius: 8px; margin: 0 0 6px; display: block;
  border: 1px solid var(--ys-line);
}
.af-img-note { display: block; font-size: 11px; color: var(--ys-ink-3); margin-top: 4px; font-style: italic; }
</style>
