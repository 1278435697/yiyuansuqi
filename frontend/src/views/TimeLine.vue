<template>
  <div class="timeline-page">
    <PageHero title="千年衣脉 · 服饰演变时间轴" kicker="TIMELINE · 衣制千年" sub="从上古到清代，拖动时间轴纵览华夏衣制的千年演变脉络" seal="脉" />

    <div v-loading="loading" class="timeline-wrap anim-stagger">
      <!-- 横向时间轴 -->
      <div class="timeline-scroll" ref="scrollEl">
        <div class="timeline-track" :style="{ width: trackWidth }">
          <div class="timeline-line"></div>
          <div v-for="(s, i) in stages" :key="s.stage" class="timeline-node" :style="nodeStyle(i)">
            <div class="node-dot" @click="selectStage(i)" :class="{ active: i === selected }">
              <span>{{ s.year.split('—')[0] }}</span>
            </div>
            <div class="node-label" @click="selectStage(i)">
              <b>{{ s.dynasty }}</b>
              <p>{{ s.representative }}</p>
              <em v-if="s.keywords?.length" class="node-kw">{{ s.keywords.slice(0, 2).join(" · ") }}</em>
            </div>
          </div>
        </div>
      </div>

      <div class="timeline-controls">
        <el-button size="small" @click="scrollBy(-1)">← 早</el-button>
        <span class="ctrl-hint">拖动 / 点击节点查看详情</span>
        <el-button size="small" @click="scrollBy(1)">晚 →</el-button>
      </div>

      <!-- 朝代详情 -->
      <div v-if="currentStage" class="stage-detail ys-card">
        <div class="stage-head">
          <h3>{{ currentStage.dynasty }} <span>{{ currentStage.year }}</span></h3>
          <span class="stage-counts">
            档案 {{ currentStage.costume_count }} 件 · 文物 {{ currentStage.relic_count }} 件
          </span>
        </div>

        <!-- 时代概述 -->
        <p class="stage-events">{{ currentStage.events }}</p>
        <p v-if="currentStage.overview" class="stage-overview">{{ currentStage.overview }}</p>

        <!-- 关键词 -->
        <div v-if="currentStage.keywords?.length" class="stage-kw">
          <span v-for="k in currentStage.keywords" :key="k" class="kw-chip">{{ k }}</span>
        </div>

        <!-- 八维度详情 -->
        <div class="dim-grid">
          <div class="dim-block">
            <h4 class="dim-title">时代背景</h4>
            <p class="dim-text">{{ currentStage.era_bg }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">代表服饰及转变原因</h4>
            <div v-for="(o, i) in currentStage.sig_outfit" :key="i" class="dim-item">
              <b>{{ i + 1 }}.</b> {{ o }}
            </div>
            <p v-if="currentStage.change_reason" class="dim-reason">转变原因：{{ currentStage.change_reason }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">形制裁剪</h4>
            <p class="dim-text">{{ currentStage.cut_shape }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">纹样色彩</h4>
            <p class="dim-text">{{ currentStage.pattern_color }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">材质工艺</h4>
            <p class="dim-text">{{ currentStage.material_craft }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">礼俗象征</h4>
            <p class="dim-text">{{ currentStage.ritual_symbol }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">关键节点</h4>
            <p class="dim-text">{{ currentStage.key_milestone }}</p>
          </div>

          <div class="dim-block">
            <h4 class="dim-title">不同人群着装与意义</h4>
            <div v-for="(s, i) in currentStage.social_wear" :key="i" class="dim-item">· {{ s }}</div>
          </div>
        </div>

        <!-- 风格要点 -->
        <div v-if="currentStage.stylePoints?.length" class="style-block">
          <h4 class="ys-title">风格要点</h4>
          <ol class="style-list">
            <li v-for="(pt, i) in currentStage.stylePoints" :key="i">{{ pt }}</li>
          </ol>
        </div>

        <!-- 代表服饰 -->
        <div class="stage-costumes" v-if="detail?.costumes?.length">
          <h4 class="ys-title">代表服饰 · {{ detail.costumes.length }} 件</h4>
          <div class="costume-cards">
            <div v-for="c in detail.costumes" :key="c.id" class="costume-card" @click="$router.push(`/archive/${c.id}`)">
              <div class="cc-head">
                <b>{{ c.name }}</b>
                <span>{{ c.category }}</span>
              </div>
              <p class="cc-desc">{{ c.description || "（形制说明整理中）" }}</p>
              <div class="cc-meta" v-if="c.fabric || c.pattern || c.color">
                <span v-if="c.fabric">面料 {{ c.fabric }}</span>
                <span v-if="c.pattern">纹样 {{ c.pattern }}</span>
                <span v-if="c.color">服色 {{ c.color }}</span>
              </div>
              <div class="cc-foot">
                <span v-if="c.wearer">{{ c.wearer }}</span>
                <span v-if="c.source_type">{{ c.source_type }}</span>
                <i>查看档案 →</i>
              </div>
            </div>
          </div>
        </div>

        <!-- 出土文物 -->
        <div class="stage-relics" v-if="detail?.relics?.length">
          <h4 class="ys-title">出土文物 · {{ detail.relics.length }} 件</h4>
          <div v-for="r in detail.relics" :key="r.id" class="relic-card" @click="$router.push(`/geomap?relic=${r.id}`)">
            <div class="relic-row">
              <b>{{ r.name }}</b>
              <span>{{ r.location }} · {{ r.museum }}</span>
            </div>
            <p v-if="r.description" class="relic-desc">{{ r.description }}</p>
            <i class="relic-go">查看出土位置 →</i>
          </div>
        </div>

        <!-- 文献出处 -->
        <p v-if="currentStage.literature" class="stage-literature">
          <span class="lit-label">文献出处</span>{{ currentStage.literature }}
        </p>

        <!-- 文献参考（原文 + 百度百科链接） -->
        <div class="ref-block" v-if="currentStage.quotes?.length || currentStage.links?.length">
          <h4 class="ys-title">文献参考</h4>
          <div v-for="(q, i) in currentStage.quotes" :key="i" class="ref-quote">
            <span class="ref-src">{{ q.src }}</span>
            <p>{{ q.text }}</p>
          </div>
          <div v-if="currentStage.links?.length" class="ref-links">
            <a v-for="(l, i) in currentStage.links" :key="i" :href="l.url" target="_blank" rel="noopener noreferrer" class="ref-link">
              百度百科 · {{ l.name }} ↗
            </a>
          </div>
        </div>

        <!-- 嵌入时空推演模拟器 -->
        <div class="sim-block">
          <h4 class="ys-title">时空推演 · {{ currentStage.dynasty }}</h4>
          <SimulatorPanel :default-era="currentStage.dynasty" compact />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { fetchTimeline, fetchTimelineDetail } from "@/api/modules";
import SimulatorPanel from "@/components/SimulatorPanel.vue";
import PageHero from "@/components/PageHero.vue";

const loading = ref(false);
const stages = ref<any[]>([]);
const detail = ref<any>(null);
const selected = ref(0);
const scrollEl = ref<HTMLDivElement>();

const trackWidth = computed(() => `${stages.value.length * 220 + 80}px`);
const currentStage = computed(() => stages.value[selected.value]);

function nodeStyle(i: number) {
  return { left: `${i * 220 + 40}px` };
}

function selectStage(i: number) {
  selected.value = i;
  loadDetail();
  const el = scrollEl.value;
  if (el) el.scrollTo({ left: Math.max(0, i * 220 - 200), behavior: "smooth" });
}

function scrollBy(dir: number) {
  const el = scrollEl.value;
  if (el) el.scrollBy({ left: dir * 440, behavior: "smooth" });
}

async function loadDetail() {
  const s = currentStage.value;
  if (!s) return;
  detail.value = await fetchTimelineDetail(s.dynasty) as any;
}

onMounted(async () => {
  loading.value = true;
  try {
    const data: any = await fetchTimeline();
    stages.value = data.stages;
    selected.value = 4; // 默认隋唐
    await loadDetail();
  } finally { loading.value = false; }
});
</script>

<style scoped>
.page-sub { color: var(--ys-ink-3); margin: -6px 0 18px; }
.timeline-wrap { margin-top: 10px; }
.timeline-scroll { overflow-x: auto; padding: 10px 0 20px; }
.timeline-track { position: relative; height: 200px; }
.timeline-line { position: absolute; top: 40px; left: 20px; right: 20px; height: 3px; background: var(--ys-line); border-radius: 2px; }
.timeline-node { position: absolute; top: 0; width: 180px; cursor: pointer; }
.node-dot { width: 16px; height: 16px; border-radius: 50%; background: #fffdf8; border: 3px solid var(--ys-red); position: relative; top: 30px; }
.node-dot.active { background: var(--ys-red); box-shadow: 0 0 0 6px rgba(169, 50, 38, 0.15); }
.node-dot span { position: absolute; top: -22px; left: -8px; font-size: 12px; color: var(--ys-ink-3); white-space: nowrap; }
.node-label { margin-top: 52px; }
.node-label b { font-size: 15px; color: var(--ys-ink); }
.node-label p { margin: 2px 0 0; font-size: 12px; color: var(--ys-ink-3); }
.node-kw { display: block; margin-top: 3px; font-style: normal; font-size: 11px; color: var(--ys-red-deep); opacity: 0.75; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.timeline-controls { display: flex; align-items: center; gap: 16px; }
.ctrl-hint { flex: 1; text-align: center; color: var(--ys-ink-3); font-size: 13px; }

.stage-detail { margin-top: 16px; }
.stage-head { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; }
.stage-head h3 { margin: 0; font-size: 20px; }
.stage-head h3 span { font-size: 13px; color: var(--ys-ink-3); font-weight: 400; margin-left: 8px; }
.stage-counts { color: var(--ys-red-deep); font-size: 13px; }
.stage-events { color: var(--ys-red-deep); font-weight: 600; line-height: 1.7; margin-bottom: 4px; }
.stage-overview { color: var(--ys-ink-2); line-height: 1.9; margin: 0 0 10px; text-align: justify; }
.stage-kw { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 14px; }
.kw-chip { border: 1px solid rgba(169, 50, 38, 0.35); background: rgba(169, 50, 38, 0.05); color: var(--ys-red-deep); border-radius: 14px; padding: 3px 12px; font-size: 12px; }

/* 八维度详情 */
.dim-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 14px 0;
}
.dim-block {
  border: 1px solid var(--ys-line);
  border-radius: 10px;
  padding: 14px 16px;
  background: rgba(255, 253, 248, 0.6);
}
.dim-title {
  margin: 0 0 8px;
  font-size: 15px;
  color: var(--ys-gold);
  display: flex;
  align-items: center;
  gap: 8px;
}
.dim-title::before {
  content: "";
  width: 3px;
  height: 14px;
  background: var(--ys-gold);
  border-radius: 2px;
}
.dim-text { margin: 0; font-size: 13px; color: var(--ys-ink-2); line-height: 1.85; text-align: justify; }
.dim-item { font-size: 13px; color: var(--ys-ink-2); line-height: 1.85; text-align: justify; margin-bottom: 6px; }
.dim-item b { color: var(--ys-gold); font-weight: 600; }
.dim-reason { margin: 4px 0 0; font-size: 13px; color: var(--ys-red-deep); line-height: 1.8; text-align: justify; }

/* 文献参考 */
.ref-block { margin-top: 8px; }
.ref-quote {
  border-left: 3px solid var(--ys-gold);
  background: rgba(212, 169, 79, 0.07);
  border-radius: 0 8px 8px 0;
  padding: 8px 14px;
  margin-bottom: 8px;
}
.ref-src {
  display: inline-block;
  background: rgba(212, 169, 79, 0.16);
  color: var(--ys-gold);
  font-size: 12px;
  padding: 1px 8px;
  border-radius: 4px;
  margin-bottom: 4px;
}
.ref-quote p { margin: 0; font-size: 13px; color: var(--ys-ink-2); line-height: 1.8; }
.ref-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.ref-link {
  display: inline-block;
  border: 1px solid var(--ys-line);
  border-radius: 14px;
  padding: 3px 12px;
  font-size: 12px;
  color: var(--ys-gold);
  text-decoration: none;
  transition: all 0.2s;
}
.ref-link:hover { background: rgba(212, 169, 79, 0.14); border-color: var(--ys-gold); }

.style-block { margin-bottom: 16px; }
.style-list { margin: 8px 0 0; padding-left: 20px; color: var(--ys-ink-2); line-height: 1.9; }
.style-list li::marker { color: var(--ys-red); }

.stage-costumes { margin: 6px 0 16px; }
.costume-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-top: 8px; }
.costume-card { border: 1px solid var(--ys-line); background: #fffdf8; border-radius: 10px; padding: 12px 14px; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; display: flex; flex-direction: column; gap: 6px; }
.costume-card:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(122, 75, 42, 0.12); }
.cc-head { display: flex; align-items: baseline; gap: 8px; }
.cc-head b { font-size: 15px; color: var(--ys-ink); }
.cc-head span { font-size: 12px; color: var(--ys-ink-3); background: #f3ead8; border-radius: 4px; padding: 1px 6px; }
.cc-desc { margin: 0; font-size: 13px; color: var(--ys-ink-2); line-height: 1.7; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; flex: 1; }
.cc-meta { display: flex; flex-wrap: wrap; gap: 6px 12px; font-size: 12px; color: var(--ys-ink-3); }
.cc-foot { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--ys-ink-3); border-top: 1px dashed var(--ys-line); padding-top: 6px; }
.cc-foot i { font-style: normal; color: var(--ys-red-deep); margin-left: auto; }

.stage-relics { margin: 6px 0 16px; }
.relic-card { border-left: 3px solid var(--ys-red); background: #f6efe4; border-radius: 6px; padding: 8px 14px; margin-bottom: 8px; cursor: pointer; transition: background 0.15s; }
.relic-card:hover { background: #f4ead6; }
.relic-go { display: block; margin-top: 4px; font-style: normal; font-size: 12px; color: var(--ys-red-deep); text-align: right; }
.relic-row { display: flex; justify-content: space-between; gap: 12px; font-size: 14px; flex-wrap: wrap; }
.relic-row span { color: var(--ys-ink-3); font-size: 12px; }
.relic-desc { margin: 4px 0 0; font-size: 13px; color: var(--ys-ink-2); line-height: 1.7; }
.stage-literature { margin: 14px 0 0; font-size: 13px; color: var(--ys-ink-3); border-left: 3px solid var(--ys-line); padding-left: 10px; }
.lit-label { display: inline-block; background: var(--ys-bg-deep); color: var(--ys-red-deep); padding: 0 6px; border-radius: 4px; margin-right: 8px; font-size: 12px; }

.sim-block { margin-top: 20px; }

@media (max-width: 900px) {
  .dim-grid { grid-template-columns: 1fr; }
}
</style>
