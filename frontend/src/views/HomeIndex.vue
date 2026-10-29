<template>
  <div class="home-page">
    <!-- Hero 大横幅 -->
    <section class="hero-banner" :class="{ 'anim-ready': heroAnim }">
      <video class="hero-bg" src="/videos/hero-bg.mp4" autoplay muted loop playsinline preload="auto" poster="/images/relics/relic_geo_mashan_jinpao.jpg"></video>
      <div class="hero-mask"></div>
      <div class="hero-frame"></div>
      <span class="hero-orn orn-left">华 夏 衣 冠 · 以 物 证 史</span>
      <span class="hero-orn orn-right">垂 裳 而 治 · 以 技 传 薪</span>
      <div class="hero-content">
        <p class="hero-kicker">衣冠有史 · 华服可溯</p>
        <p class="hero-kicker-en">YISU · CHRONICLE OF CHINESE COSTUME</p>
        <RevealTitle v-if="heroAnim" text="衣冠上国 · 华夏有衣" tag="h2" cls="hero-title" :delay="0.25" :step="0.12" />
        <div class="hero-rule"></div>
        <p class="hero-foot">新石器 · 先秦 · 秦汉 · 魏晋 · 隋唐 · 宋元 · 明清 — 传世复原</p>
      </div>
      <div class="hero-scroll">⌄</div>
    </section>

    <!-- 今日焦点 -->
    <section v-if="focusNews.length" class="focus-banner">
      <div class="focus-label">今日焦点</div>
      <div class="focus-list">
        <a v-for="n in focusNews" :key="n.id" class="focus-item" @click="openNews(n.id)">
          <img v-if="n.cover_image" class="focus-img" :src="n.cover_image" :alt="n.title" loading="lazy" @error="hideImg($event)" />
          <div class="focus-text">
            <h3>{{ n.title }}</h3>
            <p>{{ n.summary }}</p>
            <span class="ys-tag" v-for="t in n.dynasty_tags" :key="t">{{ t }}</span>
            <a v-if="n.source_url" class="src-link" :href="n.source_url" target="_blank" rel="noopener" @click.stop>原文 ↗</a>
          </div>
        </a>
      </div>
    </section>

    <div class="home-layout">
      <!-- 新闻信息流 -->
      <section class="news-stream">
        <div class="section-head">
          <h2 class="ys-title">文博资讯</h2>
          <div class="filters">
            <el-select v-model="dynasty" placeholder="按朝代筛选" clearable size="small" style="width: 130px" @change="loadNews">
              <el-option v-for="d in dynastyOptions" :key="d.name" :label="d.name" :value="d.name" />
            </el-select>
            <el-select v-model="timeRange" placeholder="按时间筛选" clearable size="small" style="width: 140px" @change="loadNews">
              <el-option label="近一周" :value="7" />
              <el-option label="近一月" :value="30" />
              <el-option label="近三月" :value="90" />
              <el-option label="近半年" :value="180" />
            </el-select>
            <el-input v-model="keyword" placeholder="搜索资讯" clearable size="small" style="width: 180px" @keyup.enter="loadNews" />
            <el-button size="small" @click="loadNews">本地搜索</el-button>
            <el-button size="small" type="primary" :loading="webState === 'loading'" @click="webSearch">全网搜索</el-button>
          </div>
        </div>

        <!-- 全网搜索结果 -->
        <div v-if="webState !== 'idle'" class="web-panel ys-card">
          <div class="web-head">
            <span class="web-badge">全网</span>
            <b>“{{ webKeyword }}”</b> 共 {{ webResults.length }} 条结果
            <span class="web-note">{{ webNote }}</span>
            <el-button text size="small" @click="webState = 'idle'; webResults = []">收起</el-button>
          </div>
          <div v-if="webState === 'loading'" class="ys-empty">正在全网抓取公开资讯…</div>
          <template v-else>
            <a v-for="(r, i) in webResults" :key="i" class="web-item" :href="r.url" target="_blank" rel="noopener noreferrer">
              <b>{{ r.title }}</b>
              <span>{{ r.source }} · 阅读原文 ↗</span>
            </a>
            <div v-if="!webResults.length" class="ys-empty">全网暂无“{{ webKeyword }}”相关资讯，建议换个关键词试试</div>
          </template>
        </div>

        <div v-loading="loading" class="news-cards">
          <article v-for="n in news" :key="n.id" class="news-card ys-card" @click="openNews(n.id)">
            <img v-if="n.cover_image" class="news-cover" :src="n.cover_image" :alt="n.title" loading="lazy" @error="hideImg($event)" />
            <div class="news-body">
              <div class="news-meta">
                <span class="ai-badge">AI摘要</span>
                <span>{{ n.source }}</span>
                <span class="date">{{ n.publish_time?.slice(0, 10) }}</span>
                <a v-if="n.source_url" class="src-link" :href="n.source_url" target="_blank" rel="noopener" @click.stop>原文 ↗</a>
              </div>
              <h3 class="news-title">{{ n.title }}</h3>
              <p class="news-summary">{{ n.summary }}</p>
              <div class="news-tags">
                <span class="ys-tag" v-for="t in n.dynasty_tags" :key="t" @click.stop="jumpArchive(t)">{{ t }}</span>
                <span class="ys-tag" v-for="t in n.entity_tags" :key="t" @click.stop="jumpArchive(t)">{{ t }}</span>
              </div>
              <div class="news-qa" v-if="n.ai_questions?.length">
                <span class="qa-label">AI推荐提问：</span>
                <span v-for="q in n.ai_questions.slice(0, 2)" :key="q" class="qa-item" @click.stop="askAI(q)">{{ q }}</span>
              </div>
            </div>
          </article>

          <div v-if="!loading && !news.length" class="ys-empty">暂无资讯，点击右侧「录入资讯」体验 AI 解析流水线</div>
        </div>

        <el-pagination
          v-if="total > pageSize"
          background layout="prev, pager, next" :total="total" :page-size="pageSize"
          :current-page="page" @current-change="(p: number) => { page = p; loadNews(); }"
        />
      </section>

      <!-- 侧边栏 -->
      <aside class="home-side">
        <div class="ys-card">
          <h3 class="ys-title">热门朝代</h3>
          <div class="tag-cloud">
            <span v-for="t in hotTags" :key="t.name" class="cloud-tag"
                  :style="{ fontSize: 12 + Math.min(10, t.count * 3) + 'px' }"
                  @click="selectDynasty(t.name)">{{ t.name }}<i>{{ t.count }}</i></span>
          </div>
        </div>

        <div class="ys-card">
          <h3 class="ys-title">关键词趋势</h3>
          <div ref="trendEl" style="height: 180px"></div>
        </div>

        <div class="ys-card">
          <h3 class="ys-title">推荐档案</h3>
          <div class="link-list">
            <a v-for="c in links" :key="c.id" class="link-item" @click="$router.push(`/archive/${c.id}`)">
              <b>{{ c.name }}</b><span>{{ c.dynasty }} · {{ c.category }}</span>
            </a>
          </div>
        </div>

        <div class="ys-card">
          <h3 class="ys-title">AI 资讯解析演示</h3>
          <el-input v-model="manualTitle" placeholder="资讯标题" size="small" />
          <el-input v-model="manualContent" type="textarea" :rows="4" placeholder="资讯正文" size="small" style="margin: 8px 0" />
          <el-button type="primary" size="small" @click="manualParse">解析并生成摘要</el-button>
          <div v-if="parseResult" class="parse-result">
            <p class="ai-badge">AI摘要</p>
            <p>{{ parseResult.summary }}</p>
            <div class="news-tags">
              <span class="ys-tag" v-for="t in parseResult.entity_tags.split(',')" :key="t" v-show="t">{{ t }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import { ElMessage } from "element-plus";
import * as echarts from "echarts";
import { useRouter } from "vue-router";
import { fetchNews, fetchHotTags, fetchTrendKeywords, fetchCostumeLinks, fetchWebSearch } from "@/api/modules";
import RevealTitle from "@/components/RevealTitle.vue";
import request from "@/api/request";

const router = useRouter();
const heroAnim = ref(false);
const news = ref<any[]>([]);
const focusNews = ref<any[]>([]);
const hotTags = ref<any[]>([]);
const links = ref<any[]>([]);
const dynastyOptions = ref([{ name: "秦汉" }, { name: "隋唐" }, { name: "宋" }, { name: "明" }, { name: "清" }]);
const dynasty = ref("");
const keyword = ref("");
const timeRange = ref<number | undefined>(undefined);
const loading = ref(false);
const page = ref(1);
const pageSize = 8;
const total = ref(0);
const trendEl = ref<HTMLDivElement>();
let trendChart: echarts.ECharts | null = null;
const manualTitle = ref("");
const manualContent = ref("");
const parseResult = ref<any>(null);
const webState = ref<"idle" | "loading" | "done">("idle");
const webKeyword = ref("");
const webResults = ref<any[]>([]);
const webNote = ref("");
const heroImgFail = ref(false);

async function webSearch() {
  if (!keyword.value.trim()) return ElMessage.warning("请输入搜索关键词");
  webState.value = "loading";
  webKeyword.value = keyword.value.trim();
  webResults.value = [];
  try {
    const data: any = await fetchWebSearch({ keyword: webKeyword.value, limit: 8 });
    webResults.value = data.items || [];
    webNote.value = data.note || "";
  } catch {
    webNote.value = "全网搜索暂时不可用（网络受限）";
  } finally {
    webState.value = "done";
  }
}

async function loadNews() {
  loading.value = true;
  try {
    const data: any = await fetchNews({ page: page.value, page_size: pageSize, dynasty: dynasty.value, keyword: keyword.value, days: timeRange.value });
    news.value = data.items;
    total.value = data.total;
    focusNews.value = data.focus || data.items.filter((n: any) => n.is_focus);
  } finally {
    loading.value = false;
  }
}

async function loadSide() {
  hotTags.value = (await fetchHotTags() as any).tags || [];
  links.value = (await fetchCostumeLinks() as any).items || [];
  const kd = await fetchTrendKeywords() as any;  await nextTick();
  if (trendEl.value) {
    trendChart?.dispose();
    trendChart = echarts.init(trendEl.value);
    trendChart.setOption({
      grid: { left: 30, right: 8, top: 10, bottom: 24 },
      xAxis: { type: "category", data: kd.data.map((x: any) => x.name), axisLabel: { fontSize: 11 } },
      yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: "#eee5d2" } } },
      series: [{ type: "bar", data: kd.data.map((x: any) => x.value),
        itemStyle: { color: "#b98a2f", borderRadius: [4, 4, 0, 0] } }],
      tooltip: { trigger: "axis" },
    });
  }
}

