<template>
  <div class="fabric-page acc-scope">
    <!-- ==================== 列表模式 ==================== -->
    <template v-if="!route.params.id">
    <!-- 头部 -->
    <PageHero grand
      title="面料"
      eyebrow-en="FABRIC · 织造图谱"
      eyebrow-index="VOL. 织·01–31"
      kicker="一部织造史"
      sub="从上古葛麻到明清织金——每一块面料，都是一部华夏织造史；经纬之间，见王朝工艺之变。"
      seal="织"
      vertical="葛麻 · 丝绸 · 绫罗 · 织锦 · 缂丝 · 妆花"
      primary-label="浏览本卷" primary-href="#catalog"
      secondary-label="看出土地图" secondary-href="/geomap"
      :stats="[
        { n: '31', l: '面料品类' },
        { n: '09', l: '织造大类' },
        { n: '16', l: '本期名锦' },
        { n: '08', l: '阅读板块' },
      ]" />

    <!-- 工具条：区块标题在左、搜索与创建在右（控件不变，只换皮） -->
    <div class="acc-toolbar">
      <AccSectionHead no="织" kicker="面料名录 · 九类" title="面料目录" :sub="`共 ${total} 种`" />
      <div class="acc-toolbar-tools">
        <el-input v-model="keyword" placeholder="搜索面料（如：罗、锦、缂丝）" clearable size="small"
                  style="width: 210px" @keyup.enter="load" />
        <el-button size="small" type="primary" plain :loading="webLoading" @click="doWebSearch">全网搜索</el-button>
        <el-button size="small" type="danger" plain @click="openCreate">＋ 创建面料</el-button>
      </div>
    </div>

    <!-- 类别筛选条 -->
    <div class="acc-filter-row">
      <el-radio-group v-model="category" @change="load">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button v-for="c in categories" :key="c" :value="c">{{ c }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 用户作品：其他用户创建的面料（自社区迁移） -->
    <div class="user-works acc-aside-card">
      <div class="uw-head">
        <AccSectionHead title="用户作品 · 面料" size="sm" />
        <div class="uw-tools">
          <el-input v-model="uwKeyword" placeholder="搜索用户面料…" size="small" clearable style="width: 180px"
                    @keyup.enter="loadUserWorks" @clear="loadUserWorks" />
          <el-button size="small" @click="loadUserWorks">搜索</el-button>
        </div>
      </div>
      <div class="uw-grid">
        <div v-for="f in userFabrics" :key="f.id" class="uw-card" role="link" tabindex="0" @click="openDetail(f)" @keydown.enter="openDetail(f)">
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

    <!-- 创建面料弹窗（信息收集与详情页正文一致：基础信息 → 面料简介 → 工艺史料 → 制作流程 → 史料出处 → 诗文 → 图片） -->
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
        <el-form-item label="面料简介">
          <el-input v-model="createForm.description" type="textarea" :rows="3"
                    placeholder="原料、工艺、文物实例、史料依据等，如：以大麻茎皮纤维织成，先秦平民最主要的衣料……" />
        </el-form-item>
        <el-form-item label="工艺史料">
          <el-input v-model="createForm.historyNote" type="textarea" :rows="3"
                    placeholder="史证引文与出土实物，如：史证：《诗经》「东门之池，可以沤麻」，马王堆一号汉墓出土细麻布残片。" />
        </el-form-item>
        <el-form-item label="制作流程">
          <el-input v-model="createForm.stepsText" type="textarea" :rows="4"
                    placeholder="每行一个步骤，格式：步骤|说明&#10;如：种麻收刈|大田种植大麻，适时收割成熟麻秆" />
        </el-form-item>
        <el-form-item label="史料出处">
          <el-input v-model="createForm.source_ref" placeholder="如：故宫博物院藏" />
        </el-form-item>
        <el-form-item label="诗文·古文">
          <el-input v-model="createForm.poemsText" type="textarea" :rows="3"
                    placeholder="每行一条，格式：出处|引文&#10;如：《诗经·陈风·东门之池》|东门之池，可以沤麻，彼美淑姬，可与晤歌。" />
        </el-form-item>
        <el-form-item label="图片链接">
          <el-input v-model="createForm.image_url" placeholder="选填：直接粘贴图片 URL，留空则显示占位" />
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

    <!-- 面料卡片网格：衣冠卡片解剖，图片区定高 + contain 不裁原图 -->
    <div v-loading="loading" class="acc-grid">
      <AccCard v-for="(f, i) in filteredList" :key="f.id" :index="i" :title="f.name"
               :image="f.image_url" :alt="f.name" :meta="f.dynasty_peak" :summary="f.description"
               :no="`${pad(i + 1)} / ${total}`" :volume="f.category" :code="f.code"
               :tags="[f.category, f.raw_material, f.technique].filter(Boolean)"
               :badge="f.created_by || f.source_ref === '用户创建' ? '用户创建' : ''"
               :tone="toneOf(f.category)" link-text="阅面料" @open="openSplit(f)">
        <template #actions>
          <el-button v-if="f.created_by || f.source_ref === '用户创建'" size="small" text type="danger" class="del-btn"
                     @click.stop="removeFabric(f)">删除</el-button>
        </template>
      </AccCard>
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

    <!-- ==================== 详情模式（衣冠卷面排版） ==================== -->
    <template v-else>
      <div class="detail-layout">
        <section class="acc-panel detail-main">
          <div class="detail-head">
            <el-button size="small" @click="$router.push('/fabric')">返回列表</el-button>
            <el-button v-if="detail?.created_by || detail?.source_ref === '用户创建'" size="small" type="danger" plain
                       style="margin-left: auto" @click="removeFabric(detail)">删除面料</el-button>
          </div>

          <!-- 眉标 + 大标题 + 属性行 -->
          <div class="acc-eyebrow">
            <span class="acc-eyebrow-line"></span>
            <span>传统服饰面料</span>
            <span v-if="detail?.code" class="acc-eyebrow-index">名录编号 {{ detail.code }}</span>
          </div>
          <h2 class="acc-detail-title" :class="{ 'is-long': titleLong }">{{ detail?.name }}</h2>
          <div class="acc-detail-meta">
            <span>{{ detail?.category || "类别待考" }}</span>
            <span class="dot"></span>
            <span>{{ detail?.dynasty_peak || "盛行朝代待考" }}</span>
            <span class="dot"></span>
            <span>{{ detail?.raw_material || "原料待考" }}</span>
          </div>

          <!-- 面料实物图 -->
          <div v-if="has('面料实物图')" class="section">
            <AccSecHead :no="secNo('面料实物图')" title="面料实物图" sub="实物 / 传世图像" />
            <div class="relic-gallery">
              <div class="relic-card">
                <img :src="detail.image_url" :alt="`${detail?.name}实物`" loading="lazy" data-lb-native
                     @click="relicLightbox = detail.image_url" @error="onImgError" />
                <p class="relic-source">▲ {{ detail?.name }} · 实物 / 传世图像</p>
              </div>
            </div>
          </div>

          <!-- 工艺示意 -->
          <div v-if="has('工艺示意')" class="section">
            <AccSecHead :no="secNo('工艺示意')" title="工艺示意" sub="完整流程与细节特写" />
            <div class="craft-imgs">
              <div v-if="detail.craft.images.overview" class="craft-img-block">
                <div class="ci-title">完整流程</div>
                <img :src="detail.craft.images.overview" :alt="detail.name + '工艺流程'" class="craft-img" data-lb-native
                     @click="relicLightbox = detail.craft.images.overview" @error="onImgError" />
              </div>
              <div v-if="detail.craft.images.detail" class="craft-img-block">
                <div class="ci-title">细节特写</div>
                <img :src="detail.craft.images.detail" :alt="detail.name + '工艺细节'" class="craft-img" data-lb-native
                     @click="relicLightbox = detail.craft.images.detail" @error="onImgError" />
              </div>
            </div>
          </div>

          <!-- 史料详析 -->
          <div v-if="has('史料详析')" class="section">
            <AccSecHead :no="secNo('史料详析')" title="史料详析" sub="简介与工艺史料" />
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
          <div v-if="has('制作流程')" class="section">
            <AccSecHead :no="secNo('制作流程')" title="制作流程" sub="工序逐条" />
            <div v-for="s in fabricSteps" :key="s.num" class="detail-sec">
              <h4 class="sec-title">{{ s.num_cn ? s.num_cn + " · " : "" }}{{ s.label || s.title }}</h4>
              <p class="sec-body">{{ s.desc || s.title }}</p>
            </div>
          </div>

          <!-- 知识图谱关联 -->
          <div v-if="has('知识图谱关联')" class="section">
            <AccSecHead :no="secNo('知识图谱关联')" title="知识图谱关联" sub="名录字段速览" />
            <div class="graph-nodes">
              <span class="graph-node"><i>类别</i>{{ detail?.category }}</span>
              <span class="graph-node"><i>原料</i>{{ detail?.raw_material }}</span>
              <span class="graph-node"><i>织造技艺</i>{{ detail?.technique }}</span>
              <span class="graph-node"><i>盛行朝代</i>{{ detail?.dynasty_peak }}</span>
              <span class="graph-node"><i>史料出处</i>{{ detail?.source_ref }}</span>
            </div>
          </div>
        </section>

        <aside class="detail-side acc-sticky">
          <div class="acc-aside-card">
            <AccSectionHead title="基础信息" size="sm" />
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="类别">{{ detail?.category || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="盛行朝代">{{ detail?.dynasty_peak || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="原料">{{ detail?.raw_material || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="织造技艺">{{ detail?.technique || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="史料出处">{{ detail?.source_ref || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="名录编号">{{ detail?.code || "待考" }}</el-descriptions-item>
              <el-descriptions-item label="工艺资料">
                <template v-if="detail?.craft">{{ detail.craft.name || "已收录" }}</template>
                <template v-else>待考</template>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="acc-aside-card">
            <AccSectionHead title="诗文 · 古文" size="sm" />
            <div v-if="detail?.poems?.length" class="detail-poems">
              <div v-for="(p, i) in detail.poems" :key="i" class="poem-item">
                <span v-if="p.src" class="poem-src">{{ p.src }}</span>
                <p>{{ p.text }}</p>
                <a v-if="p.url" :href="p.url" target="_blank" rel="noopener" class="poem-link">检索 ↗</a>
              </div>
            </div>
            <p v-else class="body-text">暂无诗文收录</p>
          </div>
          <div class="acc-aside-card">
            <AccSectionHead title="工艺简介" size="sm" />
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
import AccCard from "@/components/acc/AccCard.vue";
import AccSectionHead from "@/components/acc/AccSectionHead.vue";
import AccSecHead from "@/components/acc/AccSecHead.vue";
import { pad, toneOf } from "@/components/acc/accMeta";
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
  historyNote: "", stepsText: "", poemsText: "",
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
  createForm.value = { name: "", category: "", raw_material: "", dynasty_peak: "", technique: "", description: "", historyNote: "", stepsText: "", source_ref: "", poemsText: "", image_url: "" };
  createVisible.value = true;
}

async function submitCreate() {
  const f = createForm.value;
  if (!f.name.trim()) { ElMessage.warning("请填写面料名称"); return; }
  if (!f.category) { ElMessage.warning("请选择类别"); return; }
  createLoading.value = true;
  try {
    // 制作流程：每行 "步骤|说明"
    const steps = f.stepsText.split("\n").map((s: string) => s.trim()).filter(Boolean)
      .map((line: string, i: number) => {
        const m = line.split(/[|｜]/);
        return { num_cn: "①②③④⑤⑥⑦⑧⑨⑩"[i] || `${i + 1}`, label: (m[0] || "").trim(), desc: (m.slice(1).join("|") || "").trim() };
      }).filter((s: any) => s.label);
    // 诗文：每行 "出处|引文"
    const poems = f.poemsText.split("\n").map((s: string) => s.trim()).filter(Boolean)
      .map((line: string) => {
        const m = line.split(/[|｜]/);
        return { src: (m[0] || "").trim(), text: (m.slice(1).join("|") || "").trim(), url: "" };
      }).filter((p: any) => p.src && p.text);
    const craft = { name: "", history_note: f.historyNote || "", steps, images: {} };
    const res: any = await createFabric({ ...f, craft, poems });
    if (res && res.error) { ElMessage.error(res.error); return; }
    createVisible.value = false;
    ElMessage.success(`面料「${res.name}」已创建`);
    await load();
    loadUserWorks();
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

/* 详情分节：条件区块隐藏时节号仍连续 */
const detailSections = computed<string[]>(() => {
  const d = detail.value;
  const out: string[] = [];
  if (d?.image_url) out.push("面料实物图");
  if (d?.craft?.images && (d.craft.images.overview || d.craft.images.detail)) out.push("工艺示意");
  out.push("史料详析");
  if (fabricSteps.value.length) out.push("制作流程");
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
/* 容器宽度与调色由 acc-scope.css 统一接管，这里只补本页独有的版式 */
.fabric-page {
  padding: 20px 0 40px;
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
.user-works { margin: 0 0 26px; }
.uw-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 10px; flex-wrap: wrap; }
.uw-tools { display: flex; align-items: center; gap: 8px; }
.uw-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 10px; }
.uw-card { border: 1px solid var(--acc-line, #e6dcc8); border-radius: 8px; overflow: hidden; cursor: pointer; background: var(--acc-card-solid, #fffdf8); transition: box-shadow .2s, border-color .2s; }
.uw-card:hover { box-shadow: 0 6px 18px rgba(90, 60, 30, .14); border-color: rgba(201, 162, 39, .5); }
.uw-card:focus-visible { outline: 2px solid var(--acc-gold, #c9a227); outline-offset: 2px; }
.uw-card img { width: 100%; aspect-ratio: 3 / 2; height: auto; object-fit: contain; display: block; background: #f4ead9; }
.uw-thumb { width: 100%; aspect-ratio: 3 / 2; display: flex; align-items: center; justify-content: center; font-size: 12px; color: var(--acc-ink-3, #94836d); background: #f4ead9; }
.uw-info { padding: 8px 10px; }
.uw-info h4 { margin: 0 0 3px; font-size: 14px; color: var(--acc-ink, #3a2f24); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.uw-info p { margin: 1px 0; font-size: 12px; color: var(--acc-ink-3, #94836d); }
.uw-info .uw-desc { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.uw-empty-box { grid-column: 1 / -1; padding: 22px 0; }

/* ============ 详情模式（衣冠卷面：主栏 + 右栏） ============ */
.detail-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 44px; align-items: start; }
.detail-main { min-width: 0; }
.detail-head { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 22px; }
.body-text { margin: 10px 0 0; color: var(--acc-ink-2, #5c4c3a); font-size: 13.5px; line-height: 1.85; }
.detail-side { display: flex; flex-direction: column; min-width: 0; }
.graph-nodes { display: flex; flex-wrap: wrap; gap: 8px; }
.graph-node { border: 1px solid var(--acc-line, #e6dcc8); background: var(--acc-card-solid, #fffdf8); border-radius: 6px; padding: 4px 10px; font-size: 13px; color: var(--acc-ink-2, #5c4c3a); }
.graph-node i { font-style: normal; color: var(--acc-red, #7a221c); margin-right: 6px; }
.section { margin-top: 30px; }
.relic-gallery { margin-top: 12px; }
.relic-card { display: inline-block; max-width: 420px; }
.relic-card img { width: 100%; max-height: 340px; object-fit: contain; border-radius: 8px; border: 1px solid var(--acc-line, #e6dcc8); box-shadow: 0 8px 20px rgba(90, 60, 30, 0.14); cursor: zoom-in; background: var(--acc-card-solid, #fffdf8); }
.relic-source { font-size: 12px; color: var(--acc-ink-3, #94836d); margin-top: 6px; line-height: 1.6; letter-spacing: 1px; }
.detail-sec { border-left: 3px solid var(--acc-gold, #c9a227); background: rgba(201, 162, 39, 0.06); border-radius: 0 8px 8px 0; padding: 10px 14px; margin-top: 10px; }
.sec-title { margin: 0 0 6px; font-size: 14px; color: var(--acc-red, #7a221c); letter-spacing: 1px; }
.sec-body { margin: 0; color: var(--acc-ink-2, #5c4c3a); line-height: 1.85; font-size: 13.5px; }
.craft-imgs { margin-top: 12px; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.craft-img-block { border: 1px solid var(--acc-line, #e6dcc8); border-radius: 8px; overflow: hidden; background: var(--acc-card-solid, #fffdf8); }
.ci-title { font-size: 12.5px; color: var(--acc-red, #7a221c); padding: 6px 10px; border-bottom: 1px dashed var(--acc-line, #e6dcc8); letter-spacing: 1px; }
.craft-img { width: 100%; max-height: 300px; object-fit: contain; display: block; background: var(--acc-card-solid, #fffdf8); cursor: zoom-in; }
.detail-poems { margin-top: 10px; display: flex; flex-direction: column; gap: 10px; }
.poem-item { border-left: 2px solid var(--acc-red, #7a221c); padding: 6px 10px; background: rgba(122, 34, 28, 0.04); border-radius: 0 6px 6px 0; }
.poem-src { font-size: 11.5px; color: var(--acc-red, #7a221c); }
.poem-item p { margin: 3px 0; font-size: 12.5px; line-height: 1.7; color: var(--acc-ink-2, #5c4c3a); }
.poem-link { font-size: 12px; color: var(--acc-red, #7a221c); text-decoration: none; }

@media (max-width: 1023px) {
  .detail-layout { gap: 24px; }
}

@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
}
</style>
