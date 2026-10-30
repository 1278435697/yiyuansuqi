<script setup>
defineProps({
  visible: { type: Boolean, default: true },
  text: { type: String, default: '正在装配数字展厅…' },
});
</script>

<template>
  <transition name="fade">
    <div v-if="visible" class="loading">
      <div class="seal">衣源溯起</div>
      <div class="ring" />
      <div class="text">{{ text }}</div>
      <div class="sub">Three.js + WebXR · 无需头显，浏览器直接逛展</div>
    </div>
  </transition>
</template>

<style scoped>
.loading {
  position: absolute;
  inset: 0;
  z-index: 40;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background: radial-gradient(circle at 50% 45%, #211812, #0c0a09 70%);
}

.seal {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  font-size: 22px;
  letter-spacing: 2px;
  color: #f7edd9;
  background: var(--ink-red);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.7);
  border-radius: 6px;
}

.ring {
  width: 34px;
  height: 34px;
  border: 2px solid rgba(var(--silk-gold-rgb), 0.25);
  border-top-color: var(--silk-gold);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.text {
  font-size: 14px;
  letter-spacing: 2px;
  color: var(--silk-gold-soft);
}

.sub {
  font-size: 11.5px;
  color: #8e8471;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.fade-leave-active {
  transition: opacity 0.5s;
}

.fade-leave-to {
  opacity: 0;
}
</style>