async function manualParse() {
  if (!manualTitle.value) return ElMessage.warning("请输入标题");
  const form = new URLSearchParams();
  form.append("title", manualTitle.value);
  form.append("content", manualContent.value);
  parseResult.value = await request.post("/home/news/parse", form, { headers: { "Content-Type": "application/x-www-form-urlencoded" } });
}

function openNews(id: number) {
  router.push(`/news/${id}`);
}

function jumpArchive(tag: string) {
  router.push(`/archive?keyword=${encodeURIComponent(tag)}`);
}

function selectDynasty(name: string) {
  dynasty.value = name;
  loadNews();
}

function askAI(q: string) {
  ElMessage.info(`推荐提问：${q}`);
  router.push("/aiqa");
}

function hideImg(e: Event) {
  (e.target as HTMLImageElement).style.display = "none";
}

onMounted(() => {
  loadNews();
  loadSide();
  // 开场动画结束后再播 Hero 入场动效；SPA 直接进入时稍作延迟直接播放
  const start = () => { heroAnim.value = true; };
  if ((window as any).__preloaderActive) {
    document.addEventListener("preloader-done", start, { once: true });
    window.setTimeout(start, 3000); // 兜底：事件丢失时 3s 后强制播放
  } else {
    window.setTimeout(start, 200);
  }
});
onBeforeUnmount(() => trendChart?.dispose());
</script>

