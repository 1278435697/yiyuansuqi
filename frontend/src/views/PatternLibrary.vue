<template>
  <div class="pattern-page">
    <!-- ==================== 列表模式 ==================== -->
    <template v-if="!route.params.id">
      <PageHero title="衣溯AI · 传统服饰纹样库" kicker="PATTERN · 纹以载道"
                sub="十大类 321 条纹样——从云雷回旋到缠枝卷草，读懂织物之上的华夏语言" seal="纹" />

      <!-- 筛选栏 -->
      <div class="filter-bar anim-rise" style="animation-delay: .5s">
        <div class="filter-left">
          <el-radio-group v-model="category" @change="load">
            <el-radio-button value="">全部 {{ total }}</el-radio-button>
            <el-radio-button v-for="c in categories" :key="c.name" :value="c.name">{{ c.name }} {{ c.count }}</el-radio-button>
          </el-radio-group>
        </div>
        <div class="filter-right">
          <el-input v-model="keyword" placeholder="搜索纹样（如：云纹、龙纹、缠枝）" clearable size="small"
                    style="width: 210px" @keyup.enter="load" @clear="load" />
          <el-button size="small" type="primary" plain @click="load">搜索</el-button>
          <span class="count-tip">共 {{ total }} 条纹样</span>
        </div>
      </div>

      <!-- 纹样卡片网格：有图显图，无图纯文字卡（不留图片区） -->
      <div v-loading="loading" class="pattern-grid">
        <div v-for="p in items" :key="p.id" class="pattern-card" @click="$router.push(`/pattern/${p.id}`)">
          <img v-if="p.image_url" :src="p.image_url" :alt="p.name" class="p-img" loading="lazy" @error="onImgError" />
          <div v-else class="p-seal">{{ p.name.slice(0, 1) }}</div>
          <div class="p-body">
            <div class="p-head">
              <h3>{{ p.name }}</h3>
              <span class="p-cat">{{ p.category }}</span>
            </div>
            <p v-if="p.dynasty" class="p-dynasty">{{ p.dynasty }}</p>
            <p class="p-meaning">{{ p.meaning }}</p>
          </div>
        </div>
        <el-empty v-if="!loading && !items.length" :description="keyword ? `未找到「${keyword}」相关纹样` : '暂无纹样'" :image-size="80" />
      </div>
    </template>

    <!-- ==================== 详情模式（内容排版与资料库参考文件一致） ==================== -->
    <template v-else>
      <div class="detail-layout">
        <section class="ys-card detail-main">
          <div class="detail-head">
            <el-button size="small" @click="$router.push('/pattern')">返回列表</el-button>
          </div>

          <!-- 标题行：名称 + 类别·编号 -->
          <div class="p-modal-title-row">
            <h2>{{ detail?.name }}</h2>
            <span class="sub">{{ detail?.category }}<template v-if="detail?.code"> · 编号{{ detail.code }}</template></span>
          </div>
          <!-- 标签行 -->
          <div class="tag-row">
            <span>{{ detail?.category || "待考" }}</span>
            <span>传统服饰纹样</span>
          </div>

          <!-- 实物文物图：主图大图 + 张数徽标，点击灯箱轮播 -->
          <div class="img-row">
            <div v-if="firstImg" class="img-col" @click="openLightbox()">
              <img :src="firstImg" :alt="detail?.name" @error="onImgError" />
              <div v-if="detail?.images?.length > 1" class="count-badge">{{ detail.images.length }}张</div>
              <div class="label">实物文物图</div>
            </div>
          </div>

          <!-- 简介 -->
          <div class="section">
            <h3>简介</h3>
            <p>{{ detail?.meaning || "待补充" }}</p>
          </div>

          <!-- 朝代脉络 -->
          <div v-if="detail?.dynasties?.length" class="section">
            <h3>朝代脉络</h3>
            <div v-for="(e, i) in detail.dynasties" :key="i" class="era-item">
              <div class="era-period">{{ e.period }}</div>
              <div class="era-desc">{{ e.desc }}</div>
            </div>
          </div>

          <!-- 寓意 -->
          <div v-if="detail?.meanings?.length" class="section">
            <h3>寓意</h3>
            <div v-for="(m, i) in detail.meanings" :key="i" class="meaning-item">{{ m }}</div>
          </div>

          <!-- 属性 -->
          <div v-if="propsList.length" class="section">
            <h3>属性</h3>
            <div class="attr-grid">
              <div class="attr-card">
                <div class="attr-label">常用颜色</div>
                <div class="attr-value">{{ props.常用颜色 || "待补充" }}</div>
              </div>
              <div class="attr-card">
                <div class="attr-label">常用布料</div>
                <div class="attr-value">{{ props.常用布料 || "待补充" }}</div>
              </div>
              <div class="attr-card">
                <div class="attr-label">适用衣物</div>
                <div class="attr-value">{{ props.适用衣物 || "待补充" }}</div>
              </div>
              <div class="attr-card">
                <div class="attr-label">应用部位</div>
                <div class="attr-value">{{ props.应用部位 || "待补充" }}</div>
              </div>
            </div>
            <p class="attr-scene">使用场景：{{ props.使用场景 || props.使用场合 || "待补充" }}</p>
          </div>

          <!-- 常见搭配纹样 -->
          <div v-if="detail?.pairs?.length" class="section">
            <h3>常见搭配纹样</h3>
            <div class="partner-grid">
              <div v-for="(pn, i) in detail.pairs" :key="i" class="partner-card" @click="jumpPair(pn)">
                <div class="imgs">
                  <img v-if="pairImgs[pn]" :src="pairImgs[pn]" :alt="pn" @error="onImgError" />
                  <div v-else class="placeholder">实物图</div>
                </div>
                <div class="name">{{ pn }}</div>
                <div class="label">实物特写</div>
              </div>
            </div>
          </div>

          <!-- 知识图谱关联 -->
          <h3 class="ys-title" style="margin-top: 22px">知识图谱关联</h3>
          <div class="graph-nodes">
            <span class="graph-node"><i>类别</i>{{ detail?.category }}</span>
            <span class="graph-node"><i>盛行朝代</i>{{ detail?.dynasty || "待考" }}</span>
            <span class="graph-node"><i>文物图</i>{{ detail?.images?.length || 0 }} 幅</span>
            <span class="graph-node"><i>常见搭配</i>{{ detail?.pairs?.length || 0 }} 种</span>
            <span class="graph-node"><i>名录编号</i>{{ detail?.code || "待考" }}</span>
          </div>
        </section>

        <aside class="detail-side">
          <div class="ys-card chat-card">
            <h3 class="ys-title">名录信息</h3>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="类别">{{ detail?.category || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="盛行朝代">{{ detail?.dynasty || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="名录编号">{{ detail?.code || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="服饰应用部位">{{ detail?.applied || "待考" }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div v-if="detail?.similar" class="ys-card chat-card" style="margin-top: 14px">
            <h3 class="ys-title">相似纹样辨识</h3>
            <p class="body-text">{{ detail.similar }}</p>
          </div>
        </aside>
      </div>

      <el-image-viewer v-if="relicLightbox" :url-list="lightboxList" @close="relicLightbox = false" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import PageHero from "@/components/PageHero.vue";
import { fetchPatternCategories, fetchPatternItems, fetchPatternDetail } from "@/api/modules";

const route = useRoute();
const router = useRouter();

const categories = ref<{ name: string; count: number }[]>([]);
const category = ref("");
const keyword = ref("");
const items = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);

const detail = ref<any>(null);
const relicLightbox = ref(false);
const lightboxList = ref<string[]>([]);
const pairImgs = ref<Record<string, string>>({});
let pairIdMap: Record<string, number> = {};

async function load() {
  loading.value = true;
  try {
    const r: any = await fetchPatternItems({ category: category.value || undefined, q: keyword.value || undefined });
    items.value = r.items || [];
    total.value = r.total || 0;
  } catch (e) {
    ElMessage.error("纹样数据加载失败");
  } finally {
    loading.value = false;
  }
}

async function loadCategories() {
  try {
    const r: any = await fetchPatternCategories();
    categories.value = r.categories || [];
    if (!total.value) total.value = r.total || 0;
  } catch (e) {
    /* 忽略分类失败 */
  }
}

async function loadDetail(id: number) {
  detail.value = null;
  pairImgs.value = {};
  try {
    const r: any = await fetchPatternDetail(id);
    detail.value = r || null;
    // 为常见搭配建立 名称→id/封面图 映射（拉全量列表一次）
    try {
      const all: any = await fetchPatternItems({});
      const map: Record<string, { id: number; image_url: string }> = {};
      (all.items || []).forEach((it: any) => { if (it.name) map[it.name] = { id: it.id, image_url: it.image_url }; });
      pairIdMap = Object.fromEntries(Object.entries(map).map(([k, v]) => [k, v.id]));
      const pairs = (r?.pairs || []);
      const imgs: Record<string, string> = {};
      pairs.forEach((n: string) => { if (map[n]?.image_url) imgs[n] = map[n].image_url; });
      pairImgs.value = imgs;
    } catch (e) { /* 搭配图加载失败不阻塞 */ }
  } catch (e) {
    ElMessage.error("详情加载失败");
  }
}

const firstImg = computed(() => detail.value?.images?.[0]?.url || "");

/* 打开灯箱：全部实物文物图轮播 */
function openLightbox() {
  const urls = (detail.value?.images || []).map((i: any) => i.url).filter(Boolean);
  if (!urls.length) return;
  lightboxList.value = urls;
  relicLightbox.value = true;
}

/* 点击常见搭配 → 打开该纹样的整页详情（与参考文件一致：点击即进入该纹样） */
function jumpPair(name: string) {
  const id = pairIdMap[name];
  if (id) router.push(`/pattern/${id}`);
  else router.push({ path: "/pattern", query: { q: name } });
}

const props = computed(() => detail.value?.props || {});
const propsList = computed(() => {
  const p = props.value;
  return ["常用颜色", "常用布料", "适用衣物", "应用部位"].filter((k) => p[k]).map((k) => ({ k, v: p[k] }));
});

function onImgError(e: Event) {
  (e.target as HTMLImageElement).style.display = "none";
}

/* 详情/搜索路由变化时加载 */
watch(
  () => [route.params.id, route.query.q],
  ([id, q]) => {
    if (id) {
      loadDetail(Number(id));
    } else {
      detail.value = null;
      if (q) keyword.value = q as string;
      load();
    }
  },
  { immediate: true }
);

onMounted(() => {
  loadCategories();
});
</script>

<style scoped>
.pattern-page { max-width: 1280px; margin: 0 auto; padding: 24px 20px 60px; }
.filter-bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.count-tip { color: var(--ys-ink-soft, #8a7a63); font-size: 13px; }

/* 卡片网格 */
.pattern-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 18px; min-height: 200px; }
.pattern-card { background: var(--ys-card, #fffdf8); border: 1px solid var(--ys-line, #e6ddcc); border-radius: 12px; overflow: hidden; cursor: pointer; transition: transform .25s ease, box-shadow .25s ease; }
.pattern-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(92, 61, 46, .12); }
.p-img { width: 100%; height: 150px; object-fit: cover; display: block; background: #f0e9dc; }
.p-seal { width: 100%; height: 150px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #3a2a1a, #5c3d2e); color: #f5e6c8; font-size: 56px; font-family: "Kaiti", "STKaiti", serif; }
.p-body { padding: 12px 14px 14px; }
.p-head { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
.p-head h3 { font-size: 17px; color: var(--ys-ink, #2c2418); margin: 0; }
.p-cat { font-size: 11px; color: #8b5e3c; background: #f3ead8; padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
.p-dynasty { font-size: 12px; color: #a08a6a; margin: 4px 0 6px; }
.p-meaning { font-size: 13px; color: #6b5a3e; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin: 0; }

/* ===== 详情模式（排版与资料库参考文件一致） ===== */
.detail-layout { display: grid; grid-template-columns: 1fr 340px; gap: 20px; }
.detail-main { min-width: 0; }
.detail-head { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.body-text { color: var(--ys-ink-2); line-height: 1.8; }
.graph-nodes { display: flex; flex-wrap: wrap; gap: 8px; }
.graph-node { border: 1px solid var(--ys-line); background: #fffdf8; border-radius: 6px; padding: 4px 10px; font-size: 13px; }
.graph-node i { font-style: normal; color: var(--ys-red-deep); margin-right: 4px; }
.chat-card { padding: 16px; }
.detail-side { display: flex; flex-direction: column; gap: 0; }

/* 标题行 / 标签行（参考文件） */
.p-modal-title-row { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin: 14px 0 8px; }
.p-modal-title-row h2 { margin: 0; font-size: 24px; color: var(--ys-ink, #2c2418); }
.p-modal-title-row .sub { font-size: 13px; color: #8b5e3c; }
.tag-row { display: flex; gap: 8px; margin-bottom: 14px; }
.tag-row span { font-size: 11px; padding: 2px 8px; border-radius: 4px; background: #f0e8d8; color: #8b5e3c; }

/* 实物文物图（参考文件） */
.img-row { margin-bottom: 6px; }
.img-col { width: 100%; height: 260px; border-radius: 8px; background: #faf6ee; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 12px; color: #8b5e3c; border: 1px solid #e8dcc8; cursor: zoom-in; position: relative; overflow: hidden; }
.img-col img { width: 100%; height: 100%; object-fit: cover; border-radius: 8px; }
.img-col .count-badge { position: absolute; bottom: 24px; right: 6px; background: rgba(0,0,0,.6); color: #fff; font-size: 10px; padding: 1px 5px; border-radius: 8px; }
.img-col .label { position: absolute; bottom: 4px; left: 0; right: 0; text-align: center; font-size: 11px; color: rgba(139,94,60,.85); background: rgba(255,255,255,.75); padding: 2px 0; }

/* 区块（参考文件） */
.section { margin-top: 16px; }
.section h3 { font-size: 14px; color: #8b5e3c; margin: 0 0 8px; font-weight: 600; }
.section p { font-size: 13px; color: #444; line-height: 1.8; margin: 0; }
.era-item { display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px dashed #e8dcc8; }
.era-period { min-width: 90px; font-weight: 600; color: #8b5e3c; font-size: 12.5px; }
.era-desc { font-size: 12.5px; color: #555; }
.meaning-item { font-size: 13px; color: #444; padding: 4px 0 4px 16px; position: relative; }
.meaning-item::before { content: "•"; color: #8b5e3c; position: absolute; left: 4px; }
.attr-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
.attr-card { background: #faf6ee; border-radius: 8px; padding: 12px; }
.attr-label { font-size: 12px; color: #999; margin-bottom: 4px; }
.attr-value { font-size: 13px; color: #333; line-height: 1.6; }
.attr-scene { font-size: 12px; color: #888; margin-top: 8px !important; }
.partner-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-top: 10px; }
.partner-card { background: #faf6ee; border-radius: 8px; padding: 10px; cursor: pointer; text-align: center; transition: transform .2s; border: 1px solid transparent; }
.partner-card:hover { transform: translateY(-2px); border-color: #e8dcc8; }
.partner-card .imgs { display: flex; gap: 4px; margin-bottom: 6px; }
.partner-card .imgs img { flex: 1; height: 60px; object-fit: cover; border-radius: 4px; }
.partner-card .imgs .placeholder { flex: 1; height: 60px; display: flex; align-items: center; justify-content: center; background: #f0e8d8; border-radius: 4px; font-size: 10px; color: #8b5e3c; }
.partner-card .name { font-size: 12px; color: #444; font-weight: 500; }
.partner-card .label { font-size: 10px; color: #999; margin-top: 2px; }
@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
}
</style>
