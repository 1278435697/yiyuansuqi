<script setup>
const props = defineProps({
  modeLabel: { type: String, default: '桌面漫游模式' },
  quality: { type: String, default: 'high' },
  fps: { type: Number, default: 60 },
  vrAvailable: { type: Boolean, default: false },
  xrActive: { type: Boolean, default: false },
  hoverName: { type: String, default: '' },
  degraded: { type: Boolean, default: false },
});

const emit = defineEmits(['toggle-vr', 'set-quality', 'open-credits']);

const QUALITY_LABEL = { high: '高', medium: '中', low: '低' };
const label = (q) => QUALITY_LABEL[q] || q;
const qualityText = () => label(props.quality);
</script>

<template>
  <div class="hud">
    <!-- 左上：操作说明与状态 -->
    <div class="panel tl">
      <div class="title-row">
        <div class="museum-title">衣溯 · 华夏服饰数字博物馆</div>
        <router-link to="/" class="back-link">返回主站</router-link>
      </div>
      <ul class="keys">
        <li><b>W / A / S / D</b><span>漫游展厅</span></li>
        <li><b>鼠标拖拽</b><span>环顾四周</span></li>
        <li><b>点击实物影像</b><span>查看服饰史料</span></li>
        <li><b>Shift</b><span>加速行走</span></li>
      </ul>
      <div class="row">
        <span class="tag">{{ modeLabel }}</span>
        <span class="tag">画质 {{ qualityText() }}</span>
        <span class="tag">{{ Math.round(fps) }} FPS</span>
        <span v-if="degraded" class="tag warn">已自动降档</span>
      </div>
      <div class="row q">
        <span class="qlabel">画质</span>
        <button
          v-for="q in ['high', 'medium', 'low']"
          :key="q"
          :class="{ on: quality === q }"
          @click="emit('set-quality', q)"
        >
          {{ label(q) }}
        </button>
        <button class="ghost" @click="emit('open-credits')">图片来源</button>
      </div>
    </div>

    <!-- 右上：VR 模式开关 -->
    <div class="panel tr">
      <button v-if="vrAvailable" class="vr" :class="{ on: xrActive }" @click="emit('toggle-vr')">
        {{ xrActive ? '退出 VR 模式' : '进入 VR 模式' }}
      </button>
      <div v-else class="vr-hint">
        <b>未检测到 VR 设备</b>
        <span>已启用桌面漫游 · WebXR 兼容头显可一键进入</span>
      </div>
    </div>

    <!-- 悬停提示 -->
    <div v-if="hoverName" class="hover-tip">
      <b>{{ hoverName }}</b>
      <span>点击查看详情</span>
    </div>

    <div class="crosshair" />
  </div>
</template>

<style scoped>
.hud {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 10;
  font-size: 13px;
  color: #ece2cf;
}

.panel {
  position: absolute;
  background: rgba(20, 15, 12, 0.62);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.3);
  border-radius: 6px;
  padding: 12px 14px;
  backdrop-filter: blur(6px);
  pointer-events: auto;
}

.tl {
  top: 16px;
  left: 16px;
  min-width: 240px;
}

.tr {
  top: 16px;
  right: 16px;
  text-align: right;
}

.museum-title {
  font-size: 15px;
  letter-spacing: 2px;
  color: var(--silk-gold-soft);
  margin-bottom: 8px;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 8px;
}

.title-row .museum-title {
  margin-bottom: 0;
}

.back-link {
  flex: 0 0 auto;
  font-size: 12px;
  color: #d8c8a8;
  border-bottom: 1px solid rgba(var(--silk-gold-rgb), 0.35);
}

.back-link:hover {
  color: var(--silk-gold-soft);
}

.keys {
  list-style: none;
  margin: 0 0 10px;
  padding: 0;
}

.keys li {
  display: flex;
  gap: 10px;
  align-items: baseline;
  padding: 2px 0;
  color: #bfb3a0;
}

.keys b {
  min-width: 84px;
  color: var(--silk-gold);
  font-weight: 600;
  letter-spacing: 0.5px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.tag {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 3px;
  background: rgba(var(--silk-gold-rgb), 0.12);
  color: #d8c8a8;
}

.tag.warn {
  background: rgba(200, 80, 60, 0.28);
  color: #f0bda8;
}

.qlabel {
  font-size: 12px;
  color: #9c917f;
}

.row.q button {
  padding: 2px 10px;
  font-size: 12px;
  color: #cbbfa9;
  background: transparent;
  border: 1px solid rgba(var(--silk-gold-rgb), 0.34);
  border-radius: 3px;
}

.row.q button.on {
  color: #1a1310;
  background: var(--silk-gold);
  border-color: var(--silk-gold);
}

.row.q button.ghost {
  margin-left: auto;
  color: #d8c8a8;
}

.vr {
  padding: 9px 16px;
  font-size: 13px;
  letter-spacing: 1px;
  color: #1a1310;
  background: linear-gradient(180deg, var(--silk-gold-soft), var(--silk-gold));
  border: 1px solid var(--silk-gold);
  border-radius: 4px;
}

.vr.on {
  color: #f7edd9;
  background: var(--ink-red);
  border-color: var(--silk-gold);
}

.vr-hint {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 210px;
  font-size: 12px;
  color: #b3a894;
}

.vr-hint b {
  color: #dcc9a4;
  font-size: 13px;
}

.hover-tip {
  position: absolute;
  left: 50%;
  bottom: 74px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 18px;
  border-radius: 4px;
  background: rgba(20, 15, 12, 0.72);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.4);
}

.hover-tip b {
  color: var(--silk-gold-soft);
  font-size: 15px;
  letter-spacing: 1px;
}

.hover-tip span {
  font-size: 11px;
  color: #a79b88;
}

.crosshair {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 6px;
  height: 6px;
  margin: -3px 0 0 -3px;
  border-radius: 50%;
  background: rgba(233, 219, 190, 0.75);
  box-shadow: 0 0 0 1px rgba(20, 15, 12, 0.6);
}
</style>
