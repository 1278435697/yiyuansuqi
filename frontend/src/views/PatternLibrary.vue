<template>
  <div class="pattern-page acc-scope">
    <!-- ==================== 列表模式 ==================== -->
    <template v-if="!route.params.id">
      <PageHero grand
        title="纹样"
        eyebrow-en="PATTERN · 纹以载道"
        eyebrow-index="VOL. 纹·十类"
        kicker="纹以载道"
        sub="十大类 321 条纹样——从云雷回旋到缠枝卷草，读懂织物之上的华夏语言。"
        seal="纹"
        vertical="云雷 · 龙凤 · 缠枝 · 卷草 · 八宝 · 吉祥"
        primary-label="浏览本卷" primary-href="#catalog"
        secondary-label="看出土地图" secondary-href="/geomap"
        :stats="[
          { n: '10', l: '纹样大类' },
          { n: '321', l: '全量纹样' },
          { n: '16', l: '本期精选' },
          { n: '08', l: '阅读板块' },
        ]" />

      <!-- 工具条：区块标题在左、搜索与创建在右（控件不变，只换皮） -->
      <div class="acc-toolbar anim-rise" style="animation-delay: .5s">
        <AccSectionHead no="纹" kicker="纹样名录 · 十类" title="纹样目录" :sub="`共 ${total} 条`" />
        <div class="acc-toolbar-tools">
          <el-input v-model="keyword" placeholder="搜索纹样（如：云纹、龙纹、缠枝）" clearable size="small"
                    style="width: 210px" @keyup.enter="load" @clear="load" />
          <el-button size="small" type="primary" plain @click="load">搜索</el-button>
          <el-button size="small" type="danger" plain @click="openCreate">＋ 创建纹样</el-button>
        </div>
      </div>

      <!-- 大类筛选条 -->
      <div class="acc-filter-row anim-rise" style="animation-delay: .56s">
        <el-radio-group v-model="category" @change="load">
          <el-radio-button value="">全部 {{ total }}</el-radio-button>
          <el-radio-button v-for="c in categories" :key="c.name" :value="c.name">{{ c.name }} {{ c.count }}</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 用户作品：用户添加的纹样 -->
      <div class="user-works acc-aside-card anim-rise" style="animation-delay: .62s">
        <div class="uw-head">
          <AccSectionHead title="用户作品 · 纹样" size="sm" />
          <div class="uw-tools">
            <el-input v-model="uwKeyword" placeholder="搜索用户纹样…" size="small" clearable style="width: 180px"
                      @keyup.enter="loadUserWorks" @clear="loadUserWorks" />
            <el-button size="small" @click="loadUserWorks">搜索</el-button>
          </div>
        </div>
        <div class="uw-grid">
          <div v-for="p in userWorks" :key="p.id" class="uw-card" role="link" tabindex="0"
               @click="$router.push(`/pattern/${p.id}`)" @keydown.enter="$router.push(`/pattern/${p.id}`)">
            <img v-if="p.image_url" :src="p.image_url" :alt="p.name" loading="lazy" @error="onImgError" />
            <div v-else class="uw-thumb">暂无实物图</div>
            <div class="uw-info">
              <h4><span v-if="p.code" class="p-code">#{{ p.code }}</span>{{ p.name }}</h4>
              <p>{{ p.dynasty || "朝代待考" }} · {{ p.category }}</p>
              <p class="uw-desc">{{ p.meaning }}</p>
            </div>
          </div>
          <div v-if="!userWorks.length" class="ys-empty uw-empty-box">{{ uwKeyword ? "未找到匹配的用户纹样" : "暂无用户创建的纹样，点击右上角「＋ 创建纹样」创建第一条吧" }}</div>
        </div>
      </div>

      <!-- 纹样卡片网格：衣冠卡片解剖，图片区定高 + contain 不裁原图 -->
      <div v-loading="loading" class="acc-grid anim-rise" style="animation-delay: .68s">
        <AccCard v-for="(p, i) in items" :key="p.id" :index="i"
                 :to="`/pattern/${p.id}`" :title="p.name" :image="p.image_url" :alt="p.name"
                 :meta="p.dynasty || '朝代待考'" :summary="p.meaning"
                 :no="`${pad(i + 1)} / ${total}`" :volume="p.category"
                 :code="p.code ? `#${p.code}` : ''" :badge="p.created_by ? '用户添加' : ''"
                 :tone="toneOf(p.category)" link-text="阅纹样" />
        <el-empty v-if="!loading && !items.length" :description="keyword ? `未找到「${keyword}」相关纹样` : '暂无纹样'" :image-size="80" />
      </div>

      <!-- 创建纹样弹窗（信息收集与详情页正文区块一致：简介 → 朝代脉络 → 寓意 → 属性 → 常见搭配） -->
      <el-dialog v-model="createVisible" title="创建纹样" width="560px" :close-on-click-modal="false">
        <el-form label-width="96px" label-position="left">
          <el-form-item label="纹样名称" required>
            <el-input v-model="createForm.name" placeholder="如：联珠纹、宝相花" maxlength="60" />
          </el-form-item>
          <el-form-item label="类别">
            <el-select v-model="createForm.category" placeholder="选择大类（可选）" clearable style="width: 100%">
              <el-option v-for="c in categories" :key="c.name" :label="`${c.name}（${c.count}）`" :value="c.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="createForm.meaning" type="textarea" :rows="3"
                      placeholder="纹样总体介绍：起源、演变、工艺与典型实物，如：以婴戏图绘画为蓝本转化而成的装饰纹样……" />
          </el-form-item>
          <el-form-item label="朝代脉络">
            <el-input v-model="createForm.dynastiesText" type="textarea" :rows="4"
                      placeholder="每行一个朝代，格式：朝代|说明&#10;如：唐宋|唐代彩绘花毡已见孩童花间玩耍图景。" />
          </el-form-item>
          <el-form-item label="寓意">
            <el-input v-model="createForm.meaningsText" type="textarea" :rows="4"
                      placeholder="每行一条寓意&#10;如：多子多福：寓意多子多福、子孙昌盛。" />
          </el-form-item>
          <el-form-item label="实物图 URL">
            <el-input v-model="createForm.image_url" placeholder="文物图/复原图直链（https://…）" />
          </el-form-item>
          <el-form-item label="常用颜色">
            <el-input v-model="createForm.props.常用颜色" placeholder="如：红、金、石青" />
          </el-form-item>
          <el-form-item label="常用布料">
            <el-input v-model="createForm.props.常用布料" placeholder="如：缎、锦、缂丝" />
          </el-form-item>
          <el-form-item label="适用衣物">
            <el-input v-model="createForm.props.适用衣物" placeholder="如：袍服、马面裙" />
          </el-form-item>
          <el-form-item label="应用部位">
            <el-input v-model="createForm.props.应用部位" placeholder="如：衣身通身纹饰、领襟缘边" />
          </el-form-item>
          <el-form-item label="使用场景">
            <el-input v-model="createForm.props.使用场景" placeholder="如：婚嫁吉庆、日常穿着" />
          </el-form-item>
          <el-form-item label="常见搭配">
            <el-input v-model="createForm.pairsText" placeholder="逗号分隔，如：龙纹,云纹,缠枝纹" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="createVisible = false">取消</el-button>
          <el-button type="primary" :loading="createLoading" @click="submitCreate">提交创建</el-button>
        </template>
      </el-dialog>
    </template>

    <!-- ==================== 详情模式（衣冠卷面排版：眉标 → 大标题 → 属性行 → 分节） ==================== -->
    <template v-else>
      <div class="detail-layout">
        <section class="acc-panel detail-main">
          <div class="detail-head">
            <el-button size="small" @click="$router.push('/pattern')">返回列表</el-button>
            <el-button v-if="navStack.length" size="small" plain @click="goBackPattern">返回上一纹样</el-button>
            <el-button v-if="detail?.created_by" size="small" type="danger" plain style="margin-left: auto"
                       @click="removePattern(detail)">删除纹样</el-button>
          </div>

          <!-- 眉标 + 大标题 + 属性行 -->
          <div class="acc-eyebrow">
            <span class="acc-eyebrow-line"></span>
            <span>传统服饰纹样</span>
            <span v-if="detail?.code" class="acc-eyebrow-index">名录编号 {{ detail.code_ref || detail.code }}</span>
          </div>
          <h2 class="acc-detail-title" :class="{ 'is-long': titleLong }">{{ detail?.name }}</h2>
          <div class="acc-detail-meta">
            <span>{{ detail?.category || "类别待考" }}</span>
            <span class="dot"></span>
            <span>{{ detail?.dynasty || "盛行朝代待考" }}</span>
            <template v-if="detail?.applied">
              <span class="dot"></span>
              <span>{{ detail.applied }}</span>
            </template>
          </div>

          <!-- 实物文物图：主图大图 + 张数徽标，点击灯箱轮播（contain 不裁原图） -->
          <div class="img-row">
            <div v-if="firstImg" class="img-col" data-lb-native @click="openLightbox()">
              <img :src="firstImg" :alt="detail?.name" @error="onImgError" />
              <div v-if="detail?.images?.length > 1" class="count-badge">{{ detail.images.length }}张</div>
              <div class="label">实物文物图</div>
            </div>
          </div>

          <!-- 简介 -->
          <div v-if="has('简介')" class="section">
            <AccSecHead :no="secNo('简介')" title="简介" sub="纹样源流与总体介绍" />
            <p class="acc-detail-copy">{{ detail?.meaning || "待补充" }}</p>
          </div>

          <!-- 朝代脉络 -->
          <div v-if="has('朝代脉络')" class="section">
            <AccSecHead :no="secNo('朝代脉络')" title="朝代脉络" sub="纵览历朝演变" />
            <div v-for="(e, i) in detail.dynasties" :key="i" class="era-item">
              <div class="era-period">{{ e.period }}</div>
              <div class="era-desc">{{ e.desc }}</div>
            </div>
          </div>

          <!-- 寓意 -->
          <div v-if="has('寓意')" class="section">
            <AccSecHead :no="secNo('寓意')" title="寓意" sub="图必有意，意必吉祥" />
            <div v-for="(m, i) in detail.meanings" :key="i" class="meaning-item">{{ m }}</div>
          </div>

          <!-- 属性 -->
          <div v-if="has('属性')" class="section">
            <AccSecHead :no="secNo('属性')" title="属性" sub="颜色 · 布料 · 衣物 · 部位" />
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
          <div v-if="has('常见搭配纹样')" class="section">
            <AccSecHead :no="secNo('常见搭配纹样')" title="常见搭配纹样" sub="点击卡片可跳转至对应纹样" />
            <div class="partner-grid">
              <div v-for="(pn, i) in detail.pairs" :key="i" class="partner-card" data-lb-native role="link" tabindex="0"
                   @click="jumpPair(pn)" @keydown.enter="jumpPair(pn)">
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
          <div v-if="has('知识图谱关联')" class="section">
            <AccSecHead :no="secNo('知识图谱关联')" title="知识图谱关联" sub="名录字段速览" />
            <div class="graph-nodes">
              <span class="graph-node"><i>类别</i>{{ detail?.category }}</span>
              <span class="graph-node"><i>盛行朝代</i>{{ detail?.dynasty || "待考" }}</span>
              <span class="graph-node"><i>文物图</i>{{ detail?.images?.length || 0 }} 幅</span>
              <span class="graph-node"><i>常见搭配</i>{{ detail?.pairs?.length || 0 }} 种</span>
              <span class="graph-node"><i>名录编号</i>{{ detail?.code || "待考" }}</span>
            </div>
          </div>
        </section>

        <aside class="detail-side acc-sticky">
          <div class="acc-aside-card">
            <AccSectionHead title="名录信息" size="sm" />
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="类别">{{ detail?.category || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="盛行朝代">{{ detail?.dynasty || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="名录编号">{{ detail?.code || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="服饰应用部位">{{ detail?.applied || "待考" }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div v-if="detail?.similar" class="acc-aside-card">
            <AccSectionHead title="相似纹样辨识" size="sm" />
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
import { ElMessage, ElMessageBox } from "element-plus";
import PageHero from "@/components/PageHero.vue";
import AccCard from "@/components/acc/AccCard.vue";
import AccSectionHead from "@/components/acc/AccSectionHead.vue";
import AccSecHead from "@/components/acc/AccSecHead.vue";
import { pad, toneOf } from "@/components/acc/accMeta";
import { fetchPatternCategories, fetchPatternItems, fetchPatternDetail, createPattern, deletePattern } from "@/api/modules";

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

/* 用户创建纹样 */
const createVisible = ref(false);
const createLoading = ref(false);
const createForm = ref<any>({
  name: "", category: "", meaning: "", image_url: "",
  dynastiesText: "", meaningsText: "",
  props: { 常用颜色: "", 常用布料: "", 适用衣物: "", 应用部位: "", 使用场景: "" },
  pairsText: "",
});
function openCreate() {
  createForm.value = { name: "", category: "", meaning: "", image_url: "", dynastiesText: "", meaningsText: "", props: { 常用颜色: "", 常用布料: "", 适用衣物: "", 应用部位: "", 使用场景: "" }, pairsText: "" };
  createVisible.value = true;
}
async function submitCreate() {
  if (!createForm.value.name.trim()) return ElMessage.warning("请填写纹样名称");
  createLoading.value = true;
  try {
    const pairs = createForm.value.pairsText.split(/[,，、]/).map((s: string) => s.trim()).filter(Boolean);
    // 朝代脉络：每行 "朝代|说明"
    const dynasties = createForm.value.dynastiesText.split("\n").map((s: string) => s.trim()).filter(Boolean)
      .map((line: string) => {
        const m = line.split(/[|｜]/);
        return { period: (m[0] || "").trim(), desc: (m.slice(1).join("|") || "").trim() };
      }).filter((d: any) => d.period);
    // 寓意：每行一条
    const meanings = createForm.value.meaningsText.split("\n").map((s: string) => s.trim()).filter(Boolean);
    const r: any = await createPattern({
      name: createForm.value.name.trim(),
      category: createForm.value.category,
      meaning: createForm.value.meaning,
      image_url: createForm.value.image_url,
      dynasties,
      meanings,
      props: createForm.value.props,
      pairs,
    });
    if (r.error) return ElMessage.error(r.error);
    ElMessage.success(`已创建纹样「${r.name}」`);
    createVisible.value = false;
    if (route.params.id) router.push("/pattern");
    load();
    loadCategories();
    loadUserWorks();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "添加失败（请确认已登录）");
  } finally {
    createLoading.value = false;
  }
}
async function removePattern(p: any) {
  try {
    await ElMessageBox.confirm(`确定删除纹样「${p.name}」？删除后不可恢复。`, "删除确认", { type: "warning" });
  } catch { return; }
  try {
    const r: any = await deletePattern(p.id);
    if (r.error) return ElMessage.error(r.error);
    ElMessage.success("已删除");
    router.push("/pattern");
    load();
    loadCategories();
    loadUserWorks();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败（请确认已登录）");
  }
}

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

/* 用户作品：用户添加的纹样 */
const uwKeyword = ref("");
const userWorks = ref<any[]>([]);
async function loadUserWorks() {
  const kw = uwKeyword.value.trim();
  try {
    const d: any = await fetchPatternItems({});
    let arr = (d.items || []).filter((x: any) => x.created_by);
    if (kw) {
      arr = arr.filter((x: any) => (x.name || "").includes(kw) || (x.meaning || "").includes(kw) || (x.category || "").includes(kw));
    }
    userWorks.value = arr;
  } catch (e) { /* 忽略 */ }
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

/* 点击常见搭配 → 直接进入该纹样详情（维护跳转链，可逐层返回） */
function jumpPair(name: string) {
  const id = pairIdMap[name];
  if (id) {
    const chain = [...navStack.value];
    if (route.params.id) chain.push(Number(route.params.id));
    const q = chain.length ? { from: chain.join(",") } : {};
    router.push({ path: `/pattern/${id}`, query: q });
  } else {
    router.push({ path: "/pattern", query: { q: name } }); // 库中无此条目时才回列表搜索
  }
}

/* 跳转链：当前纹样之前经过的纹样 id 列表（由近及远） */
const navStack = computed<number[]>(() => {
  const f = route.query.from;
  if (!f) return [];
  return String(f).split(",").map((x) => Number(x)).filter((x) => x > 0);
});

/* 返回上一纹样（弹出一层，保留剩余链） */
function goBackPattern() {
  const chain = [...navStack.value];
  const backId = chain.pop();
  if (!backId) return;
  const q = chain.length ? { from: chain.join(",") } : {};
  router.push({ path: `/pattern/${backId}`, query: q });
}

const props = computed(() => detail.value?.props || {});
const propsList = computed(() => {
  const p = props.value;
  return ["常用颜色", "常用布料", "适用衣物", "应用部位"].filter((k) => p[k]).map((k) => ({ k, v: p[k] }));
});

/* 详情分节：条件区块隐藏时节号仍连续 */
const detailSections = computed<string[]>(() => {
  const d = detail.value;
  const out = ["简介"];
  if (d?.dynasties?.length) out.push("朝代脉络");
  if (d?.meanings?.length) out.push("寓意");
  if (propsList.value.length) out.push("属性");
  if (d?.pairs?.length) out.push("常见搭配纹样");
  out.push("知识图谱关联");
  return out;
});
function has(k: string) {
  return detailSections.value.includes(k);
}
function secNo(k: string) {
  return pad(detailSections.value.indexOf(k) + 1);
}
const titleLong = computed(() => (detail.value?.name || "").length > 6);

function onImgError(e: Event) {
  (e.target as HTMLImageElement).style.display = "none";
}

/* 路由变化时加载（fullPath 覆盖列表/详情/搜索/搭配跳转全部场景） */
watch(
  () => route.fullPath,
  () => {
    const id = route.params.id;
    if (id) {
      loadDetail(Number(id));
    } else {
      detail.value = null;
      const q = route.query.q as string | undefined;
      if (q) keyword.value = q;
      load();
    }
  },
  { immediate: true }
);

onMounted(() => {
  loadCategories();
  if (!route.params.id) loadUserWorks();
});
</script>

<style scoped>
/* 页面容器宽度与调色由 acc-scope.css 统一接管，这里只补本页独有的版式 */
.pattern-page { padding: 0 0 60px; }

/* 卡片是裸 div 补了 tabindex 的，全站没有默认焦点环，这里自己给一个 */
.uw-card:focus-visible, .partner-card:focus-visible {
  outline: 2px solid var(--acc-gold, #c9a227); outline-offset: 2px;
}

/* ===== 详情模式（衣冠卷面：主栏 + 右栏） ===== */
.detail-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 44px; align-items: start; }
.detail-main { min-width: 0; }
.detail-head { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 22px; }
.body-text { margin: 10px 0 0; color: var(--acc-ink-2, #5c4c3a); font-size: 13.5px; line-height: 1.85; }
.detail-side { display: flex; flex-direction: column; min-width: 0; }
.graph-nodes { display: flex; flex-wrap: wrap; gap: 8px; }
.graph-node { border: 1px solid var(--acc-line, #e6dcc8); background: var(--acc-card-solid, #fffdf8); border-radius: 6px; padding: 4px 10px; font-size: 13px; color: var(--acc-ink-2, #5c4c3a); }
.graph-node i { font-style: normal; color: var(--acc-red, #7a221c); margin-right: 6px; }

/* 实物文物图：定高 + contain，原图不裁 */
.img-row { margin: 18px 0 6px; }
.img-col { width: 100%; height: 300px; border-radius: 10px; background: #f8f0e1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 12px; color: var(--acc-ink-3, #94836d); border: 1px solid var(--acc-line, #e6dcc8); cursor: zoom-in; position: relative; overflow: hidden; }
.img-col img { width: 100%; height: 100%; object-fit: contain; border-radius: 10px; }
.img-col .count-badge { position: absolute; bottom: 26px; right: 8px; background: rgba(58, 47, 36, .72); color: #fff8e8; font-size: 10px; padding: 2px 7px; border-radius: 8px; }
.img-col .label { position: absolute; bottom: 0; left: 0; right: 0; text-align: center; font-size: 11px; letter-spacing: 2px; color: var(--acc-red, #7a221c); background: rgba(255, 253, 248, .82); border-top: 1px solid var(--acc-line-gold, rgba(201, 162, 39, .34)); padding: 3px 0; }

/* 分节内的正文块（标题由 AccSecHead 负责） */
.section { margin-top: 30px; }
.era-item { display: flex; gap: 14px; padding: 10px 0; border-bottom: 1px dashed var(--acc-line, #e6dcc8); }
.era-period { min-width: 92px; font-weight: 700; color: var(--acc-red, #7a221c); font-size: 13px; letter-spacing: 1px; }
.era-desc { font-size: 13px; color: var(--acc-ink-2, #5c4c3a); line-height: 1.8; }
.meaning-item { font-size: 13.5px; color: var(--acc-ink-2, #5c4c3a); line-height: 1.8; padding: 4px 0 4px 18px; position: relative; }
.meaning-item::before { content: "·"; color: var(--acc-gold, #c9a227); font-weight: 700; position: absolute; left: 6px; }
.attr-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
.attr-card { background: rgba(201, 162, 39, .07); border: 1px solid var(--acc-line, #e6dcc8); border-radius: 8px; padding: 12px 14px; }
.attr-label { font-size: 12px; color: var(--acc-ink-3, #94836d); margin-bottom: 5px; letter-spacing: 1px; }
.attr-value { font-size: 13.5px; color: var(--acc-ink, #3a2f24); line-height: 1.7; }
.attr-scene { font-size: 12.5px; color: var(--acc-ink-3, #94836d); margin-top: 10px !important; letter-spacing: 1px; }
.partner-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-top: 12px; }
.partner-card { background: rgba(255, 253, 248, .8); border: 1px solid var(--acc-line, #e6dcc8); border-radius: 8px; padding: 10px; cursor: pointer; text-align: center; transition: transform .2s, border-color .2s; }
.partner-card:hover { transform: translateY(-3px); border-color: rgba(201, 162, 39, .55); }
.partner-card .imgs { display: flex; gap: 4px; margin-bottom: 6px; }
.partner-card .imgs img { flex: 1; min-width: 0; width: 100%; max-width: 100%; aspect-ratio: 1 / 1; height: auto; object-fit: contain; border-radius: 4px; background: #f4ead9; }
.partner-card .imgs .placeholder { flex: 1; aspect-ratio: 1 / 1; display: flex; align-items: center; justify-content: center; background: #f4ead9; border-radius: 4px; font-size: 10px; color: var(--acc-ink-3, #94836d); }
.partner-card .name { font-size: 13px; color: var(--acc-ink, #3a2f24); font-weight: 600; }
.partner-card .label { font-size: 10px; color: var(--acc-ink-3, #94836d); margin-top: 2px; letter-spacing: 1px; }

/* 用户作品：用户添加的纹样 */
.user-works { margin: 26px 0 24px; }
.uw-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 10px; flex-wrap: wrap; }
.uw-tools { display: flex; align-items: center; gap: 8px; }
.uw-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 10px; }
.uw-card { border: 1px solid var(--acc-line, #e6dcc8); border-radius: 8px; overflow: hidden; cursor: pointer; background: var(--acc-card-solid, #fffdf8); transition: box-shadow .2s, border-color .2s; }
.uw-card:hover { box-shadow: 0 6px 18px rgba(90, 60, 30, .14); border-color: rgba(201, 162, 39, .5); }
.uw-card img { width: 100%; aspect-ratio: 1 / 1; height: auto; object-fit: contain; display: block; background: #f4ead9; }
.uw-thumb { width: 100%; aspect-ratio: 1 / 1; display: flex; align-items: center; justify-content: center; font-size: 12px; color: var(--acc-ink-3, #94836d); background: #f4ead9; }
.uw-info { padding: 8px 10px; }
.uw-info h4 { margin: 0 0 3px; font-size: 14px; color: var(--acc-ink, #3a2f24); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.uw-info p { margin: 1px 0; font-size: 12px; color: var(--acc-ink-3, #94836d); }
.uw-info .uw-desc { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.6; }
.uw-empty-box { grid-column: 1 / -1; padding: 22px 0; }
.p-code { font-size: 11px; color: var(--acc-red, #7a221c); font-weight: 500; margin-right: 6px; background: rgba(201, 162, 39, .12); padding: 1px 6px; border-radius: 4px; white-space: nowrap; }

@media (max-width: 1023px) {
  .detail-layout { gap: 24px; }
}

@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
  .img-col { height: 232px; }
}

@media (max-width: 480px) {
  .attr-grid { grid-template-columns: 1fr; }
}
</style>
