<template>
  <div class="fabric-page">
    <!-- ==================== 列表模式 ==================== -->
    <template v-if="!route.params.id">
    <!-- 头部 -->
    <PageHero title="衣溯AI · 历代服装面料" kicker="FABRIC · 一部织造史" sub="从上古葛麻到明清织金——每一块面料，都是一部华夏织造史" seal="织" />

    <!-- 筛选栏 -->
    <div class="filter-bar anim-rise" style="animation-delay: .5s">
      <div class="filter-left">
        <el-radio-group v-model="category" @change="load">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button v-for="c in categories" :key="c" :value="c">{{ c }}</el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-right">
        <el-input v-model="keyword" placeholder="搜索面料（如：罗、锦、缂丝）" clearable size="small"
                  style="width: 210px" @keyup.enter="load" />
        <el-button size="small" type="primary" plain :loading="webLoading" @click="doWebSearch">全网搜索</el-button>
        <el-button size="small" type="danger" plain @click="openCreate">＋ 创建面料</el-button>
        <span class="count-tip">共 {{ total }} 种面料</span>
      </div>
    </div>

    <!-- 用户作品：其他用户创建的面料（自社区迁移） -->
    <div class="user-works ys-card">
      <div class="uw-head">
        <h3 class="ys-title">用户作品 · 面料</h3>
        <div class="uw-tools">
          <el-input v-model="uwKeyword" placeholder="搜索用户面料…" size="small" clearable style="width: 180px"
                    @keyup.enter="loadUserWorks" @clear="loadUserWorks" />
          <el-button size="small" @click="loadUserWorks">搜索</el-button>
        </div>
      </div>
      <div class="uw-grid">
        <div v-for="f in userFabrics" :key="f.id" class="uw-card" @click="openDetail(f)">
          <img v-if="f.image_url" :src="f.image_url" :alt="f.name" loading="lazy" />
          <div v-else class="uw-thumb">暂无实物图</div>
          <div class="uw-info">
            <h4>{{ f.name }}</h4>
            <p>{{ f.dynasty_peak }} · {{ f.category }}</p>
            <p class="uw-desc">{{ f.description }}</p>
          </div>
        </div>
        <div v-if="!userFabrics.length" class="ys-empty uw-empty-box">{{ uwKeyword ? "未找到匹配的用户面料" : "暂无用户创建的面料，点击「＋ 创建面料」创建第一条吧" }}</div>
      </div>
    </div>

    <!-- 创建面料弹窗 -->
    <el-dialog v-model="createVisible" title="自主创建面料档案" width="560px" destroy-on-close>
      <el-form :model="createForm" label-width="84px" size="small">
        <el-form-item label="面料名称" required>
          <el-input v-model="createForm.name" placeholder="如：杭罗" maxlength="50" />
        </el-form-item>
        <el-form-item label="类别" required>
          <el-select v-model="createForm.category" placeholder="选择类别" style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="原料">
          <el-input v-model="createForm.raw_material" placeholder="如：桑蚕丝" />
        </el-form-item>
        <el-form-item label="盛行朝代">
          <el-input v-model="createForm.dynasty_peak" placeholder="如：明清" />
        </el-form-item>
        <el-form-item label="织造技艺">
          <el-input v-model="createForm.technique" placeholder="如：绞经组织" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="createForm.description" type="textarea" :rows="3"
                    placeholder="原料、工艺、文物实例、史料依据等" />
        </el-form-item>
        <el-form-item label="图片链接">
          <el-input v-model="createForm.image_url" placeholder="选填：直接粘贴图片 URL，留空则显示占位" />
        </el-form-item>
        <el-form-item label="史料出处">
          <el-input v-model="createForm.source_ref" placeholder="如：故宫博物院藏" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="createVisible = false">取消</el-button>
        <el-button size="small" type="danger" :loading="createLoading" @click="submitCreate">保存面料</el-button>
      </template>
    </el-dialog>

    <!-- 全网搜索弹窗 -->
    <el-dialog v-model="webVisible" title="全网搜索 · 面料资料" width="720px" destroy-on-close>
      <div class="web-search-bar">
        <el-input v-model="webQuery" placeholder="输入关键词搜索全网（如：宋代四经绞罗 工艺）" size="small"
                  @keyup.enter="doWebSearch" />
        <el-button size="small" type="primary" :loading="webLoading" @click="doWebSearch">搜索</el-button>
      </div>
      <div v-if="webError" class="web-error">{{ webError }}</div>
      <div v-loading="webLoading" class="web-results">
        <a v-for="(r, i) in webResults" :key="i" class="web-item" :href="r.url" target="_blank" rel="noopener">
          <div class="web-title">{{ r.title }}</div>
          <div class="web-snippet">{{ r.snippet }}</div>
          <div class="web-source">{{ r.source }}</div>
        </a>
        <el-empty v-if="!webLoading && webResults.length === 0 && !webError" description="暂无搜索结果" :image-size="70" />
      </div>
    </el-dialog>

    <!-- 面料卡片网格 -->
    <div v-loading="loading" class="fabric-grid">
      <div v-for="f in filteredList" :key="f.id" class="fabric-card" @click="openSplit(f)">
        <div class="card-img">
          <img v-if="f.image_url" :src="f.image_url" :alt="f.name" loading="lazy" @error="onImgError" />
          <div v-else class="img-placeholder">暂无图</div>
          <span class="dynasty-badge">{{ f.dynasty_peak }}</span>
          <span v-if="f.created_by" class="user-badge">用户创建</span>
        </div>
        <div class="card-body">
          <div class="f-head">
            <h3>{{ f.name }}</h3>
            <el-button v-if="f.created_by || f.source_ref === '用户创建'" size="small" text type="danger" class="del-btn" @click.stop="removeFabric(f)">删除</el-button>
          </div>
          <div class="tags">
            <span class="tag cat">{{ f.category }}</span>
            <span class="tag">{{ f.raw_material }}</span>
            <span v-if="f.technique" class="tag tech">{{ f.technique }}</span>
          </div>
          <p class="desc">{{ f.description }}</p>
          <div class="card-foot">
            <span class="source">📜 {{ f.source_ref }}</span>
            <span class="more">查看详情 ›</span>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && filteredList.length === 0" description="未找到匹配的面料" />
    </div>

    <!-- 点击卡片：主图从中心放大、分裂翻转成三张素材卡片，点击任意一张进入详情 -->
    <SplitReveal
      :visible="splitVisible"
      :title="splitTitle"
      :cards="splitCards"
      @close="splitVisible = false"
      @select="onSplitSelect"
    />
    </template>

    <!-- ==================== 详情模式（与档案详情一致） ==================== -->
    <template v-else>
      <div class="detail-layout">
        <section class="ys-card detail-main">
          <div class="detail-head">
            <el-button size="small" @click="$router.push('/fabric')">返回列表</el-button>
            <h2>{{ detail?.name }} <span class="dynasty">{{ detail?.dynasty_peak }} · {{ detail?.category }}</span></h2>
            <el-button v-if="detail?.created_by || detail?.source_ref === '用户创建'" size="small" type="danger" plain
                       style="margin-left: auto" @click="removeFabric(detail)">删除面料</el-button>
          </div>

          <el-descriptions :column="2" border size="small" style="margin: 14px 0">
            <el-descriptions-item label="类别">{{ detail?.category || "待考" }}</el-descriptions-item>
            <el-descriptions-item label="盛行朝代">{{ detail?.dynasty_peak || "待考" }}</el-descriptions-item>
            <el-descriptions-item label="原料">{{ detail?.raw_material || "待考" }}</el-descriptions-item>
            <el-descriptions-item label="织造技艺">{{ detail?.technique || "待考" }}</el-descriptions-item>
            <el-descriptions-item label="史料出处">{{ detail?.source_ref || "待考" }}</el-descriptions-item>
            <el-descriptions-item label="工艺资料">
              <template v-if="detail?.craft">{{ detail.craft.name || "已收录" }}</template>
              <template v-else>待考</template>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 面料实物图 -->
          <template v-if="detail?.image_url">
            <h3 class="ys-title">面料实物图</h3>
            <div class="relic-gallery">
              <div class="relic-card">
                <img :src="detail.image_url" :alt="`${detail?.name}实物`" loading="lazy"
                     @click="relicLightbox = detail.image_url" @error="onImgError" />
                <p class="relic-source">▲ {{ detail?.name }} · 实物 / 传世图像</p>
              </div>
            </div>
          </template>

          <!-- 工艺示意图 -->
          <template v-if="detail?.craft?.images && (detail.craft.images.overview || detail.craft.images.detail)">
            <h3 class="ys-title">工艺示意</h3>
            <div class="craft-imgs">
              <div v-if="detail.craft.images.overview" class="craft-img-block">
                <div class="ci-title">完整流程</div>
                <img :src="detail.craft.images.overview" :alt="detail.name + '工艺流程'" class="craft-img"
                     @click="relicLightbox = detail.craft.images.overview" @error="onImgError" />
              </div>
              <div v-if="detail.craft.images.detail" class="craft-img-block">
                <div class="ci-title">细节特写</div>
                <img :src="detail.craft.images.detail" :alt="detail.name + '工艺细节'" class="craft-img"
                     @click="relicLightbox = detail.craft.images.detail" @error="onImgError" />
              </div>
            </div>
          </template>

          <!-- 史料详析 -->
          <h3 class="ys-title">史料详析</h3>
          <div class="detail-sections">
            <div class="detail-sec">
              <h4 class="sec-title">面料简介</h4>
              <p class="sec-body">{{ detail?.description || "（暂无简介）" }}</p>
            </div>
            <div v-if="detail?.craft?.history_note" class="detail-sec">
              <h4 class="sec-title">工艺史料</h4>
              <p class="sec-body">{{ detail.craft.history_note }}</p>
            </div>
          </div>

          <!-- 制作流程 -->
          <template v-if="fabricSteps.length">
            <h3 class="ys-title">制作流程</h3>
            <div class="detail-sections">
              <div v-for="s in fabricSteps" :key="s.num" class="detail-sec">
                <h4 class="sec-title">{{ s.num_cn ? s.num_cn + " · " : "" }}{{ s.label || s.title }}</h4>
                <p class="sec-body">{{ s.desc || s.title }}</p>
              </div>
            </div>
          </template>

          <!-- 知识图谱关联 -->
          <h3 class="ys-title">知识图谱关联</h3>
          <div class="graph-nodes">
            <span class="graph-node"><i>类别</i>{{ detail?.category }}</span>
            <span class="graph-node"><i>原料</i>{{ detail?.raw_material }}</span>
            <span class="graph-node"><i>织造技艺</i>{{ detail?.technique }}</span>
            <span class="graph-node"><i>盛行朝代</i>{{ detail?.dynasty_peak }}</span>
            <span class="graph-node"><i>史料出处</i>{{ detail?.source_ref }}</span>
          </div>
        </section>

        <aside class="detail-side">
          <div class="ys-card chat-card">
            <h3 class="ys-title">诗文 · 古文</h3>
            <div v-if="detail?.poems?.length" class="detail-poems">
              <div v-for="(p, i) in detail.poems" :key="i" class="poem-item">
                <span v-if="p.src" class="poem-src">{{ p.src }}</span>
                <p>{{ p.text }}</p>
                <a :href="p.url" target="_blank" rel="noopener" class="poem-link">检索 ↗</a>
              </div>
            </div>
            <p v-else class="body-text">暂无诗文收录</p>
          </div>
          <div class="ys-card chat-card" style="margin-top: 14px">
            <h3 class="ys-title">工艺简介</h3>
            <p class="body-text">{{ detail?.craft?.history_note || detail?.description || "资料整理中。" }}</p>
          </div>
        </aside>
      </div>

      <el-image-viewer v-if="relicLightbox" :url-list="[relicLightbox]" @close="relicLightbox = ''" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fetchFabrics, fetchFabricWebSearch, createFabric, deleteFabric } from "@/api/modules";
