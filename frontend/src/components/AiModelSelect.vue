<script setup lang="ts">
import { onMounted, ref } from "vue";
import { AI_MODEL_FALLBACK, aiModel, setAiModel } from "@/utils/aiModel";

const props = defineProps<{ modelValue?: string; compact?: boolean; label?: string }>();
const emit = defineEmits<{ (e: "update:modelValue", v: string): void }>();

interface ModelItem { id: string; label?: string; note?: string; default?: boolean }
const items = ref<ModelItem[]>([]);
const cur = ref(props.modelValue || aiModel() || "");
const tip = ref("");

const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? "http://127.0.0.1:8765" : "");

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/aiqa/models`);
    const data = await res.json();
    if (data?.items?.length) items.value = data.items;
  } catch {
    items.value = AI_MODEL_FALLBACK as ModelItem[];
  }
  if (!items.value.length) items.value = AI_MODEL_FALLBACK as ModelItem[];
  // 本地记忆优先，其次后端标记的默认模型，最后取清单第一个
  const saved = aiModel();
  const hit = items.value.find((m) => m.id === saved && saved)
    || items.value.find((m) => m.default)
    || items.value[0];
  if (!items.value.some((m) => m.id === cur.value)) cur.value = hit?.id || "";
  syncTip();
  emit("update:modelValue", cur.value);
});

function syncTip() {
  tip.value = items.value.find((m) => m.id === cur.value)?.note || "";
}

function onChange() {
  setAiModel(cur.value);
  syncTip();
  emit("update:modelValue", cur.value);
}
</script>

<template>
  <label class="ams" :class="{ compact: props.compact }">
    <span class="ams-k">{{ props.label || "模型" }}</span>
    <select v-model="cur" class="ams-s" @change="onChange">
      <option v-for="m in items" :key="m.id" :value="m.id">{{ m.label || m.id }}</option>
    </select>
    <span v-if="tip && !props.compact" class="ams-tip">{{ tip }}</span>
  </label>
</template>

<style scoped>
.ams {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 4px 3px 10px;
  border: 1px solid rgba(201, 162, 39, 0.55);
  border-radius: 999px;
  background: linear-gradient(180deg, #fffaf0, #f6efe2);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  font-size: 12px;
  color: #6b2020;
  max-width: 100%;
}
.ams-k {
  letter-spacing: 0.14em;
  color: #9a7b2e;
  white-space: nowrap;
  font-size: 11px;
}
.ams-s {
  appearance: none;
  border: 0;
  outline: none;
  background: transparent;
  color: #6b2020;
  font: inherit;
  font-weight: 600;
  padding: 2px 18px 2px 2px;
  cursor: pointer;
  max-width: 190px;
  background-image: linear-gradient(45deg, transparent 50%, #9a7b2e 50%), linear-gradient(135deg, #9a7b2e 50%, transparent 50%);
  background-position: calc(100% - 8px) center, calc(100% - 3px) center;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
}
.ams-tip {
  color: #9a8a6a;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
}
.ams.compact {
  padding: 2px 3px 2px 8px;
  font-size: 11px;
  gap: 4px;
}
@media (max-width: 720px) {
  .ams-tip { display: none; }
  .ams-s { max-width: 132px; }
}
</style>
