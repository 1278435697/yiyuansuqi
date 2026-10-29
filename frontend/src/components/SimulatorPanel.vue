<template>
  <div class="sim-panel" :class="{ compact }">
    <!-- 时代选择 -->
    <div class="era-tabs">
      <button v-for="(e, i) in eras" :key="e.id" class="era-tab" :class="{ active: i === eraIdx }"
              @click="setEra(i)">
        {{ e.name }}
      </button>
    </div>

    <div class="sim-body">
      <!-- 推演舞台 -->
      <div class="stage-col">
        <h4 class="ys-title">{{ currentEra?.name }} · {{ currentEra?.label }}</h4>
        <div class="stage-meta">
          <span>形制：{{ currentEra?.costume }}</span>
          <span>面料：{{ currentEra?.fabric }}</span>
          <span>纹样：{{ currentEra?.pattern }}</span>
          <span>服色：{{ currentEra?.color }}</span>
        </div>

        <!-- 写实复原图 + 推演特征层 -->
        <div class="figure-wrap" :key="eraIdx">
          <div class="figure-box">
            <div class="stage-ambient" :style="stageGlow"></div>
            <div v-if="eraImage" class="figure-stage" :style="figureStyle">
              <img :src="eraImage" class="figure-img" :alt="`${currentEra?.name}服饰复原`" loading="lazy">
              <svg class="feature-layer" viewBox="0 0 240 340" preserveAspectRatio="xMidYMid slice">
                <!-- 织理层（纺织工艺） -->
                <g v-if="features.fabOp > 0.02" :opacity="features.fabOp" stroke="#8a5a2a" stroke-width="1.3">
                  <line v-for="x in fabricXs" :key="x" :x1="x" :y1="84" :x2="x" :y2="308" />
                </g>
                <!-- 联珠纹领缘/袖缘（对外交流） -->
                <g v-if="features.exOp > 0.06" :opacity="features.exOp">
                  <path d="M92,86 Q120,102 148,86" fill="none" stroke="#d4a017" stroke-width="1.8"/>
                  <circle v-for="(p, i) in beadPos" :key="'b'+i" :cx="p[0]" :cy="p[1]" r="2.1" fill="#d4a017"/>
                </g>
                <!-- 主纹样层（审美变迁·纹样指标） -->
                <g v-if="features.patOp > 0.03" :opacity="features.patOp">
                  <g v-for="(m, i) in features.motifPos" :key="'m'+i" :transform="`translate(${m.x} ${m.y})`">
                    <g v-html="motifSvg(features.motif, features.motifSize)"></g>
                  </g>
                </g>
                <!-- 礼制标识层（玉佩·蔽膝） -->
                <g v-if="features.ritualOp > 0.05" :opacity="features.ritualOp" transform="translate(153 150)">
                  <circle r="7" fill="none" stroke="#d4a017" stroke-width="2"/>
                  <circle r="3.4" fill="none" stroke="#d4a017" stroke-width="1.2"/>
                  <path d="M0,7 L-3.5,26 L0,23 L3.5,26 Z" fill="#c4242a" opacity="0.85"/>
                  <line x1="0" y1="27" x2="0" y2="36" stroke="#d4a017" stroke-width="1.4"/>
                </g>
                <!-- 衣摆线（衣长指标） -->
                <path v-if="features.hemY < 306"
                      :d="`M80,${features.hemY} Q120,${features.hemY + 10} 160,${features.hemY}`"
                      fill="none" stroke="#c08a4a" stroke-width="1.6" stroke-dasharray="4 3" opacity="0.8"/>
                <!-- 广袖轮廓线（袖宽指标） -->
                <path :d="`M78,98 Q${features.sleeveX},150 ${features.sleeveX},212`"
                      fill="none" stroke="#c08a4a" stroke-width="1.6" stroke-dasharray="4 3" opacity="0.6"/>
              </svg>
            </div>
            <div v-else class="figure-fallback">该朝代复原图整理中</div>
            <div v-if="Object.keys(metricDeltas).length" class="figure-badge">
              推演中 · {{ Object.keys(metricDeltas).length }} 项偏离史实
            </div>
          </div>
          <p class="figure-note">史实复原 · 依据出土实物与文献考据绘制</p>
        </div>

        <!-- 指标对比 -->
        <div class="metrics">
          <div v-for="m in metricRows" :key="m.key" class="metric-row">
            <span class="metric-name">{{ m.label }}</span>
            <div class="metric-bar">
              <div class="bar-base" :style="{ width: m.baseline + '%' }"></div>
              <div class="bar-fc" :style="{ width: m.forecast + '%' }"></div>
            </div>
            <span class="metric-val">{{ m.forecast }}<i>/{{ m.baseline }}</i></span>
            <span v-if="metricDeltas[m.key]" class="metric-delta"
                  :class="metricDeltas[m.key] > 0 ? 'up' : 'down'">
              {{ metricDeltas[m.key] > 0 ? "▲" : "▼" }}{{ Math.abs(metricDeltas[m.key]) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 叙事与图谱 -->
      <div class="narrative-col">
        <h4 class="ys-title">服饰详述</h4>
        <p class="narrative-text">{{ narrative }}</p>
        <div class="narrative-ref" v-if="currentEra?.ref">
          <span class="ref-label">史料基线</span>{{ currentEra.ref }}
        </div>

        <h4 class="ys-title" style="margin-top: 14px">知识图谱联动</h4>
        <div class="graph-chips">
          <span v-for="(n, i) in graphNodes" :key="i" class="chip" :class="{ hl: n.highlight }">
            <i>{{ n.type }}</i>{{ n.value }}
          </span>
        </div>

        <h4 class="ys-title" style="margin-top: 14px">千年衣制演变趋势</h4>
        <div ref="trendBox" class="trend-box" style="height: 300px"></div>
        <p class="trend-note">各朝代代表服饰形制指标的千年演变脉络（史实基线）。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { fetchSimulatorEras, simulateEra, fetchSimulatorTrend } from "@/api/modules";
import { EchartTimeSim } from "@/utils/EchartTimeSim";

const props = defineProps<{
  defaultEra?: string;
  compact?: boolean;
}>();

/* 史实基线参数：不再开放调节，按真实史料展示 */
const BASELINE_PARAMS = { ritual: 50, craft: 50, climate: 50, aesthetic: 50, exchange: 50 };

const eras = ref<any[]>([]);
const eraIdx = ref(4);
const forecast = ref<Record<string, number>>({});
const baseline = ref<Record<string, number>>({});
const narrative = ref("");
const trendBox = ref<HTMLDivElement>();
let trendSim: EchartTimeSim | null = null;

const currentEra = computed(() => eras.value[eraIdx.value]);
const metricRows = computed(() =>
  Object.entries(forecast.value).map(([key, value]) => ({
    key, label: ({ silh: "版型", len: "衣长", sleeve: "袖宽", color: "色彩", pat: "纹样", fab: "面料", ritual: "礼制标识" } as any)[key] ?? key,
    forecast: value, baseline: baseline.value[key] ?? 0,
  })),
);

/* 朝代 → 写实复原图映射 */
const ERA_IMG: Record<string, string> = {
  "上古": "/images/dynasty_shanggu.jpg",
  "先秦": "/images/dynasty_xianqin.jpg",
  "秦汉": "/images/dynasty_qinhan.jpg",
  "魏晋": "/images/dynasty_weijin.jpg",
  "隋唐": "/images/dynasty_suitang.jpg",
  "宋": "/images/dynasty_song.jpg",
  "元": "/images/dynasty_yuan.jpg",
  "明": "/images/dynasty_ming.jpg",
  "清": "/images/dynasty_qing.jpg",
};

/* 朝代 → 主纹样类型 */
const ERA_MOTIF: Record<string, string> = {
  "上古": "fuxing", "先秦": "fuxing", "秦汉": "yunwen", "魏晋": "yunwen",
  "隋唐": "baoxiang", "宋": "zhezhi", "元": "tuantuan", "明": "zhezhi", "清": "tuantuan",
};

/* 纹样 SVG 生成（内部数据，安全） */
function motifSvg(type: string, s: number): string {
  const stroke = "#d4a017";
  const fill = "rgba(196,42,58,0.42)";
  switch (type) {
    case "baoxiang": {
      let p = `<circle r="${(s * 0.34).toFixed(1)}" fill="none" stroke="${stroke}" stroke-width="1"/>`;
      for (let i = 0; i < 8; i++) {
        p += `<ellipse transform="rotate(${i * 45}) translate(0,${(-s * 0.62).toFixed(1)})" rx="${(s * 0.28).toFixed(1)}" ry="${(s * 0.5).toFixed(1)}" fill="${fill}" stroke="${stroke}" stroke-width="0.5"/>`;
      }
      return `<g>${p}</g>`;
    }
    case "yunwen": {
      return `<g>` +
        `<path d="M0,0 Q${(s * 0.5).toFixed(1)},${(-s * 0.55).toFixed(1)} ${(s * 0.9).toFixed(1)},${(-s * 0.1).toFixed(1)} Q${(s * 0.75).toFixed(1)},${(s * 0.35).toFixed(1)} 0,0 Z" fill="${fill}" stroke="${stroke}" stroke-width="0.6"/>` +
        `<path d="M0,0 Q${(-s * 0.5).toFixed(1)},${(-s * 0.55).toFixed(1)} ${(-s * 0.9).toFixed(1)},${(-s * 0.1).toFixed(1)} Q${(-s * 0.75).toFixed(1)},${(s * 0.35).toFixed(1)} 0,0 Z" fill="${fill}" stroke="${stroke}" stroke-width="0.6"/>` +
        `<circle r="${(s * 0.22).toFixed(1)}" fill="${fill}" stroke="${stroke}" stroke-width="0.5"/></g>`;
    }
    case "zhezhi": {
      return `<g>` +
        `<path d="M0,${(s * 0.5).toFixed(1)} Q${(s * 0.3).toFixed(1)},0 0,${(-s * 0.5).toFixed(1)}" stroke="${stroke}" stroke-width="0.7" fill="none"/>` +
        `<circle cy="${(-s * 0.55).toFixed(1)}" r="${(s * 0.3).toFixed(1)}" fill="${fill}" stroke="${stroke}" stroke-width="0.6"/>` +
        `<path d="M0,0 Q${(s * 0.35).toFixed(1)},${(-s * 0.1).toFixed(1)} ${(s * 0.5).toFixed(1)},${(s * 0.25).toFixed(1)} Q${(s * 0.2).toFixed(1)},${(s * 0.3).toFixed(1)} 0,0 Z" fill="rgba(58,110,84,0.55)"/></g>`;
    }
    case "tuantuan": {
      let p = `<circle r="${(s * 0.4).toFixed(1)}" fill="none" stroke="${stroke}" stroke-width="0.8"/>`;
      for (let i = 0; i < 12; i++) {
        p += `<path transform="rotate(${i * 30})" d="M0,0 L${(-s * 0.12).toFixed(1)},${(-s * 0.8).toFixed(1)} L${(s * 0.12).toFixed(1)},${(-s * 0.8).toFixed(1)} Z" fill="${fill}" stroke="${stroke}" stroke-width="0.5"/>`;
      }
      return `<g>${p}</g>`;
    }
    case "fuxing": {
      return `<g>` +
        `<path d="M${(-s * 0.5).toFixed(1)},${(s * 0.4).toFixed(1)} L${(s * 0.5).toFixed(1)},${(-s * 0.4).toFixed(1)} L${(s * 0.5).toFixed(1)},0 L0,0 Z" fill="${fill}" stroke="${stroke}" stroke-width="0.6"/>` +
        `<path d="M${(s * 0.5).toFixed(1)},${(-s * 0.4).toFixed(1)} L${(-s * 0.5).toFixed(1)},${(s * 0.4).toFixed(1)} L${(-s * 0.5).toFixed(1)},0 L0,0 Z" fill="none" stroke="${stroke}" stroke-width="0.6"/></g>`;
    }
    default:
      return `<circle r="${(s * 0.4).toFixed(1)}" fill="${fill}" stroke="${stroke}" stroke-width="0.6"/>`;
  }
}

const eraImage = computed(() => (currentEra.value ? ERA_IMG[currentEra.value.name] || "" : ""));

/* 推演特征层：参数 → 真实形制特征（而非整图缩放） */
const features = computed(() => {
  const f = forecast.value;
  const len = f.len ?? 60, sleeve = f.sleeve ?? 60, silh = f.silh ?? 50;
  const pat = f.pat ?? 50, fab = f.fab ?? 50, ritual = f.ritual ?? 50;
  const patOp = Math.max(0, Math.min(1, (pat - 15) / 55));           // 纹样浮现 15→0, 70→1
  const fabOp = Math.max(0, Math.min(0.5, (fab - 20) / 140));        // 织理密度 20→0, 90→0.5
  const ritualOp = Math.max(0, Math.min(1, (ritual - 35) / 45));     // 玉佩出现 35→0, 80→1
  const exOp = Math.max(0, Math.min(1, (pat - 20) / 55));            // 联珠纹领缘（交流+纹样）
  const hemY = 226 + (len / 100) * 60;                               // 衣摆线随衣长升降
  const sleeveX = 76 - ((sleeve - 10) / 90) * 32;                    // 广袖外缘 44-76
  const motif = ERA_MOTIF[currentEra.value?.name] || "baoxiang";
  const motifSize = 9 + patOp * 9;
  const motifPos = [
    { x: 98, y: 114 }, { x: 143, y: 116 },
    { x: 94, y: Math.min(hemY - 8, 292) }, { x: 121, y: Math.min(hemY + 3, 298) }, { x: 149, y: Math.min(hemY - 8, 292) },
  ];
  return { patOp, fabOp, ritualOp, exOp, hemY, sleeveX, motif, motifSize, motifPos };
});

/* 图片滤镜：固定史实基线，仅做柔和的写实呈现 */
const figureStyle = computed(() => {
  return { filter: "saturate(0.99) contrast(1.03) brightness(1.0)" };
});

/* 舞台氛围：固定史实基调 */
const stageGlow = computed(() => {
  return { background: "rgba(180,150,120,0.08)" };
});

/* 织理竖线位置 */
const fabricXs = computed(() => {
  const xs: number[] = [];
  for (let x = 66; x <= 174; x += 8) xs.push(x);
  return xs;
});
/* 联珠纹领缘珠点 */
const beadPos = [[96, 89], [108, 94.5], [120, 96.5], [132, 94.5], [144, 89]];

/* 指标变化幅度（相对史实基线） */
const metricDeltas = computed(() => {
  const out: Record<string, number> = {};
  for (const k of Object.keys(forecast.value)) {
    const f = forecast.value[k] ?? 0, b = baseline.value[k] ?? 0;
    if (Math.abs(f - b) >= 2) out[k] = f - b;
  }
  return out;
});

const graphNodes = computed(() => {
  const e = currentEra.value;
  return e ? [
    { type: "朝代", value: e.name, highlight: true },
    { type: "流行服饰", value: e.costume, highlight: true },
    { type: "代表纹样", value: e.pattern },
    { type: "常用面料", value: e.fabric },
    { type: "服色取向", value: e.color },
  ] : [];
});

async function init() {
  const data: any = await fetchSimulatorEras();
  eras.value = data.eras;

  const idx = eras.value.findIndex((e: any) => e.name === props.defaultEra);
  if (idx >= 0) eraIdx.value = idx;
  await refresh();
  trendSim = new EchartTimeSim([trendBox.value!]);
  await trendSim.load(BASELINE_PARAMS);
}

async function refresh() {
  const res: any = await simulateEra(eraIdx.value, BASELINE_PARAMS);
  forecast.value = res.forecast;
  baseline.value = res.baseline;
  narrative.value = res.narrative;
}

function setEra(i: number) {
  eraIdx.value = i;
  refresh();
  trendSim?.load(BASELINE_PARAMS);
}

onMounted(init);
onBeforeUnmount(() => trendSim?.dispose());
</script>

<style scoped>
.sim-panel { width: 100%; }
.era-tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 14px; }
.era-tab { padding: 5px 12px; border: 1px solid var(--ys-line); border-radius: 16px; background: #fffdf8; cursor: pointer; font-size: 13px; font-family: inherit; color: var(--ys-ink-2); }
.era-tab.active { background: var(--ys-red); color: #fff; border-color: var(--ys-red); }

.sim-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.compact .sim-body { grid-template-columns: 1fr 1fr; }


.stage-col { text-align: center; }
.stage-meta { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; font-size: 13px; color: var(--ys-ink-2); margin-bottom: 8px; }
.figure-wrap { display: flex; flex-direction: column; align-items: center; min-height: 380px; }
.figure-box { position: relative; }
.stage-ambient { position: absolute; inset: 0; border-radius: 8px; transition: background 0.18s ease; pointer-events: none; z-index: 0; }
.figure-stage { position: relative; width: 240px; height: 340px; border-radius: 8px; overflow: hidden; box-shadow: 0 10px 24px rgba(122, 60, 30, 0.18); transition: filter .12s ease; background: #f7f1e4; z-index: 1; }
.figure-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.feature-layer { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.figure-badge { position: absolute; top: 8px; left: 50%; transform: translateX(-50%); background: var(--ys-red); color: #fff; font-size: var(--ys-fs-micro); padding: 2px 10px; border-radius: 12px; white-space: nowrap; box-shadow: 0 2px 8px rgba(169, 50, 38, 0.35); z-index: 2; }
.figure-fallback { width: 200px; height: 300px; display: grid; place-items: center; border: 1px dashed var(--ys-line); border-radius: 8px; color: var(--ys-ink-3); font-size: 13px; }
.figure-note { font-size: var(--ys-fs-micro); color: var(--ys-ink-3); margin-top: 6px; }

.metrics { text-align: left; margin-top: 8px; }
.metric-row { display: flex; align-items: center; gap: 8px; font-size: 12px; margin: 4px 0; }
.metric-name { width: 52px; color: var(--ys-ink-2); }
.metric-bar { flex: 1; position: relative; height: 10px; background: #eee5d2; border-radius: 5px; overflow: hidden; }
.bar-base { position: absolute; left: 0; top: 0; height: 100%; background: rgba(176, 164, 140, 0.35); }
.bar-fc { position: absolute; left: 0; top: 0; height: 100%; background: var(--ys-red); border-radius: 5px; }
.metric-val { width: 64px; text-align: right; font-weight: 700; }
.metric-val i { font-style: normal; color: var(--ys-ink-3); font-weight: 400; }
.metric-delta { width: 40px; text-align: right; font-size: 12px; font-weight: 700; }
.metric-delta.up { color: var(--ys-red-deep); }
.metric-delta.down { color: #3d7a3d; }

.narrative-text { font-size: 13px; line-height: 1.9; color: var(--ys-ink-2); }
.narrative-ref { margin-top: 10px; font-size: 12px; color: var(--ys-ink-3); border-left: 3px solid var(--ys-line); padding-left: 8px; }
.ref-label { display: inline-block; background: var(--ys-bg-deep); color: var(--ys-red-deep); padding: 0 6px; border-radius: 4px; margin-right: 6px; }

.graph-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { border: 1px solid var(--ys-line); background: #fffdf8; border-radius: 6px; padding: 3px 8px; font-size: 12px; }
.chip.hl { border-color: var(--ys-red); color: var(--ys-red-deep); background: rgba(169, 50, 38, 0.05); }
.chip i { font-style: normal; color: var(--ys-ink-3); margin-right: 3px; }

.trend-box { width: 100%; }
.trend-note { font-size: var(--ys-fs-micro); color: var(--ys-ink-3); margin-top: 6px; }

@media (max-width: 1100px) {
  .sim-body { grid-template-columns: 1fr; }
  .compact .sim-body { grid-template-columns: 1fr; }
}
</style>
