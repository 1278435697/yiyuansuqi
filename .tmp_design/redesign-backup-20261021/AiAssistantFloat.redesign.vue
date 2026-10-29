<template>
  <!-- 全局悬浮 AI 助手：右下角印章球 + 展开对话面板 -->
  <div class="ai-float">
    <!-- 对话面板 -->
    <transition name="af-pop">
      <div v-if="open" class="af-panel">
        <div class="af-head">
          <span class="af-head-seal">问</span>
          <div class="af-head-text">
            <b>衣溯 · 华夏衣冠志</b>
            <i>溯源 · 复原 · 传承</i>
          </div>
          <button class="af-close" title="收起" @click="open = false">×</button>
        </div>

        <!-- 快捷问题 -->
        <div v-if="!msgs.length" class="af-quick">
          <p class="af-quick-tip">可以从这里开始问：</p>
          <button v-for="q in quickQs" :key="q" class="af-chip" @click="ask(q)">{{ q }}</button>
        </div>

        <!-- 消息区 -->
        <div ref="listEl" class="af-msgs">
          <div v-for="(m, i) in msgs" :key="i" class="af-row" :class="m.role">
            <div class="af-bubble">
              <p>{{ m.content }}</p>
              <span v-if="m.ref" class="af-ref">引用：{{ m.ref }}</span>
            </div>
          </div>
          <div v-if="loading" class="af-row assistant">
            <div class="af-bubble af-typing"><span></span><span></span><span></span></div>
          </div>
          <div v-if="note" class="af-note">{{ note }}</div>
        </div>

        <!-- 输入区 -->
        <div class="af-input">
          <el-input v-model="input" placeholder="问我任何服饰溯源问题…" size="small" clearable
                    @keyup.enter="send" :disabled="loading" />
          <button class="af-send" :disabled="loading" @click="send">发送</button>
        </div>
      </div>
    </transition>

    <!-- 悬浮球 -->
    <button class="af-ball" :class="{ active: open }" title="衣溯 · 华夏衣冠志 助手" @click="open = !open">
      <span class="af-ball-seal">问</span>
      <span class="af-ball-tip">衣溯 · 华夏衣冠志 助手</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from "vue";
import { fetchAiChat } from "@/api/modules";

const open = ref(false);
const input = ref("");
const loading = ref(false);
const note = ref("");
const listEl = ref<HTMLElement | null>(null);

interface Msg {
  role: "user" | "assistant";
  content: string;
  ref?: string;
}

const msgs = ref<Msg[]>([]);

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

function ask(q: string) {
  input.value = q;
  send();
}

async function send() {
  const q = (input.value || "").trim();
  if (!q || loading.value) return;
  msgs.value.push({ role: "user", content: q });
  input.value = "";
  loading.value = true;
  note.value = "";
  scrollBottom();
  try {
    const history = msgs.value.slice(0, -1).map((m) => ({ role: m.role, content: m.content }));
    const res: any = await fetchAiChat({ question: q, history });
    msgs.value.push({ role: "assistant", content: res.answer || "（未获取到回答）", ref: res.source_ref || "" });
    note.value = res.note || "";
  } catch {
    msgs.value.push({ role: "assistant", content: "（服务暂不可用，请稍后再试）", ref: "" });
  } finally {
    loading.value = false;
    scrollBottom();
  }
}

// 打开时聚焦输入框
watch(open, (v) => {
  if (v) nextTick(() => scrollBottom());
});
</script>

<style scoped>
.ai-float {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

/* ===== 悬浮球 ===== */
.af-ball {
  position: relative;
  width: 56px;
  height: 56px;
  border: 1px solid rgba(124, 43, 30, 0.85);
  border-radius: 0;
  cursor: pointer;
  display: grid;
  place-items: center;
  background: var(--ys-red);
  box-shadow: 0 8px 24px rgba(23, 20, 15, 0.18);
  transition: transform 0.3s var(--ease), background-color 0.3s var(--ease), box-shadow 0.3s var(--ease);
}
.af-ball::before {
  content: '';
  position: absolute;
  inset: 4px;
  border: 1px solid rgba(247, 244, 238, 0.32);
  pointer-events: none;
}
.af-ball::after {
  content: '';
  position: absolute;
  inset: -6px;
  border: 1px solid rgba(138, 106, 36, 0.4);
  animation: afPulse 3.2s var(--ease) infinite;
  pointer-events: none;
}
@keyframes afPulse {
  0% { transform: scale(0.94); opacity: 0.8; }
  70%, 100% { transform: scale(1.12); opacity: 0; }
}
.af-ball:hover {
  transform: translateY(-2px);
  background: var(--ys-red-deep);
  box-shadow: 0 12px 28px rgba(23, 20, 15, 0.24);
}
.af-ball.active { transform: scale(0.96); }
.af-ball-seal {
  color: var(--paper);
  font-size: 22px;
  font-weight: 600;
  font-family: var(--font-serif);
  text-shadow: none;
  user-select: none;
  letter-spacing: 0;
}
.af-ball-tip {
  position: absolute;
  right: 66px;
  top: 50%;
  transform: translateY(-50%) translateX(6px);
  white-space: nowrap;
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--ys-ink);
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 0;
  padding: 4px 10px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s var(--ease), transform 0.25s var(--ease);
}
.af-ball:hover .af-ball-tip { opacity: 1; transform: translateY(-50%) translateX(0); }