import PageHero from "@/components/PageHero.vue";
import SplitReveal from "@/components/SplitReveal.vue";
import { ElMessage, ElMessageBox } from "element-plus";

const route = useRoute();
const router = useRouter();

const list = ref<any[]>([]);
const categories = ref<string[]>([]);
const category = ref("");
const keyword = ref("");
const loading = ref(false);
const total = ref(0);
const detailVisible = ref(false);
const detail = ref<any>(null);
const relicLightbox = ref("");
/* 全网搜索 */
const webVisible = ref(false);
const webLoading = ref(false);
const webError = ref("");
const webQuery = ref("");
const webResults = ref<any[]>([]);
/* 自主创建 */
const createVisible = ref(false);
const createLoading = ref(false);
const createForm = ref({
  name: "", category: "", raw_material: "", dynasty_peak: "",
  technique: "", description: "", image_url: "", source_ref: "",
});
/* 用户作品：其他用户创建的面料（自社区迁移） */
const uwKeyword = ref("");
const userFabrics = ref<any[]>([]);
async function loadUserWorks() {
  const kw = uwKeyword.value.trim();
  try {
    const f: any = await fetchFabrics();
    let arr = (f.items || []).filter((x: any) => x.created_by || x.source_ref === "用户创建");
    if (kw) {
      arr = arr.filter((x: any) => (x.name || "").includes(kw) || (x.description || "").includes(kw));
    }
    userFabrics.value = arr.slice(0, 9);
  } catch { /* 忽略 */ }
}

