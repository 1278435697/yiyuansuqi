<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue';
import { useRouter } from 'vue-router';
import data from '../data/exhibits.json';
import { buildHall, createEngine } from '../museum/scene.js';
import { buildExhibits } from '../museum/exhibits.js';
import { createControls } from '../museum/controls.js';
import { createInteractor } from '../museum/interactions.js';
import {
  applyQuality,
  createFpsMonitor,
  detectQuality,
  nextLowerQuality,
} from '../museum/performance.js';
import { createXR, isVRSupported } from '../museum/xr.js';
import HUD from '../components/HUD.vue';
import ExhibitCard from '../components/ExhibitCard.vue';
import AskPanel from '../components/AskPanel.vue';
import LoadingMask from '../components/LoadingMask.vue';
import CreditsDialog from '../components/CreditsDialog.vue';

const router = useRouter();

const stageEl = ref(null);
const canvasEl = ref(null);

const loading = ref(true);
const loadingText = ref('正在装配数字展厅…');
const quality = ref('high');
const fps = ref(60);
const degraded = ref(false);
const vrAvailable = ref(false);
const xrActive = ref(false);
const modeLabel = ref('桌面漫游模式');
const hoverId = ref('');
const selected = ref(null);
const askOpen = ref(false);
const askExhibit = ref(null);
const creditsOpen = ref(false);

const exhibits = data.exhibits;
const gallery = data.gallery;

const engine = shallowRef(null);
let controls = null;
let interactor = null;
let xr = null;
let fpsMonitor = null;
let hall = null;
let units = [];
let resizeObserver = null;
let lastTime = 0;

const hoverName = computed(() => {
  const ex = exhibits.find((e) => e.id === hoverId.value);
  return ex ? `${ex.dynastyShort} · ${ex.name}` : '';
});

const creditEntries = computed(() => {
  const out = [];
  for (const ex of exhibits) {
    for (const c of ex.credits) out.push(c);
  }
  for (const g of gallery) {
    out.push({ text: g.caption, museum: g.museum, exhibition: '文化墙影像（展厅后墙）', url: g.url });
  }
  return out;
});

const anyModal = computed(() => Boolean(selected.value) || askOpen.value || creditsOpen.value);

watch([anyModal, xrActive], () => {
  if (controls) controls.setEnabled(!anyModal.value && !xrActive.value);
  if (anyModal.value) hoverId.value = '';
});

const resize = () => {
  const el = stageEl.value;
  const eng = engine.value;
  if (!el || !eng) return;
  const w = Math.max(1, el.clientWidth);
  const h = Math.max(1, el.clientHeight);
  eng.renderer.setSize(w, h, false);
  eng.camera.aspect = w / h;
  eng.camera.updateProjectionMatrix();
};

const setQuality = (q) => {
  quality.value = q;
  const eng = engine.value;
  if (!eng) return;
  applyQuality(q, { renderer: eng.renderer, scene: eng.scene, hall, units });
};

const onHover = (x, y) => {
  if (!interactor || anyModal.value) return;
  interactor.setPointer(x, y);
  interactor.hover();
};

const onTap = (x, y) => {
  if (!interactor || anyModal.value) return;
  interactor.setPointer(x, y);
  const id = interactor.select();
  if (!id) return;
  const ex = exhibits.find((e) => e.id === id);
  if (ex) selected.value = ex;
};

const openAsk = (ex) => {
  selected.value = null;
  askExhibit.value = ex || null;
  askOpen.value = true;
};

const goTryon = (ex) => {
  router.push({ name: 'tryon', query: { garment: ex.tryonId, from: 'museum' } });
};

const toggleVR = async () => {
  if (!xr) return;
  if (xrActive.value) {
    xr.exit();
    return;
  }
  try {
    await xr.enter();
  } catch (e) {
    modeLabel.value = 'VR 启动失败 · 保持桌面漫游';
  }
};

const loop = (time) => {
  const eng = engine.value;
  if (!eng) return;
  const dt = lastTime ? Math.min((time - lastTime) / 1000, 0.05) : 0.016;
  lastTime = time;
  if (controls) controls.update(dt);
  if (xr) xr.update(dt);
  if (fpsMonitor) {
    const f = fpsMonitor.tick(time);
    if (f) fps.value = f;
  }
  eng.renderer.render(eng.scene, eng.camera);
};

onMounted(async () => {
  const eng = createEngine(canvasEl.value);
  engine.value = eng;
  resize();
  resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(stageEl.value);

  loadingText.value = '正在构建国风展厅…';
  hall = await buildHall(eng.scene, { ...data.hall, gallery }, eng.loader);

  loadingText.value = '正在装配历代服饰展品…';
  const built = await buildExhibits(eng.scene, exhibits, eng.loader);
  units = built.units;

  loadingText.value = '正在优化渲染设置…';
  const info = detectQuality(eng.renderer);
  quality.value = info.quality;
  applyQuality(quality.value, { renderer: eng.renderer, scene: eng.scene, hall, units });

  controls = createControls({
    camera: eng.camera,
    rig: eng.rig,
    domElement: canvasEl.value,
    bounds: hall.bounds,
    obstacles: built.obstacles,
    onHover,
    onTap,
    start: { x: 0, z: 6.6, yaw: 0 },
  });

  interactor = createInteractor({
    camera: eng.camera,
    targets: built.picks,
    onHoverChange: (id) => {
      hoverId.value = id || '';
    },
  });

  fpsMonitor = createFpsMonitor({
    onDegrade: () => {
      const nq = nextLowerQuality(quality.value);
      if (nq !== quality.value) {
        degraded.value = true;
        setQuality(nq);
      }
    },
  });

  vrAvailable.value = await isVRSupported();
  xr = createXR({
    renderer: eng.renderer,
    scene: eng.scene,
    camera: eng.camera,
    rig: eng.rig,
    bounds: hall.bounds,
    obstacles: built.obstacles,
    onStateChange: (act, label) => {
      xrActive.value = act;
      modeLabel.value = label;
      hoverId.value = '';
    },
  });

  loading.value = false;
  lastTime = 0;
  eng.renderer.setAnimationLoop(loop);
});

onBeforeUnmount(() => {
  const eng = engine.value;
  if (eng) eng.renderer.setAnimationLoop(null);
  if (resizeObserver) resizeObserver.disconnect();
  if (controls) controls.dispose();
  if (interactor) interactor.dispose();
  if (xr) xr.dispose();
  if (eng) eng.renderer.dispose();
  engine.value = null;
});
</script>

<template>
  <div ref="stageEl" class="museum">
    <canvas ref="canvasEl" class="scene-canvas" />

    <HUD
      :mode-label="modeLabel"
      :quality="quality"
      :fps="fps"
      :vr-available="vrAvailable"
      :xr-active="xrActive"
      :hover-name="hoverName"
      :degraded="degraded"
      @toggle-vr="toggleVR"
      @set-quality="setQuality"
      @open-credits="creditsOpen = true"
    />

    <ExhibitCard
      :exhibit="selected"
      @close="selected = null"
      @tryon="goTryon"
      @ask="openAsk"
    />

    <AskPanel :open="askOpen" :exhibit="askExhibit" @close="askOpen = false" />

    <CreditsDialog :open="creditsOpen" :entries="creditEntries" @close="creditsOpen = false" />

    <LoadingMask :visible="loading" :text="loadingText" />
  </div>
</template>

<style scoped>
.museum {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: #0c0b0e;
}

.scene-canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
  touch-action: none;
}

.scene-canvas:active {
  cursor: grabbing;
}
</style>