<style scoped>
/* Hero 大横幅 */
.hero-banner {
  position: relative;
  height: 100vh;
  width: 100vw;
  margin-left: calc(50% - 50vw);
  border-radius: 0;
  overflow: hidden;
  margin-top: -24px;
  margin-bottom: 32px;
  border: none;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.4);
}
.hero-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.02);
}
.hero-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(12, 7, 3, 0.74) 0%, rgba(18, 12, 6, 0.28) 48%, rgba(30, 22, 14, 0.9) 100%);
}
/* 内嵌金框（参赛级门面细节） */
.hero-frame {
  position: absolute;
  inset: 10px;
  z-index: 3;
  pointer-events: none;
  border: 1px solid rgba(201, 162, 39, 0.5);
  border-radius: 10px;
}
.hero-frame::before,
.hero-frame::after {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(233, 200, 106, 0.85);
}
.hero-frame::before { top: -1px; left: -1px; border-right: none; border-bottom: none; border-top-left-radius: 10px; }
.hero-frame::after { bottom: -1px; right: -1px; border-left: none; border-top: none; border-bottom-right-radius: 10px; }
/* 左右竖排装饰字 */
.hero-orn {
  position: absolute;
  z-index: 3;
  writing-mode: vertical-rl;
  letter-spacing: 10px;
  font-size: 12px;
  color: rgba(246, 231, 191, 0.62);
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.6);
  pointer-events: none;
  user-select: none;
}
.orn-left { left: 30px; top: 50%; transform: translateY(-50%); }
.orn-right { right: 30px; top: 50%; transform: translateY(-50%); }
/* 开场金色扫光（等待开场动画结束后播放） */
.hero-banner::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background: linear-gradient(105deg, transparent 40%, rgba(255, 224, 150, 0.26) 50%, transparent 60%);
  transform: translateX(-100%);
  opacity: 0;
}
.hero-banner.anim-ready::after {
  opacity: 1;
  animation: heroSheen 1.5s ease-out 1.3s forwards;
}
@keyframes heroSheen {
  to { transform: translateX(100%); }
}
.hero-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 24px;
}
.hero-kicker {
  margin: 0 0 10px;
  color: var(--ys-gold);
  font-size: 14px;
  letter-spacing: 6px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.5);
  display: inline-flex;
  align-items: center;
  gap: 12px;
}
.hero-kicker-en {
  margin: 0 0 16px;
  color: rgba(201, 162, 39, 0.9);
  font-size: 12px;
  letter-spacing: 4px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.5);
}
.hero-kicker::before,
.hero-kicker::after {
  content: "";
  width: 36px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(201, 162, 39, 0.85));
}
.hero-kicker::after { background: linear-gradient(270deg, transparent, rgba(201, 162, 39, 0.85)); }
.hero-sub {
  margin: 0;
  color: rgba(247, 236, 216, 0.92);
  font-size: 16px;
  letter-spacing: 4px;
  text-shadow: 0 1px 10px rgba(0, 0, 0, 0.55);
}
/* 副标题下的金色分隔 + 朝代时间链 */
.hero-rule {
  width: 220px;
  height: 1px;
  margin: 16px 0 10px;
  background: linear-gradient(90deg, transparent, rgba(201, 162, 39, 0.8), transparent);
}
.hero-foot {
  margin: 0;
  color: rgba(245, 239, 228, 0.68);
  font-size: 12px;
  letter-spacing: 3px;
}
/* 底部滚动提示（静态，克制） */
.hero-scroll {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  z-index: 3;
  font-size: 16px;
  color: rgba(246, 231, 191, 0.7);
  pointer-events: none;
}
/* Hero 入场：kicker → 标题逐字 → 副标题，错峰渐显 */
.hero-title {
  margin: 0 0 12px;
  color: #f6e7bf;
  font-size: 52px;
  letter-spacing: 16px;
  font-weight: 700;
  text-shadow:
    0 1px 0 rgba(122, 34, 28, 0.85),
    0 3px 0 rgba(90, 24, 18, 0.5),
    0 7px 20px rgba(0, 0, 0, 0.65);
}
.hero-kicker, .hero-sub { opacity: 0; }
.hero-banner.anim-ready .hero-kicker { animation: heroUp 0.7s cubic-bezier(0.22, 0.9, 0.3, 1.2) 0.05s forwards; }
.hero-banner.anim-ready .hero-sub { animation: heroUp 0.7s cubic-bezier(0.22, 0.9, 0.3, 1.2) 0.85s forwards; }
@keyframes heroUp {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: none; }
}