/* 朝代时间排序：按 dynasty_peak 中最早出现的朝代作为起始年代权重 */
const DYNASTY_KEYS = ["上古", "先秦", "战国", "秦汉", "汉", "魏晋", "唐", "宋", "元", "明", "清", "后世", "历代"];
function dynastyStart(s: string): number {
  if (!s) return 99;
  for (let i = 0; i < DYNASTY_KEYS.length; i++) if (s.includes(DYNASTY_KEYS[i])) return i;
  return 99;
}
function dynastyEnd(s: string): number {
  if (!s) return 99;
  let r = 0;
  for (let i = 0; i < DYNASTY_KEYS.length; i++) if (s.includes(DYNASTY_KEYS[i])) r = i;
  return r;
}

const filteredList = computed(() => {
  let arr = list.value;
  const kw = keyword.value.trim();
  if (kw) {
    arr = arr.filter(
      (f) => f.name.includes(kw) || f.raw_material.includes(kw) || f.technique.includes(kw) || f.description.includes(kw)
    );
  }
  return [...arr].sort(
    (a, b) =>
      dynastyStart(a.dynasty_peak) - dynastyStart(b.dynasty_peak) ||
      dynastyEnd(a.dynasty_peak) - dynastyEnd(b.dynasty_peak) ||
      a.name.localeCompare(b.name, "zh")
  );
});

