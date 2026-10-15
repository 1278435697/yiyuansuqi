<template>
  <component :is="tag" :class="['reveal-title', cls]" :style="wrapperDelay">
    <span v-for="(ch, i) in chars" :key="i" class="rt-ch"
          :style="{ animationDelay: (base + i * step) + 's' }">{{ ch }}</span>
  </component>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  text: string;
  tag?: string;
  cls?: string;
  delay?: number;   // 首字起始延迟（秒）
  step?: number;    // 相邻字间隔（秒）
}>(), { tag: "h2", cls: "", delay: 0.12, step: 0.05 });

const chars = computed(() =>
  props.text.split("").map((ch) => (ch === " " ? "\u00A0" : ch))
);
const base = computed(() => props.delay);
const wrapperDelay = computed(() => ({ animationDelay: props.delay + "s" }));
</script>

<style scoped>
.reveal-title { line-height: 1.4; }
/* 逐字“跳动浮现”：每字从下方弹起、带弹性回弹，节奏分明 */
.rt-ch {
  display: inline-block;
  opacity: 0;
  transform: translateY(38px) scale(0.9);
  animation: rtJump 0.62s cubic-bezier(0.18, 0.89, 0.32, 1.26) forwards;
  will-change: transform, opacity;
}
@keyframes rtJump {
  0%   { opacity: 0; transform: translateY(38px) scale(0.9); }
  55%  { opacity: 1; transform: translateY(-5px) scale(1.05); }
  78%  { opacity: 1; transform: translateY(3px) scale(0.99); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
