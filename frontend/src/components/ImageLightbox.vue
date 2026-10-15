<template>
  <Teleport to="body">
    <div v-if="url" class="ys-lightbox" @click.self="close" @wheel.prevent="onWheel">
      <button class="lb-close" title="关闭" @click="close">✕</button>
      <div class="lb-stage" :class="{ full: fullSize }" @click.self="close">
        <img :src="url" :alt="alt" class="lb-img" :class="{ full: fullSize }" @click="toggleSize" draggable="false" />
      </div>
      <div class="lb-hint">
        <span>{{ fullSize ? "已放大：点击图片恢复适应" : "点击图片放大细节" }}</span>
        <span>·</span>
        <span>点击背景或 ✕ 关闭</span>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";

const url = ref("");
const alt = ref("");
const fullSize = ref(false);

function open(src: string, text = "") {
  url.value = src;
  alt.value = text;
  fullSize.value = false;
  document.body.style.overflow = "hidden";
}
function close() {
  url.value = "";
  document.body.style.overflow = "";
}
function toggleSize() {
  fullSize.value = !fullSize.value;
}
let zoom = 1;
function onWheel(e: WheelEvent) {
  if (!fullSize.value) return;
  zoom = Math.min(6, Math.max(1, zoom + (e.deltaY < 0 ? 0.15 : -0.15)));
  const img = document.querySelector<HTMLElement>(".lb-stage.full .lb-img");
  if (img) img.style.transform = `scale(${zoom})`;
}
function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") close();
}
onMounted(() => document.addEventListener("keydown", onKey));
onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKey);
  document.body.style.overflow = "";
});

// 全局点击拦截：任何 <img> 点击即放大查看
function onDocClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  const img = target.closest("img");
  if (!img || !img.src) return;
  // 数字博物馆展厅内的图片由展品卡片自行接管，避免抢占缩略图点击
  if (img.closest(".museum")) return;
  // 数据为空（如懒加载占位）不弹
  if (!img.currentSrc && !img.src) return;
  e.preventDefault();
  e.stopPropagation();
  open(img.currentSrc || img.src, img.alt || "");
}
onMounted(() => document.addEventListener("click", onDocClick, true));
onBeforeUnmount(() => document.removeEventListener("click", onDocClick, true));

defineExpose({ open });
</script>

<style scoped>
.ys-lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(12, 10, 8, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
  animation: lb-fade 0.18s ease;
}
.lb-close {
  position: absolute;
  top: 18px;
  right: 22px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  z-index: 2;
  transition: background 0.15s;
}
.lb-close:hover { background: rgba(255, 255, 255, 0.22); }
.lb-stage {
  max-width: 94vw;
  max-height: 90vh;
  overflow: auto;
  border-radius: 6px;
  cursor: zoom-in;
}
.lb-stage.full {
  cursor: grab;
  max-width: 96vw;
  max-height: 94vh;
}
.lb-img {
  display: block;
  max-width: 94vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 4px;
  user-select: none;
  transform-origin: center center;
  transition: transform 0.1s ease;
}
.lb-img.full {
  max-width: none;
  max-height: none;
  width: auto;
  height: auto;
  transform: scale(1);
}
.lb-hint {
  position: absolute;
  bottom: 18px;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.55);
  font-size: 13px;
  display: flex;
  gap: 8px;
  justify-content: center;
  pointer-events: none;
}
@keyframes lb-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