async function load() {
  loading.value = true;
  try {
    const res: any = await fetchFabrics(category.value);
    list.value = res.items || [];
    categories.value = res.categories || [];
    total.value = res.total || 0;
  } catch (e) {
    console.error("加载面料失败", e);
  } finally {
    loading.value = false;
  }
}

function openDetail(f: any) {
  router.push(`/fabric/${f.id}`);
}

/* 点击卡片：主图从中心放大、分裂翻转成三张素材卡片 */
const splitVisible = ref(false);
const splitTitle = ref("");
const splitCards = ref<any[]>([]);
let splitTarget: any = null;
function openSplit(f: any) {
  splitTarget = f;
  splitTitle.value = `${f.name} · 面料素材`;
  const craft = f.craft || {};
  const steps = (craft.steps || f.process_steps || []).slice(0, 4).map((s: any) => ({
    label: (s.num_cn || "工序") + " · " + (s.label || s.title || ""),
    value: s.desc || s.title || "",
  }));
  splitCards.value = [
    {
      image: f.image_url || undefined,
      kicker: `${f.category || "面料"} · ${f.dynasty_peak || ""}`,
      title: f.name,
      text: `${f.raw_material || ""}${f.technique ? " · " + f.technique : ""}`,
    },
    {
      image: craft.images?.overview || f.image_url || undefined,
      kicker: "工艺流程",
      title: "制作流程 · 完整示意",
      text: (craft.history_note || f.process || "工艺资料整理中。").slice(0, 80),
      list: steps,
    },
    {
      image: craft.images?.detail || undefined,
      kicker: "工艺细节",
      title: "细节特写 · 史料依据",
      text: (f.description || "（暂无简介）").slice(0, 80),
      list: f.source_ref ? [{ label: "史料出处", value: f.source_ref }] : undefined,
    },
  ];
  splitVisible.value = true;
}
function onSplitSelect() {
  splitVisible.value = false;
  if (splitTarget) router.push(`/fabric/${splitTarget.id}`);
}

function onImgError(e: Event) {
  (e.target as HTMLImageElement).style.display = "none";
}