/* 档案精粹 · 卡片墙 */
.feat-head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.gold-line { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(212, 169, 79, 0.5), transparent); }
.feat-title { margin: 0; }
/* 首页标题自带两侧 gold-line，关闭 ys-title 内部延伸线 */
.feat-title::after { display: none; }
.feat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
/* 纹样精粹 6 卡：3 列 × 2 排对齐 */
.feat-grid-3 {
  grid-template-columns: repeat(3, 1fr);
}
.feat-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--ys-card);
  border: 1px solid var(--ys-line);
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  color: var(--ys-ink);
}
.feat-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(90, 60, 30, 0.2); }
.feat-thumb {
  height: 128px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(150deg, #f7f0e2, #efe6d6);
}
.feat-thumb img { width: 100%; height: 100%; object-fit: contain; transition: transform 0.4s ease; }
.feat-card:hover .feat-thumb img { transform: scale(1.05); }
.feat-seal {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  background: var(--ys-red);
  color: #ffe9d0;
  font-size: 26px;
  font-weight: 700;
  border-radius: 6px;
  box-shadow: inset 0 0 0 2px rgba(255, 228, 190, 0.35);
}
.feat-card b { font-size: 16px; letter-spacing: 1px; }
.feat-meta { color: var(--ys-ink-3); font-size: 12px; letter-spacing: 1px; }

/* 精粹区与 Hero 间距节奏 */
.feature-sec { margin-bottom: 32px; }

.focus-banner {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding: 18px 22px;
  background: linear-gradient(135deg, #7e2418, #a93226);
  border-radius: 12px;
  color: #fff;
}
.focus-label {
  writing-mode: vertical-rl;
  letter-spacing: 4px;
  font-weight: 700;
  font-size: 16px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 4px;
  padding: 6px 4px;
}
.focus-list { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.focus-item { cursor: pointer; padding: 8px 12px; background: rgba(255,255,255,0.08); border-radius: 8px; display: flex; gap: 12px; align-items: center; }
.focus-img { width: 108px; height: 70px; object-fit: cover; border-radius: 6px; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.25); }
.focus-text { flex: 1; min-width: 0; }
.focus-item h3 { margin: 0; font-size: 15px; }
.focus-item p { margin: 4px 0 6px; font-size: 13px; opacity: 0.9; }
.focus-item .ys-tag { color: #fff; background: rgba(255,255,255,0.18); border-color: transparent; }

.home-layout { display: grid; grid-template-columns: 1fr 330px; gap: 20px; }
.news-stream { min-width: 0; }
.section-head { display: flex; justify-content: space-between; align-items: center; }
.filters { display: flex; gap: 8px; align-items: center; }
.web-panel { margin-bottom: 14px; padding: 14px 16px; }
.web-head { display: flex; align-items: center; gap: 8px; font-size: 13px; flex-wrap: wrap; }
.web-badge { background: var(--ys-red); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.web-note { color: var(--ys-ink-3); font-size: 12px; flex: 1; }
.web-item { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 8px 4px; border-bottom: 1px dashed var(--ys-line); font-size: 14px; color: var(--ys-ink-1); }
.web-item:hover { color: var(--ys-red-deep); }
.web-item span { color: var(--ys-ink-3); font-size: 12px; flex-shrink: 0; }
.news-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; align-items: stretch; }
.news-card { cursor: pointer; transition: transform 0.22s ease, box-shadow 0.22s ease; overflow: hidden; }
.news-card:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(90, 60, 30, 0.18); }
.news-cover { width: 100%; height: 130px; object-fit: cover; display: block; }
.news-body { padding: 0 16px 14px; }
.news-meta { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--ys-ink-3); }
.src-link { color: var(--ys-red-deep); text-decoration: none; font-size: 12px; white-space: nowrap; }
.src-link:hover { text-decoration: underline; }
.ai-badge { background: var(--ys-red); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.news-title { margin: 8px 0 6px; font-size: 17px; }
.news-summary { margin: 0 0 8px; color: var(--ys-ink-2); font-size: 14px; line-height: 1.7; }
.news-qa { font-size: 13px; color: var(--ys-ink-3); }
.qa-item { color: var(--ys-red-deep); cursor: pointer; margin-right: 10px; text-decoration: underline dotted; }

.home-side { display: flex; flex-direction: column; gap: 16px; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.cloud-tag { cursor: pointer; color: var(--ys-red-deep); border: 1px solid var(--ys-line); padding: 2px 8px; border-radius: 14px; background: #fffdf8; }
.cloud-tag i { font-style: normal; color: var(--ys-ink-3); margin-left: 2px; font-size: 11px; }
.link-list { display: flex; flex-direction: column; }
.link-item { display: flex; justify-content: space-between; padding: 8px 4px; cursor: pointer; border-bottom: 1px dashed var(--ys-line); font-size: 14px; }
.link-item span { color: var(--ys-ink-3); font-size: 12px; }
.parse-result { margin-top: 10px; font-size: 13px; color: var(--ys-ink-2); }

@media (max-width: 1200px) {
  .news-cards { grid-template-columns: 1fr; }
  .feat-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 900px) {
  .home-layout { grid-template-columns: 1fr; }
  .focus-banner { flex-direction: column; }
  .hero-banner { height: 100vh; margin: -24px -16px 32px; }
  .hero-title { font-size: 34px; letter-spacing: 8px; }
  .hero-orn { display: none; }
}
@media (max-width: 560px) {
  .feat-grid { grid-template-columns: 1fr; }
}
</style>
