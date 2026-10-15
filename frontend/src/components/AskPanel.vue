<script setup>
import { nextTick, ref, watch } from 'vue';
import { askLocal, SUGGESTIONS } from '../data/knowledge.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  exhibit: { type: Object, default: null },
});
const emit = defineEmits(['close']);

// 对接主站后端：开发直连 8765，生产走同源 /api（与 src/api/request.ts 一致）
const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? 'http://127.0.0.1:8765' : '');

const messages = ref([]);
const input = ref('');
const pending = ref(false);
const listEl = ref(null);

const scrollDown = async () => {
  await nextTick();
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight;
};

const askBackend = async (question) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const history = messages.value.slice(0, -1).map((m) => ({
      role: m.role === 'ai' ? 'assistant' : 'user',
      content: m.text,
    }));
    const res = await fetch(`${API_BASE}/api/aiqa/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!data || !data.answer) throw new Error('empty answer');
    return { answer: data.answer, source: data.source_ref || data.source || 'AI 溯源知识库' };
  } finally {
    clearTimeout(timer);
  }
};

const submit = async (text) => {
  const question = (text ?? input.value).trim();
  if (!question || pending.value) return;
  input.value = '';
  messages.value.push({ role: 'user', text: question });
  pending.value = true;
  scrollDown();
  let reply = null;
  try {
    reply = await askBackend(question);
  } catch (e) {
    reply = { answer: askLocal(question), source: '本地知识库（后端未启动）' };
  }
  messages.value.push({ role: 'ai', text: reply.answer, source: reply.source });
  pending.value = false;
  scrollDown();
};

watch(
  () => props.open,
  (v) => {
    if (!v) return;
    messages.value = [];
    if (props.exhibit) {
      messages.value.push({
        role: 'ai',
        text: `正在查看「${props.exhibit.dynasty}·${props.exhibit.name}」。可以问我关于它的形制、纹样、材质或历史，也可以问其他朝代的服饰。`,
        source: '展厅导览',
      });
    } else {
      messages.value.push({
        role: 'ai',
        text: '我是衣溯 AI 服饰导览，可以问我历代汉服的形制、纹样与工艺。',
        source: '展厅导览',
      });
    }
  },
);
</script>

<template>
  <div v-if="open" class="ask-mask" @click.self="emit('close')">
    <div class="ask-panel">
      <div class="head">
        <div class="t">问 AI · 服饰史料问答</div>
        <button class="close" @click="emit('close')">×</button>
      </div>

      <div ref="listEl" class="list">
        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble">{{ m.text }}</div>
          <div v-if="m.source" class="src">{{ m.source }}</div>
        </div>
        <div v-if="pending" class="msg ai">
          <div class="bubble typing">正在检索知识库…</div>
        </div>
      </div>

      <div class="suggest">
        <button v-for="s in SUGGESTIONS" :key="s" @click="submit(s)">{{ s }}</button>
      </div>

      <div class="input-row">
        <input
          v-model="input"
          type="text"
          placeholder="输入你的问题，例如：马面裙的名称由来？"
          @keyup.enter="submit()"
        />
        <button class="send" :disabled="pending" @click="submit()">提问</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ask-mask {
  position: absolute;
  inset: 0;
  z-index: 32;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  padding: 16px;
  background: rgba(8, 6, 5, 0.5);
}

.ask-panel {
  display: flex;
  flex-direction: column;
  width: min(420px, 92vw);
  height: min(560px, 78vh);
  background: linear-gradient(180deg, #241a14, #1a120e);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.45);
  border-radius: 8px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.6);
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(var(--silk-gold-rgb), 0.24);
}

.t {
  font-size: 14px;
  letter-spacing: 1px;
  color: var(--silk-gold-soft);
}

.close {
  width: 26px;
  height: 26px;
  font-size: 18px;
  color: #d8c8a8;
  background: transparent;
  border: none;
}

.list {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.msg {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 88%;
}

.msg.user {
  align-self: flex-end;
  align-items: flex-end;
}

.bubble {
  padding: 9px 12px;
  font-size: 13px;
  line-height: 1.75;
  border-radius: 8px;
  background: rgba(var(--silk-gold-rgb), 0.12);
  color: #ded2b8;
  white-space: pre-wrap;
}

.msg.user .bubble {
  background: var(--ink-red);
  color: #f6ead5;
}

.bubble.typing {
  color: #a89b83;
  font-style: italic;
}

.src {
  font-size: 10.5px;
  color: #857a68;
}

.suggest {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 12px 10px;
}

.suggest button {
  padding: 4px 9px;
  font-size: 11.5px;
  color: #cbbfa9;
  background: transparent;
  border: 1px solid rgba(var(--silk-gold-rgb), 0.3);
  border-radius: 12px;
}

.input-row {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid rgba(var(--silk-gold-rgb), 0.24);
}

.input-row input {
  flex: 1;
  padding: 9px 12px;
  font-size: 13px;
  color: #ece2cf;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.3);
  border-radius: 4px;
  outline: none;
}

.input-row input:focus {
  border-color: var(--silk-gold);
}

.send {
  padding: 0 18px;
  font-size: 13px;
  color: #1a1310;
  background: var(--silk-gold);
  border: 1px solid var(--silk-gold);
  border-radius: 4px;
}

.send:disabled {
  opacity: 0.5;
}
</style>