async function doWebSearch() {
  const q = webQuery.value.trim() || keyword.value.trim();
  webVisible.value = true; // 点按钮即打开弹窗，用户可输入关键词
  if (!q) return;
  webQuery.value = q;
  webLoading.value = true;
  webError.value = "";
  try {
    const res: any = await fetchFabricWebSearch(q);
    webResults.value = res.results || [];
    webError.value = res.error || "";
  } catch (e: any) {
    webResults.value = [];
    webError.value = e?.response?.data?.detail || "全网搜索失败，请稍后重试";
  } finally {
    webLoading.value = false;
  }
}

function openCreate() {
  const token = localStorage.getItem("yisu_token") || "";
  if (!token) {
    ElMessage.warning("请先登录，再创建面料");
    router.push("/login");
    return;
  }
  createForm.value = { name: "", category: "", raw_material: "", dynasty_peak: "", technique: "", description: "", image_url: "", source_ref: "" };
  createVisible.value = true;
}

async function submitCreate() {
  const f = createForm.value;
  if (!f.name.trim()) { ElMessage.warning("请填写面料名称"); return; }
  if (!f.category) { ElMessage.warning("请选择类别"); return; }
  createLoading.value = true;
  try {
    const res: any = await createFabric(f);
    if (res && res.error) { ElMessage.error(res.error); return; }
    createVisible.value = false;
    ElMessage.success(`面料「${res.name}」已创建`);
    await load();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "创建失败，请确认已登录");
  } finally {
    createLoading.value = false;
  }
}