/* ===== 对话面板 ===== */
.af-panel {
  width: 384px;
  max-height: 580px;
  display: flex;
  flex-direction: column;
  margin-bottom: 14px;
  background: var(--paper);
  border: 1px solid var(--line-2);
  border-top: 2px solid var(--ink);
  border-radius: 0;
  overflow: hidden;
  box-shadow: 0 24px 60px -24px rgba(23, 20, 15, 0.4);
}
.af-pop-enter-active { transition: opacity 0.3s var(--ease), transform 0.36s var(--ease); }
.af-pop-leave-active { transition: opacity 0.2s var(--ease), transform 0.2s var(--ease); }
.af-pop-enter-from, .af-pop-leave-to { opacity: 0; transform: translateY(14px); }

.af-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px 14px;
  background: transparent;
  color: var(--ys-ink);
  position: relative;
  border-bottom: 1px solid var(--line);
}
.af-head::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 56px;
  height: 1px;
  background: var(--ys-gold);
}
.af-head-seal {
  width: 34px;
  height: 34px;
  flex: none;
  display: grid;
  place-items: center;
  border: 1px solid var(--ys-red);
  border-radius: 0;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--ys-red);
  transform: none;
  position: relative;
}
.af-head-seal::after {
  content: '';
  position: absolute;
  inset: 3px;
  border: 1px solid rgba(156, 59, 42, 0.3);
}
.af-head-text { flex: 1; min-width: 0; }
.af-head-text b {
  display: block;
  font-family: var(--font-serif);
  font-size: 15px;
  letter-spacing: 0.16em;
  font-weight: 600;
}
.af-head-text i {
  display: block;
  font-style: normal;
  font-size: 9.5px;
  color: var(--ys-ink-3);
  letter-spacing: 0.22em;
  margin-top: 3px;
  text-transform: uppercase;
}
.af-close {
  border: none;
  background: transparent;
  color: var(--ys-ink-3);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 0;
  transition: color 0.2s var(--ease);
}
.af-close:hover { background: transparent; color: var(--ys-red); }

/* 快捷问题 */
.af-quick { padding: 14px 18px 6px; }
.af-quick-tip { margin: 0 0 10px; font-size: 10.5px; letter-spacing: 0.16em; color: var(--ys-gold); }
.af-chip {
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 0;
  padding: 9px 2px;
  font-size: 12.5px;
  color: var(--ys-ink-2);
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--line);
  border-radius: 0;
  cursor: pointer;
  transition: padding-left 0.3s var(--ease), color 0.3s var(--ease);
}
.af-chip:hover {
  color: var(--ys-red-deep);
  border-color: var(--line);
  background: transparent;
  transform: none;
  padding-left: 10px;
}

/* 消息区 */
.af-msgs {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 140px;
  max-height: 330px;
  background: transparent;
  scrollbar-width: thin;
  scrollbar-color: var(--line-2) transparent;
}
.af-row { display: flex; animation: afMsgIn 0.4s var(--ease) both; }
@keyframes afMsgIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.af-row.user { justify-content: flex-end; }
.af-row.assistant { justify-content: flex-start; }
.af-bubble {
  max-width: 84%;
  padding: 10px 14px;
  border-radius: 0;
  font-size: 13px;
  line-height: 1.85;
  word-break: break-word;
}
.af-row.user .af-bubble {
  background: var(--ys-red);
  color: #fbf6ee;
  border-right: 3px solid var(--ys-red-deep);
}
.af-row.assistant .af-bubble {
  background: transparent;
  border: 0;
  border-left: 1px solid var(--ys-gold);
  padding-left: 14px;
  padding-right: 0;
  color: var(--ys-ink);
}
.af-ref {
  display: block;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--line);
  font-size: 10.5px;
  color: var(--ys-ink-3);
}
.af-note {
  padding: 0 18px 12px;
  font-size: 10.5px;
  color: var(--ys-ink-3);
  line-height: 1.7;
  letter-spacing: 0.03em;
}
.af-typing { display: inline-flex; gap: 5px; padding: 14px; }
.af-typing span {
  width: 5px;
  height: 5px;
  border-radius: 0;
  background: var(--ys-gold);
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
  gap: 8px;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--line);
  background: transparent;
}
.af-input :deep(.el-input__wrapper) { background-color: transparent !important; }
.af-send {
  flex: none;
  border: 1px solid var(--ys-red-deep);
  padding: 6px 16px;
  border-radius: 0;
  background: var(--ys-red);
  color: #fbf6ee;
  font-size: 12px;
  letter-spacing: 0.2em;
  cursor: pointer;
  transition: background-color 0.25s var(--ease);
}
.af-send:hover:not(:disabled) { transform: none; box-shadow: none; background: var(--ys-red-deep); }
.af-send:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 480px) {
  .af-panel { width: calc(100vw - 32px); max-height: 62vh; }
  .ai-float { right: 14px; bottom: 14px; }
}
@media (prefers-reduced-motion: reduce) {
  .af-ball::after, .af-row { animation: none; }
  .af-ball, .af-chip, .af-ball-tip, .af-send { transition: none; }
}
</style>