async function removeFabric(f: any) {
  try {
    await ElMessageBox.confirm(`确定删除面料「${f.name}」吗？删除后不可恢复。`, "删除确认", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch { return; }
  try {
    const res: any = await deleteFabric(f.id);
    if (res && res.error) { ElMessage.error(res.error); return; }
    ElMessage.success("面料已删除");
    await load();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.response?.data?.error || "删除失败，请确认已登录");
  }
}

onMounted(async () => {
  if (route.params.id) {
    await loadDetail();
  } else {
    await load();
  }
  loadUserWorks();
});

/* 详情模式：制作流程列表 */
const fabricSteps = computed<any[]>(() => {
  const d = detail.value;
  if (!d) return [];
  if (d.craft?.steps?.length) return d.craft.steps;
  if (d.process_steps?.length) return d.process_steps;
  return [];
});

/* 详情模式：路由 /fabric/:id → 从已加载列表取数据（未加载则先拉取） */
async function loadDetail() {
  const id = route.params.id;
  if (!id) return;
  if (!list.value.length) await load();
  const hit = list.value.find((x) => String(x.id) === String(id));
  if (hit) detail.value = hit;
  else detail.value = null;
}
watch(() => route.params.id, () => { if (route.params.id) loadDetail(); });
</script>

<style scoped>
.fabric-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}
.page-hero {
  text-align: center;
  padding: 18px 0 6px;
}
.page-hero h2 {
  font-size: 28px;
  color: #7c2d12;
  letter-spacing: 2px;
  margin-bottom: 6px;
}
.page-hero p {
  color: #8a6d5a;
  font-size: 14px;
  letter-spacing: 1px;
}
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 14px 0 18px;
}
.filter-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.count-tip {
  font-size: 13px;
  color: #8a6d5a;
}
.fabric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.fabric-card {
  background: #fffdf8;
  border: 1px solid #eadfd0;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.fabric-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 22px rgba(124, 45, 18, 0.12);
}
.card-img {
  position: relative;
  height: 160px;
  background: #f6efe4;
  overflow: hidden;
}
.card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.fabric-card:hover .card-img img {
  transform: scale(1.05);
}
.img-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b7a58f;
  font-size: 13px;
}
.dynasty-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(126, 36, 24, 0.85);
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}
.user-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(36, 96, 126, 0.85);
  color: #fff;
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 10px;
}
.card-body {
  padding: 12px 14px 14px;
}
.f-head { display: flex; justify-content: space-between; align-items: baseline; }
.f-head h3 {
  font-size: 18px;
  color: #4a2c17;
  margin-bottom: 8px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 8px;
  background: #f3e9db;
  color: #7c5b3e;
}
.tag.cat {
  background: #fde8e4;
  color: #a03422;
}
.tag.tech {
  background: #e6eef5;
  color: #2c5a7c;
}
.desc {
  font-size: 13px;
  color: #6b5440;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 62px;
}
.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  font-size: 12px;
}
.source {
  color: #a08b74;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 65%;
}
.more {
  color: #a03422;
  white-space: nowrap;
}
/* 详情弹窗 */
.detail-wrap {
  text-align: left;
}
.detail-img {
  width: 100%;
  max-height: 320px;
  object-fit: contain;
  background: #f6efe4;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: zoom-in;
}
.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.detail-wrap h3 {
  font-size: 20px;
  color: #4a2c17;
  margin-bottom: 8px;
}
.detail-desc {
  font-size: 14px;
  color: #5a4432;
  line-height: 1.8;
}
/* 面料工艺素材 */
.detail-craft {
  margin-top: 14px;
  background: #faf5ea;
  border: 1px solid #eadfd0;
  border-radius: 12px;
  padding: 12px 14px;
}
.craft-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.craft-step {
  flex: 1 1 200px;
  min-width: 170px;
  background: linear-gradient(135deg, rgba(225, 185, 143, 0.16), rgba(225, 185, 143, 0.08));
  border: 1px solid rgba(185, 138, 47, 0.35);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  gap: 8px;
}
.cs-num {
  flex: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #c9976a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cs-body { min-width: 0; }
.cs-label {
  font-size: 13px;
  font-weight: 700;
  color: #4a2c17;
}
.cs-label em {
  font-style: normal;
  color: #a03422;
  font-weight: 400;
  font-size: 12px;
}
.cs-body p {
  margin: 3px 0 0;
  font-size: 12px;
  color: #6b5440;
  line-height: 1.6;
}
.craft-imgs {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ci-title {
  font-size: 13px;
  font-weight: 700;
  color: #7c2d12;
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.craft-img {
  width: 100%;
  border-radius: 10px;
  border: 1px solid #eadfd0;
  background: #fffdf8;
}
.craft-note {
  margin-top: 12px;
  font-size: 12px;
  color: #8a6d5a;
  line-height: 1.7;
  border-top: 1px dashed #e3d5c2;
  padding-top: 10px;
}
.detail-process {
  margin-top: 14px;
  background: #f6efe4;
  border-radius: 8px;
  padding: 10px 12px;
}
.dp-title {
  font-size: 13px;
  font-weight: 700;
  color: #7c2d12;
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.dp-raw { margin: 0 0 4px; font-size: 13px; color: #7c5b3e; }
.dp-flow { margin: 0; font-size: 13px; color: #5a4432; line-height: 1.8; }
.dp-step {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 10px;
  background: #fffdf8;
  border: 1px solid #eadfd0;
  border-radius: 8px;
}
.dp-step-title {
  flex: none;
  min-width: 130px;
  font-size: 13px;
  font-weight: 700;
  color: #a03422;
}
.dp-step-desc {
  font-size: 12.5px;
  color: #5a4432;
  line-height: 1.7;
}
.detail-poems {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.poem-item {
  border-left: 3px solid #b98a2f;
  background: rgba(185, 138, 47, 0.08);
  border-radius: 0 8px 8px 0;
  padding: 8px 12px;
  position: relative;
}
.poem-src {
  display: inline-block;
  font-size: 11px;
  color: #8a5a12;
  background: rgba(185, 138, 47, 0.16);
  border-radius: 4px;
  padding: 1px 6px;
  margin-bottom: 4px;
}
.poem-item p { margin: 0; font-size: 13px; color: #5a4432; line-height: 1.75; padding-right: 44px; }
.poem-link {
  position: absolute;
  right: 10px;
  top: 10px;
  font-size: 12px;
  color: #a03422;
  text-decoration: none;
  border: 1px solid rgba(160, 52, 34, 0.4);
  border-radius: 10px;
  padding: 1px 8px;
}
.poem-link:hover { background: rgba(160, 52, 34, 0.1); }
.detail-source {
  margin-top: 14px;
  font-size: 13px;
  color: #8a6d5a;
  background: #f6efe4;
  border-radius: 8px;
  padding: 8px 12px;
}
/* 全网搜索弹窗 */
.web-search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.web-error {
  color: #c0392b;
  font-size: 13px;
  margin-bottom: 10px;
}
.web-results {
  min-height: 120px;
}
.web-item {
  display: block;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #eadfd0;
  margin-bottom: 8px;
  text-decoration: none;
  transition: background 0.2s;
}
.web-item:hover {
  background: #f6efe4;
}
.web-title {
  font-size: 14px;
  font-weight: 600;
  color: #7c2d12;
  margin-bottom: 4px;
}
.web-snippet {
  font-size: 13px;
  color: #6b5440;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.web-source {
  font-size: 12px;
  color: #a08b74;
  margin-top: 4px;
}

/* 用户作品：其他用户创建的面料 */
.user-works { margin-bottom: 14px; }
.uw-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 10px; flex-wrap: wrap; }
.uw-head .ys-title { margin: 0; }
.uw-tools { display: flex; align-items: center; gap: 8px; }
.uw-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 10px; }
.uw-card { border: 1px solid var(--ys-line); border-radius: 8px; overflow: hidden; cursor: pointer; background: #fffdf8; transition: box-shadow .2s; }
.uw-card:hover { box-shadow: 0 4px 14px rgba(122, 58, 32, .12); }
.uw-card img { width: 100%; height: 96px; object-fit: cover; display: block; background: #f4ecdf; }
.uw-thumb { width: 100%; height: 96px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #8a7a60; background: #f6efe4; }
.uw-info { padding: 8px 10px; }
.uw-info h4 { margin: 0 0 3px; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.uw-info p { margin: 1px 0; font-size: 12px; color: var(--ys-ink-3); }
.uw-info .uw-desc { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.uw-empty-box { grid-column: 1 / -1; padding: 22px 0; }

/* ============ 详情模式（与档案详情一致） ============ */
.detail-layout { display: grid; grid-template-columns: 1fr 340px; gap: 20px; }
.detail-main { min-width: 0; }
.detail-head { display: flex; align-items: center; gap: 14px; }
.detail-head h2 { margin: 0; font-size: 22px; }
.detail-head .dynasty { font-size: 13px; color: var(--ys-ink-3); font-weight: 400; margin-left: 6px; }
.body-text { color: var(--ys-ink-2); line-height: 1.8; }
.graph-nodes { display: flex; flex-wrap: wrap; gap: 8px; }
.graph-node { border: 1px solid var(--ys-line); background: #fffdf8; border-radius: 6px; padding: 4px 10px; font-size: 13px; }
.graph-node i { font-style: normal; color: var(--ys-red-deep); margin-right: 4px; }
.relic-gallery { margin: 10px 0 18px; }
.relic-card { display: inline-block; max-width: 420px; }
.relic-card img { width: 100%; max-height: 340px; object-fit: contain; border-radius: 8px; box-shadow: 0 8px 20px rgba(122, 60, 30, 0.18); cursor: zoom-in; background: #fffdf6; }
.relic-source { font-size: 12px; color: var(--ys-ink-3); margin-top: 6px; line-height: 1.6; }
.detail-sections { margin: 10px 0 16px; display: flex; flex-direction: column; gap: 12px; }
.detail-sec { border-left: 3px solid var(--ys-red); background: rgba(169, 50, 38, 0.04); border-radius: 0 8px 8px 0; padding: 10px 14px; }
.sec-title { margin: 0 0 6px; font-size: 14px; color: var(--ys-red-deep); }
.sec-body { margin: 0; color: var(--ys-ink-2); line-height: 1.8; font-size: 13.5px; }
.craft-imgs { margin: 10px 0 18px; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.craft-img-block { border: 1px solid var(--ys-line); border-radius: 8px; overflow: hidden; background: #fffdf8; }
.ci-title { font-size: 12.5px; color: var(--ys-red-deep); padding: 6px 10px; border-bottom: 1px dashed var(--ys-line); }
.craft-img { width: 100%; max-height: 300px; object-fit: contain; display: block; background: #fffdf6; cursor: zoom-in; }
.detail-poems { display: flex; flex-direction: column; gap: 10px; }
.poem-item { border-left: 2px solid var(--ys-red); padding: 6px 10px; background: rgba(169, 50, 38, 0.04); border-radius: 0 6px 6px 0; }
.poem-src { font-size: 11.5px; color: var(--ys-red-deep); }
.poem-item p { margin: 3px 0; font-size: 12.5px; line-height: 1.7; color: var(--ys-ink-2); }
.poem-link { font-size: 12px; color: #7c2d12; text-decoration: none; }
.chat-card { padding: 16px; }
.detail-side { display: flex; flex-direction: column; gap: 0; }
@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
}
</style>
