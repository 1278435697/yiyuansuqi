<template>
  <div class="archive-page">
    <!-- 档案列表模式 -->
    <template v-if="!currentId">
      <PageHero title="衣溯AI · 历代服饰档案" kicker="ARCHIVE · 华夏衣冠" sub="从出土实物到传世文献，每一件服饰都有迹可循、有史可查" seal="档" />
      <div class="section-head">
        <div class="filters anim-rise" style="animation-delay: .5s">
          <el-select v-model="dynasty" placeholder="按朝代" clearable size="small" style="width: 120px" @change="load">
            <el-option v-for="e in eras" :key="e.name" :label="e.name" :value="e.name" />
          </el-select>
          <el-select v-model="category" placeholder="按类别" clearable size="small" style="width: 120px" @change="load">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索服饰" clearable size="small" style="width: 170px" @keyup.enter="load" />
          <el-button size="small" type="primary" plain :loading="webLoading" @click="doWebSearch">全网搜索</el-button>
          <el-button size="small" type="danger" plain @click="openCreate">＋ 创建档案</el-button>
        </div>
      </div>

      <!-- 创建档案弹窗 -->
      <el-dialog v-model="createVisible" title="自主创建服饰档案" width="560px" destroy-on-close>
        <el-form :model="createForm" label-width="84px" size="small">
          <el-form-item label="服饰名称" required>
            <el-input v-model="createForm.name" placeholder="如：齐胸襦裙" maxlength="50" />
          </el-form-item>
          <el-form-item label="朝代" required>
            <el-select v-model="createForm.dynasty" placeholder="选择朝代" style="width: 100%">
              <el-option v-for="d in allEras" :key="d" :label="d" :value="d" />
            </el-select>
          </el-form-item>
          <el-form-item label="类别">
            <el-select v-model="createForm.category" placeholder="选择类别" style="width: 100%">
              <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="穿着者">
            <el-input v-model="createForm.wearer" placeholder="如：唐代仕女" />
          </el-form-item>
          <el-form-item label="来源类型">
            <el-select v-model="createForm.source_type" style="width: 100%">
              <el-option v-for="s in sourceOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="面料">
            <el-input v-model="createForm.fabric" placeholder="如：罗 · 纱 · 绢" />
          </el-form-item>
          <el-form-item label="纹样">
            <el-input v-model="createForm.pattern" placeholder="如：宝相花 · 缠枝莲" />
          </el-form-item>
          <el-form-item label="服色">
            <el-input v-model="createForm.color" placeholder="如：绯红 / 月白" />
          </el-form-item>
          <el-form-item label="图片链接">
            <el-input v-model="createForm.image_url" placeholder="选填：直接粘贴图片 URL，留空则显示占位" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="createForm.description" type="textarea" :rows="3"
                      placeholder="形制、史料依据、参考来源等（建议附出处）" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button size="small" @click="createVisible = false">取消</el-button>
          <el-button size="small" type="danger" :loading="createLoading" @click="submitCreate">保存档案</el-button>
        </template>
      </el-dialog>

      <!-- 用户作品：其他用户创建的服饰档案（自社区迁移） -->
      <div class="user-works ys-card">
        <div class="uw-head">
          <h3 class="ys-title">用户作品 · 服饰档案</h3>
          <div class="uw-tools">
            <el-input v-model="uwKeyword" placeholder="搜索用户档案…" size="small" clearable style="width: 180px"
                      @keyup.enter="loadUserWorks" @clear="loadUserWorks" />
            <el-button size="small" @click="loadUserWorks">搜索</el-button>
          </div>
        </div>
        <div class="uw-grid">
          <div v-for="c in userWorks" :key="c.id" class="uw-card" @click="$router.push(`/archive/${c.id}`)">
            <img v-if="c.image_url" :src="c.image_url" :alt="c.name" loading="lazy" />
            <div v-else class="uw-thumb">暂无实物图</div>
            <div class="uw-info">
              <h4>{{ c.name }}</h4>
              <p>{{ c.dynasty }} · {{ c.category }}</p>
              <p class="uw-desc">{{ c.description }}</p>
            </div>
          </div>
          <div v-if="!userWorks.length" class="ys-empty uw-empty-box">{{ uwKeyword ? "未找到匹配的用户档案" : "暂无用户创建的档案，点击右上角「＋ 创建档案」创建第一条吧" }}</div>
        </div>
      </div>

      <!-- 全网搜索结果（联动外部搜索） -->
      <div v-if="webResults.length" class="ys-card web-results">
        <div class="web-head">
          <h3 class="ys-title">全网结果 · “{{ webQuery }}”</h3>
          <el-button size="small" text type="primary" @click="webResults = []">收起</el-button>
        </div>
        <a v-for="r in webResults" :key="r.url" class="web-item" :href="r.url" target="_blank" rel="noopener">
          <div class="web-item-title">{{ r.title }}</div>
          <div class="web-item-src">{{ r.source }}</div>
          <p class="web-item-snippet">{{ r.snippet }}</p>
        </a>
      </div>
      <div v-else-if="webError" class="ys-card web-results">
        <p class="ys-muted">{{ webError }}</p>
      </div>

      <div v-loading="loading" class="costume-grid">
        <div v-for="c in costumes" :key="c.id" class="costume-card ys-card" @click="openSplit(c)">
          <div class="card-img">
            <img v-if="c.image_url" :src="c.image_url" :alt="c.name" loading="lazy" />
            <div v-else class="img-placeholder">暂无图</div>
            <span class="dynasty-badge">{{ c.dynasty }}</span>
            <span v-if="c.created_by" class="user-badge">用户创建</span>
          </div>
          <div class="card-body">
            <div class="card-head">
              <h3>{{ c.name }}</h3>
              <el-button v-if="c.source_type === '用户创建'" size="small" text type="danger" class="del-btn" @click.stop="removeCostume(c)">删除</el-button>
            </div>
            <p class="costume-desc">{{ c.description || "（暂无简介）" }}</p>
            <div class="costume-meta">
              <span>{{ c.category }}</span>
              <span>{{ c.fabric || "面料待考" }}</span>
              <span>{{ c.source_type }}</span>
            </div>
            <div class="ys-tag" v-for="p in (c.pattern || '').split('·').slice(0, 2)" :key="p" v-show="p">{{ p }}</div>
          </div>
        </div>
        <div v-if="!loading && !costumes.length" class="ys-empty">暂无档案，稍后接入数据后展示</div>
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

    <!-- 档案详情模式（含 AI 第一人称对话 + 史料详析 + 权威实例图） -->
    <template v-else>
      <div class="detail-layout">
        <section class="ys-card detail-main">
          <div class="detail-head">
            <el-button size="small" @click="$router.push('/archive')">返回列表</el-button>
            <h2>{{ detail?.name }} <span class="dynasty">{{ detail?.dynasty }} · {{ detail?.category }}</span></h2>
            <el-button v-if="detail?.source_type === '用户创建'" size="small" type="danger" plain style="margin-left: auto" @click="removeCostume(detail)">删除档案</el-button>
          </div>

          <el-descriptions :column="2" border size="small" style="margin: 14px 0">
            <el-descriptions-item label="穿着者">{{ detail?.wearer || "待考" }}</el-descriptions-item>
            <el-descriptions-item label="来源类型">{{ detail?.source_type }}</el-descriptions-item>
            <el-descriptions-item label="面料">{{ detail?.fabric }}</el-descriptions-item>
            <el-descriptions-item label="纹样">{{ detail?.pattern }}</el-descriptions-item>
            <el-descriptions-item label="服色">{{ detail?.color }}</el-descriptions-item>
            <el-descriptions-item label="出土文物">
              <template v-if="detail?.relic">{{ detail.relic.name }}（{{ detail.relic.location }} · {{ detail.relic.museum }}）</template>
              <template v-else>待考</template>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 权威实例图 -->
          <template v-if="detailData.relicImage">
            <h3 class="ys-title">权威实例图</h3>
            <div class="relic-gallery">
              <div class="relic-card">
                <img :src="detailData.relicImage" :alt="`${detail?.name}权威实例`" loading="lazy"
                     @click="relicLightbox = detailData.relicImage" />
                <p class="relic-source">▲ {{ detailData.relicCaption }}</p>
              </div>
            </div>
          </template>

          <h3 class="ys-title">史料详析</h3>
          <div class="detail-sections">
            <div v-for="sec in detailData.sections" :key="sec.title" class="detail-sec">
              <h4 class="sec-title">{{ sec.title }}</h4>
              <p class="sec-body">{{ sec.body }}</p>
            </div>
          </div>

          <h3 class="ys-title">形制说明</h3>
          <p class="body-text">{{ detail?.description || "（暂无形制说明）" }}</p>

          <h3 class="ys-title">知识图谱关联</h3>
          <div class="graph-nodes">
            <span v-for="(r, i) in detail?.relations || []" :key="i" class="graph-node">
              <i>{{ r.type }}</i>{{ r.value }}
            </span>
          </div>
          <p v-if="!detail?.relations?.length" class="body-text">关联数据待补录</p>
        </section>

        <aside class="detail-side">
          <div class="ys-card chat-card">
            <h3 class="ys-title">AI 第一人称对话</h3>
            <div class="chat-box" ref="chatBox">
              <div v-for="(m, i) in messages" :key="i" class="chat-msg" :class="m.role">
                <div class="chat-bubble">{{ m.content }}</div>
                <div v-if="m.role === 'assistant' && m.source" class="chat-source">溯源：{{ m.source }}</div>
              </div>
              <div v-if="chatLoading" class="chat-typing">正在检索史料并作答…</div>
            </div>
            <div class="chat-input">
              <el-input v-model="question" placeholder="问它：你穿在身上是什么感觉？" size="small"
                        @keyup.enter="sendChat" :disabled="!detail" />
              <el-button type="primary" size="small" :loading="chatLoading" @click="sendChat">提问</el-button>
            </div>
            <div class="chat-suggests">
              <el-tag v-for="q in suggests" :key="q" size="small" class="suggest" @click="question = q">{{ q }}</el-tag>
            </div>
          </div>
        </aside>
      </div>

      <!-- 实例图放大 -->
      <div v-if="relicLightbox" class="lightbox" @click="relicLightbox = null">
        <img :src="relicLightbox" alt="实例图放大" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fetchCostumes, fetchCostumeDetail, fetchEras, chatWithCostume, fetchArchiveWebSearch, createCostume, deleteCostume } from "@/api/modules";
import PageHero from "@/components/PageHero.vue";
import SplitReveal from "@/components/SplitReveal.vue";
import { ElMessage, ElMessageBox } from "element-plus";

const route = useRoute();
const router = useRouter();

const costumes = ref<any[]>([]);
const detail = ref<any>(null);

/* 点击卡片：主图从中心放大、分裂翻转成三张素材卡片 */
const splitVisible = ref(false);
const splitTitle = ref("");
const splitCards = ref<any[]>([]);
let splitTarget: any = null;
function openSplit(c: any) {
  splitTarget = c;
  splitTitle.value = `${c.name} · 素材档案`;
  const dd = COSTUME_DETAILS[c.name] || {};
  const ex = EXTRA_IMAGES[c.name] || {};
  const sections = dd.sections || [];
  // 去重取图：三张卡绝不重复，池子充足时优先"实例→形制→史料"
  const used: string[] = [];
  const pick = (...cands: Array<string | undefined>) => {
    for (const cnd of cands) {
      if (cnd && !used.includes(cnd)) { used.push(cnd); return cnd; }
    }
    return undefined;
  };
  splitCards.value = [
    {
      image: pick(dd.relicImage, c.image_url, ex.structure, ex.literature),
      kicker: "权威实例图",
      title: c.name,
      text: dd.relicCaption || "出土实物 / 传世文献对应的权威实例。",
    },
    {
      image: pick(ex.structure, ex.literature, dd.relicImage, c.image_url),
      kicker: "形制结构",
      title: "形制 · 面料 · 纹样",
      text: c.description || "（暂无形制说明）",
      list: [
        { label: "穿着者", value: c.wearer || "待考" },
        { label: "面料", value: c.fabric || "待考" },
        { label: "纹样", value: c.pattern || "待考" },
        { label: "服色", value: c.color || "待考" },
      ],
    },
    {
      image: pick(ex.literature, ex.structure, c.image_url, dd.relicImage),
      kicker: "史料详析",
      title: "考据文本",
      text: (sections[0]?.body || "史料整理中。").slice(0, 80) + (sections.length ? "…" : ""),
      list: sections.slice(0, 3).map((s: any) => ({ label: s.title, value: s.body.slice(0, 26) + "…" })),
    },
  ];
  splitVisible.value = true;
}
function onSplitSelect() {
  splitVisible.value = false;
  if (splitTarget) router.push(`/archive/${splitTarget.id}`);
}
const eras = ref<any[]>([]);
const categories = ["上衣", "下裳", "首服", "配饰", "袍服"];
const categoryOptions = [...categories, "袍服"];
const sourceOptions = ["用户创建", "出土", "传世", "文献", "图像"];
const allEras = ["上古", "先秦", "秦汉", "魏晋", "隋唐", "宋", "元", "明", "清"];
const dynasty = ref("");
const category = ref("");
const keyword = ref("");
const loading = ref(false);
/* 用户作品：其他用户创建的服饰档案（自社区迁移） */
const uwKeyword = ref("");
const userWorks = ref<any[]>([]);
async function loadUserWorks() {
  const kw = uwKeyword.value.trim();
  try {
    const d: any = await fetchCostumes({ source_type: "用户创建", keyword: kw || undefined, page: 1, page_size: 9 });
    userWorks.value = d.items || [];
  } catch { /* 忽略 */ }
}
/* 自主创建档案 */
const createVisible = ref(false);
const createLoading = ref(false);
const createForm = ref({
  name: "", dynasty: "", category: "", wearer: "",
  source_type: "用户创建", fabric: "", pattern: "", color: "",
  description: "", image_url: "",
});
function openCreate() {
  const token = localStorage.getItem("yisu_token") || localStorage.getItem("token") || "";
  if (!token) {
    ElMessage.warning("请先登录，再创建档案");
    router.push("/login");
    return;
  }
  createForm.value = { name: "", dynasty: "", category: "", wearer: "", source_type: "用户创建", fabric: "", pattern: "", color: "", description: "", image_url: "" };
  createVisible.value = true;
}
async function submitCreate() {
  const f = createForm.value;
  if (!f.name.trim()) { ElMessage.warning("请填写服饰名称"); return; }
  if (!f.dynasty) { ElMessage.warning("请选择朝代"); return; }
  createLoading.value = true;
  try {
    const res: any = await createCostume(f);
    if (res && res.error) { ElMessage.error(res.error); return; }
    createVisible.value = false;
    ElMessage.success(`档案「${res.name}」已创建`);
    await load();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "创建失败，请确认已登录");
  } finally {
    createLoading.value = false;
  }
}
async function removeCostume(c: any) {
  try {
    await ElMessageBox.confirm(`确定删除档案「${c.name}」吗？删除后不可恢复。`, "删除确认", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch { return; }
  try {
    const res: any = await deleteCostume(c.id);
    if (res && res.error) { ElMessage.error(res.error); return; }
    ElMessage.success("档案已删除");
    await load();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.response?.data?.error || "删除失败，请确认已登录");
  }
}
/* 全网搜索联动 */
const webResults = ref<any[]>([]);
const webLoading = ref(false);
const webError = ref("");
const webQuery = ref("");
const currentId = ref<number | null>(null);
const messages = ref<any[]>([]);
const question = ref("");
const chatLoading = ref(false);
const chatBox = ref<HTMLDivElement>();
const relicLightbox = ref<string | null>(null);
const suggests = ["你穿在身上是什么感觉？", "你代表了哪个朝代的审美？", "你的出土溯源是怎样的？", "你的纹样有什么寓意？"];

/* ===== 史料详析配置（考据文本 + 权威实例图） ===== */
const COSTUME_DETAILS: Record<string, any> = {
  "深衣": {
    relicImage: "/images/relics/relic_xianqin_shenyi.jpg",
    relicCaption: "战国素纱绵袍（垂胡袖直裾深衣） · 湖北荆州马山一号楚墓出土 · 荆州博物馆藏（图源：湖北日报）",
    sections: [
      { title: "形制结构", body: "深衣为上衣下裳连属的长衣，交领右衽，大襟（曲裾或直裾）掩覆，腰部以带束系。衣长“短毋见肤，长毋被土”，袖口宽博而收敛。先秦时期为士大夫阶层常服与礼服。" },
      { title: "出土实物", body: "湖北江陵马山一号楚墓（战国晚期）出土大量丝织衣袍，是先秦深衣形制的重要实物证据。其中凤鸟纹绣绢䋺衣以紫红绢为地、凤鸟相蟠纹刺绣为饰，印证《楚辞》所载“被文服纤”的华美。" },
      { title: "工艺特征", body: "面料以丝、麻为主，纹样见黻纹、回纹，衣缘以锦镶边。楚墓织物刺绣针法细密，色彩以赭红、玄色为主，体现“玄端”礼服的庄重。" },
      { title: "礼制含义", body: "《礼记·深衣》言其“可以为文，可以为武，可以傧相，可以治军旅”，深衣是集礼制、实用与身份标识于一体的先秦服饰。" },
    ],
  },
  "素纱单衣": {
    relicImage: "/images/relics/relic_han_susha.jpg",
    relicCaption: "西汉素纱单衣（襌衣） · 长沙马王堆一号汉墓（辛追墓）出土 · 湖南博物院藏",
    sections: [
      { title: "形制结构", body: "交领右衽、直裾式单衣（襌衣），无衬里。衣长160厘米，通袖长195厘米，重仅48克，薄如蝉翼、轻若云雾，是中国首批禁止出国（境）展览文物。" },
      { title: "出土实物", body: "1972年长沙马王堆一号汉墓（西汉长沙国丞相利苍之妻辛追墓）出土。同墓还出土曲裾式素纱单衣、印花敷彩纱丝绵袍等大量丝织品。" },
      { title: "工艺特征", body: "衣料为平纹方孔素纱，由汉代三眠蚕所吐之丝织成（单丝仅10.2—11.3旦），经纬密度极细，体现西汉缫丝织造的巅峰水平。" },
      { title: "穿着场合", body: "素纱单衣轻薄透体，一般罩于深衣或袍服之外作“禅衣”穿着；其轻盈质感亦见于长沙国贵族墓葬壁画与文献记载。" },
    ],
  },
  "曲裾深衣": {
    relicImage: "/images/relics/relic_han_quju_v2.jpg",
    relicCaption: "西汉朱红菱纹罗丝绵袍（曲裾） · 长沙马王堆一号汉墓出土 · 湖南博物院藏",
    sections: [
      { title: "形制结构", body: "曲裾深衣为绕襟长衣，衣襟自腋下向身后缠绕数周再回掖，下裳宽阔曳地，行走时衣裾飘举。汉代曲裾袍为贵族礼服，等级标识鲜明。" },
      { title: "出土实物", body: "马王堆一号汉墓出土素纱曲裾式襌衣与朱红菱纹罗丝绵袍，均为曲裾样式代表；朱红菱纹罗丝绵袍衣身朱红、缘边浅米，体现“尚红”的汉代服色取向。" },
      { title: "工艺特征", body: "面料以缣、绮、罗、锦为主，纹样见云气纹、兽纹与菱纹。马王堆织品提花、印花、敷彩工艺并存，织造技术极为成熟。" },
      { title: "礼制含义", body: "《后汉书·舆服志》载汉代服制等级分明，曲裾深衣的衣长、缘色、纹样均与穿着者身份相应。" },
    ],
  },
  "宽衫大袖": {
    relicImage: "/images/relics/relic_weijin_kuanshan.jpg",
    relicCaption: "《洛神赋图》局部（宋摹本，保留魏晋画风） · 顾恺之原作 · 故宫博物院藏本",
    sections: [
      { title: "形制结构", body: "魏晋名士崇尚宽衣博带：宽衫大袖、袒胸露腹、高冠博带，衣身宽博、袖口广大，行走时衣袂飘举，体现“得意忘形”的玄学审美。" },
      { title: "图像证据", body: "顾恺之《洛神赋图》中的曹植与名士形象均着宽衫大袖；《世说新语》载名士服章“宽衣博带，从容自若”，是魏晋风度的直观写照。" },
      { title: "工艺特征", body: "面料以纱、罗、绢为主，素白、浅青为主色，纹样见忍冬纹、莲花纹，受佛教美术东传影响。" },
      { title: "审美变迁", body: "由汉之庄重转为魏晋之飘逸，服饰的松垮宽博既是审美自觉，也是士人对抗礼法束缚的象征。" },
    ],
  },
  "大袖襦裙": {
    relicImage: "/images/relics/relic_tang_ruqun.jpg",
    relicCaption: "《簪花仕女图》局部 · 唐周昉绘 · 辽宁省博物馆藏",
    sections: [
      { title: "形制结构", body: "唐代女性盛装为高腰束胸襦裙：裙腰高束于胸际，下裳曳地多褶；外罩大袖罗纱衫，肩绕披帛，手臂饰臂钏。大袖衫袖宽可达1.3米以上。" },
      { title: "图像证据", body: "周昉《簪花仕女图》中贵妇身着大袖纱罗衫、高腰裙与披帛，是盛唐宫廷女性服饰的典型写照；唐墓壁画供养人形象亦同此式。" },
      { title: "工艺特征", body: "面料以锦、绫、纱为主，纹样见宝相花、联珠纹，服色绯红、明黄、靛青并重，织染工艺与外来纹样交融。" },
      { title: "开放风气", body: "唐代女子裙装高束袒胸、薄纱透体，是历代少见的开放着装；这与李唐王朝胡汉交融、丝路通达的时代背景直接相关。" },
    ],
  },
  "圆领袍": {
    relicImage: "/images/relics/relic_tang_yuanling.jpg",
    relicCaption: "《步辇图》局部（唐太宗与使臣着圆领袍） · 唐阎立本绘 · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "圆领袍（团领袍）为隋唐男子常服：圆领窄袖（或宽袖）、腰间束带，下摆加横襕者称“襕袍”。除祭祀典礼外，士庶官宦平时均可穿着。" },
      { title: "图像证据", body: "阎立本《步辇图》中唐太宗及随行官员皆着幞头圆领袍，连皇帝也不例外；吐番使者禄东赞着织锦袍，见证丝路织锦的传播。" },
      { title: "来源与演变", body: "圆领袍由胡服改制而来，吸收了鲜卑、中亚服饰的窄袖束带元素，经北周、隋定型，唐代成为最具代表性的男装。" },
      { title: "纹样面料", body: "官员袍色依品级（绯、紫、青、绿），面料以绫、罗为主，纹样见联珠纹、团窠纹等中亚传入的图案。" },
    ],
  },
  "褙子": {
    relicImage: "/images/relics/relic_song_beizi.jpg",
    relicCaption: "南宋花罗绣彩花边单衣（合领对襟） · 福州南宋黄昇墓出土 · 国家一级文物 · 福建省博物馆藏",
    sections: [
      { title: "形制结构", body: "宋代褙子（背子）为直领（合领）对襟、两侧开衩的长衣，衣长及膝至足，无袪或系带，穿着时露出里衣。是宋代男女通用的典型外衣。" },
      { title: "出土实物", body: "福州南宋黄昇墓出土服饰逾300件，其中花罗绣彩花边单衣为合领对襟、无系带，衣身绣梅花、缠枝牡丹、芙蓉、山茶、荷花等纹样，为国家一级文物。" },
      { title: "工艺特征", body: "面料以罗、纱、绢为主，宋代罗织造精细；边饰以绣、妆缎、印花、印金等多种工艺镶缀，整体清雅含蓄，体现“理学风范”的审美。" },
      { title: "穿着场合", body: "《宋史·舆服志》载命妇以褙子为常服，未嫁女子、侍妾亦常着之；皇后受册后谒庙、节庆宴饮亦有穿褙子的记载。" },
    ],
  },
  "质孙服": {
    relicImage: "/images/relics/relic_yuan_zhisun.jpg",
    relicCaption: "元代织金袍服（博物馆展陈） · 质孙服为元代宫廷一色服制",
    sections: [
      { title: "形制结构", body: "质孙服（一色服）为元代宫廷大宴的官服：交领右衽、窄袖束腰，腰以下打褶或作裙状，与蒙古骑射生活方式相应。" },
      { title: "史料记载", body: "《元史·舆服志》详载质孙服之制：天子与百官在大宴（质孙宴）时“衣冠同色”，按等级服用不同色质孙，一日一换、同色者谓之“质孙”。" },
      { title: "工艺特征", body: "面料以纳石失（织金锦）为贵，金线织入锦中，辅以八宝纹、云肩纹；黄金织造是蒙元服饰最鲜明的技术标志。" },
      { title: "文化交融", body: "质孙服融合蒙古传统与西域织金工艺，见证欧亚大陆丝路贸易与工艺交流的鼎盛。" },
    ],
  },
  "马面裙": {
    relicImage: "/images/relics/relic_ming_maqun.jpg",
    relicCaption: "蓝色缠枝四季花卉纹织金妆花缎马面裙 · 明 · 长88厘米 · 山东博物馆藏（图源：清华大学美术学院）",
    sections: [
      { title: "形制结构", body: "马面裙两侧打褶、前后中幅平整如“马面”，裙腰双层（以棉布为腰），两端系带。穿时裙门前后相叠，行走时两侧褶裥自然展开。" },
      { title: "出土实物", body: "明代马面裙出土与传世较多：山东博物馆藏蓝色缠枝四季花卉纹织金妆花缎马面裙（长88厘米、腰围104厘米）；江苏明嘉靖徐蕃夫妇墓出土朵梅纹花缎马面裙（裙身左右各打6褶）；定陵孝端皇后棺内亦出土妆花马面裙。" },
      { title: "工艺特征", body: "马面裙以妆花缎、织金缎为常见面料，“妆花”为彩色纬纱通梭或短梭显花的织造技法；裙身饰缠枝莲、龙凤、海水江崖等纹样，织金工艺繁密华美。" },
      { title: "流行与等级", body: "马面裙上承宋代裙制、下启清代裙式，是明代女性最具代表性的裙装；织金妆花者等级较高，多属赐服或命妇所着。" },
    ],
  },
  "旗装": {
    relicImage: "/images/relics/relic_qing_qizhuang.jpg",
    relicCaption: "《孝贤纯皇后朝服像》 · 清乾隆 · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "清代旗装为满族服饰体系：圆领、立领盘扣、直身窄袖（礼服加马蹄袖），袍身直筒，外罩褂、坎肩。满汉服饰并存，旗装是清代最具代表性的女装。" },
      { title: "图像证据", body: "故宫博物院藏《孝贤纯皇后朝服像》中，皇后着明黄朝服、披领、朝珠、护腕，饰龙纹与海水江崖纹，规制森严，是清代宫廷服饰的权威图像。" },
      { title: "工艺特征", body: "面料以绸、缎、缂丝为主，纹样见团花纹、龙纹；缂丝织造通经断纬，色彩富丽，工艺登峰造极。" },
      { title: "礼制等级", body: "清代服色与纹样严格按等级：明黄为帝后专用，皇子、亲王递减；《皇朝礼器图式》系统记载清代冠服制度。" },
    ],
  },
  "上衣下裳": {
    relicImage: "https://aka.doubaocdn.com/s/uDjHyPS6dU",
    relicCaption: "马山一号楚墓出土对襟款服饰 · 荆州博物馆藏（华夏上衣下裳之制早期实物佐证）",
    sections: [
      { title: "形制结构", body: "上衣下裳为华夏衣制最古老的组合：上衣象天、下裳象地，上衣短而合体、下裳长而曳地，腰间束带。后世深衣、襦裙、袄裙等一切服装形态皆由此演化。" },
      { title: "史料记载", body: "《周易·系辞》载“黄帝尧舜垂衣裳而天下治”；《尚书·益稷》载“予欲观古人之象，日月星辰山龙华虫作会”。上衣下裳被视为“垂衣裳而治”的礼乐文明起点。" },
      { title: "工艺特征", body: "上古衣料以葛、麻、兽皮为主，后渐用丝帛。纹样见云雷纹、黻纹，以玄（黑）为上、黄（土）为贵，染织工艺雏形于此成型。" },
      { title: "礼制含义", body: "上衣下裳确立“衣—裳—带—佩”的着装秩序，成为礼制“正名”的一部分；《礼记》反复申说衣冠之制与尊卑等级的关系。" },
    ],
  },
  "冕服": {
    relicImage: "/images/relics/relic_xianqin_mianfu.jpg",
    relicCaption: "《兴献帝画像》 · 穿十二团龙十二章衮服 · 明代帝王画像（冕服十二章之制承先秦）",
    sections: [
      { title: "形制结构", body: "冕服为帝王最高礼服：玄衣纁裳（上衣黑、下裳赤黄），腰束大带，首服为冕（冠上覆板前后垂旒）。《周礼》定“六冕”之制，依祭祀对象不同而有所降杀。" },
      { title: "史料记载", body: "《周礼·司服》载“王之吉服，祀昊天上帝则服大裘而冕”；东汉明帝依据古制恢复十二章纹冕服。明兴献帝画像所穿十二团龙十二章衮服即沿此制。" },
      { title: "十二章纹", body: "十二章：日、月、星辰、山、龙、华虫（雉）、宗彝、藻、火、粉米、黼、黻，各象其义（如日月光辉、山镇稳重、龙能变化），是华夏服饰纹样体系的最高等级。" },
      { title: "礼制含义", body: "冕服将“服—礼—政”合一：天子祭天地、享先王、朝诸侯皆服冕，冕旒数量与章纹多寡是君臣等级的直接标尺。" },
    ],
  },
  "凤鸟纹绣绢䋺衣": {
    relicImage: "/images/relics/relic_xianqin_fengniaoxiu.jpg",
    relicCaption: "战国一凤一龙相蟠纹绣紫红绢单衣 · 马山一号楚墓出土 · 荆州博物馆藏",
    sections: [
      { title: "形制结构", body: "战国楚式衣袍：交领右衽、大袖，衣缘以锦镶边，衣身绣凤鸟相蟠纹。与马山一号楚墓出土的龙凤纹绣绢䋺衣同属“衣被天下”的楚织绣精品。" },
      { title: "出土实物", body: "湖北江陵马山一号楚墓（战国晚期，约公元前300年）出土衣衾19件、绣品37件，其中凤鸟纹绣绢䋺衣以紫红绢为地、凤鸟与蟠螭交缠刺绣，色彩斑斓。" },
      { title: "工艺特征", body: "楚墓绣品以锁绣针法为主，纹样曲线流转；锦缘用提花织机织出，色彩赭红、玄褐相间，印证《楚辞》“被文服纤、丽而不奇”的记载。" },
      { title: "文化含义", body: "凤鸟纹为楚文化核心母题，象征“凤鸣朝阳”与生命再生；衣绣凤鸟不仅是审美，更是楚人信巫好祀的精神表达。" },
    ],
  },
  "信期绣绵袍": {
    relicImage: "/images/relics/relic_han_xinqixiu.jpg",
    relicCaption: "褐色菱纹罗地“信期绣”丝绵袍 · 马王堆一号汉墓出土 · 湖南博物院藏",
    sections: [
      { title: "形制结构", body: "西汉丝绵袍：交领右衽、曲裾（或直裾）式长袍，夹絮丝绵。衣长150厘米、通袖长250厘米、袖口28厘米、腰宽60厘米，规格可见汉代贵妇礼服之恢弘。" },
      { title: "出土实物", body: "1972年马王堆一号汉墓出土。该墓丝织品数量达百余件，信期绣纹样以穗状流云与卷曲蔓草为骨，寓“燕雀归巢、信期而至”之意。" },
      { title: "工艺特征", body: "罗地织绣：罗为多孔透气的提花织物，绣线细密；衣缘以起绒锦镶边。信期绣与乘云绣、长寿绣并称“马王堆三大名绣”。" },
      { title: "穿着场合", body: "绵袍为长沙国贵族冬装，外可罩素纱单衣；辛追墓出土时丝袍叠放规整，足证其生前礼制生活之讲究。" },
    ],
  },
  "印花敷彩丝绵袍": {
    relicImage: "/images/relics/relic_han_yinhuafucai.jpg",
    relicCaption: "印花敷彩纱丝绵袍 · 马王堆一号汉墓出土 · 湖南博物院藏（官网图）",
    sections: [
      { title: "形制结构", body: "西汉直裾式丝绵袍：交领右衽，身长129厘米、袖通长250厘米。面料为印花敷彩纱，轻薄而有骨架，是汉代贵族礼服中的珍品。" },
      { title: "出土实物", body: "马王堆一号汉墓（辛追墓）出土，同墓另有素纱单衣、信期绣绵袍等。印花敷彩纱将“印花”与“手绘”两道工序结合，为西汉首创。" },
      { title: "工艺特征", body: "纹样为藤本植物，朱红、粉白、墨黑三色套印再以彩笔勾绘。印花敷彩技术（先印轮廓、再敷彩填色）是汉代染织工艺的最高成就之一。" },
      { title: "穿着场合", body: "此类华服为长沙国丞相夫人等级的随葬礼服，印证《汉书·景帝纪》对锦绣绮罗的记载，反映西汉上层社会的奢华生活。" },
    ],
  },
  "魏晋襦裙": {
    relicImage: "/images/relics/relic_weijin_ruqun.jpg",
    relicCaption: "《女史箴图》局部（袿衣仕女） · 顾恺之绘 · 大英博物馆藏本",
    sections: [
      { title: "形制结构", body: "魏晋女性襦裙：上襦短窄、下裙宽长曳地，裙腰束高，配彩色飘带（蔽膝与垂绦）。宽大衣裙随步飘举，是“裙裾飞扬”的魏晋审美。" },
      { title: "图像证据", body: "顾恺之《女史箴图》中贵族女性着宽大衣裙、披帛垂绦，衣纹如春蚕吐丝；同期敦煌壁画供养人亦见襦裙外加大袖衫的装束。" },
      { title: "工艺特征", body: "面料以纱、罗、绢为主，素白、浅青为主色；纹样见忍冬纹、莲花纹，体现佛教美术东渐的影响。" },
      { title: "审美含义", body: "魏晋玄学尚“清虚旷远”，女性服饰由汉之庄重转向飘逸纤丽，宽袖、长裙、飘带构成“凌云”意象。" },
    ],
  },
  "裲裆": {
    relicImage: "/images/relics/relic_weijin_liangdang.jpg",
    relicCaption: "南北朝武士图砖 · 着宽袖衣外穿裲裆 · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "裲裆（两当）：前胸后背各一片布帛，肩部缀带相连，无袖，外穿于褶衣之上。形制接近后世背心、坎肩，是武将与仪卫的标识性装束。" },
      { title: "图像证据", body: "河南邓县南朝画像砖与故宫藏南北朝武士图砖中，武士身着宽袖衣、外罩裲裆，束带佩刀；同期陶俑亦常见此式。" },
      { title: "工艺特征", body: "裲裆以布帛为面，讲究者饰鳞纹、兽纹，武将裲裆或内衬铁片（发展为甲）。" },
      { title: "礼制含义", body: "《释名》云“裲裆，其一当胸、其一当背也”；其制后世演变为宋代背子、清代坎肩，是华夏“无袖衣”谱系的源头之一。" },
    ],
  },
  "半臂": {
    relicImage: "/images/relics/relic_tang_banbi.jpg",
    relicCaption: "唐永泰公主墓壁画 · 持物侍女着半臂 · 陕西历史博物馆藏",
    sections: [
      { title: "形制结构", body: "半臂为短袖上衣，袖长及肘，对襟或套头，领口宽大。隋唐女子穿法：内着长袖衫襦、外罩半臂，下配高腰长裙，是唐代“胡化”时尚的象征。" },
      { title: "图像证据", body: "唐永泰公主墓、燕德妃墓（昭陵）壁画中，侍女多着半臂襦裙、披帛垂肩；敦煌壁画供养人亦有半臂装束，可见其流行之广。" },
      { title: "工艺特征", body: "半臂面料以锦、绫、纱为主，袖口与领缘以锦镶边；纹样见宝相花、联珠纹，色彩绯红、靛青并重，华丽鲜明。" },
      { title: "来源与演变", body: "半臂由半袖短衣受胡服影响改制，初唐女子“上襦外着半臂”成为一时风尚，晚唐后渐少见，为宋明背子、褙子所承。" },
    ],
  },
  "胡服·缺胯袍": {
    relicImage: "/images/relics/relic_tang_hufu.jpg",
    relicCaption: "唐章怀太子墓《客使图》 · 陕西历史博物馆藏（唯一反映外交题材的唐墓壁画）",
    sections: [
      { title: "形制结构", body: "缺胯袍为胡服系袍服：圆领（或翻领）、窄袖、袍身开衩便于骑马。唐墓壁画中胡人使节多着翻领紫袍、束带，足蹬靴，是“胡服盛行”的直接证据。" },
      { title: "图像证据", body: "章怀太子墓墓道东壁《客使图》（高1.85米、长2.47米）：左三人为唐鸿胪寺官员（介帻漆纱笼冠、阔袖大红袍），右三人为东罗马、新罗、靺鞨使节，各着本族服制。" },
      { title: "工艺特征", body: "胡服以织锦为贵，联珠纹、团窠纹等中亚纹样传入；唐太宗令织“胡锦”，色彩绚烂，见证丝路织造交流。" },
      { title: "历史含义", body: "唐代与三百余国交往，长安设鸿胪寺、典客署专司接待；《客使图》正是胡汉服饰交汇、万国来朝的时代缩影。" },
    ],
  },
  "幞头": {
    relicImage: "/images/relics/relic_tang_futou.jpg",
    relicCaption: "唐懿德太子墓壁画 · 戴幞头穿圆领袍人物 · 陕西历史博物馆藏",
    sections: [
      { title: "形制结构", body: "幞头为唐代男子最通行首服：以黑色皂罗裹头，四脚束结（两脚系于脑后、两脚反结于顶），后渐加硬脚、展脚。上至帝王、下至庶民，无不佩戴。" },
      { title: "图像证据", body: "章怀太子墓《仪卫领队图》、懿德太子墓壁画中，仪卫与官员均戴幞头、着圆领袍、束革带；《步辇图》中唐太宗亦戴幞头。" },
      { title: "工艺特征", body: "幞头用料以罗、帛为主，玄色为常；演变中脚形由软变硬、由直变曲，至宋发展为展脚幞头、乌纱帽。" },
      { title: "礼制含义", body: "“袍衫幞头”是唐代官民服饰的基本组合；服色依品级而分，幞头之脚形亦随身份地位变化，是身份制度的直接载体。" },
    ],
  },
  "大袖·礼衣": {
    relicImage: "/images/relics/relic_song_daxiu.jpg",
    relicCaption: "《宋宁宗后坐像》 · 交领大袖五彩褘衣 · 台北故宫博物院藏",
    sections: [
      { title: "形制结构", body: "宋代命妇大袖礼衣（褘衣）：交领、大袖、衣长及足，配花钗礼冠、霞帔与玉带。宽袖舒展、缘边织金，是宋代宫廷最隆重的女装礼服。" },
      { title: "图像证据", body: "《宋宁宗后坐像》所绘皇后着交领大袖五彩褘衣，衣身绣摇翟雉纹、缘边织金，头戴凤冠花钗；同期《宋仁宗后坐像》亦同式。" },
      { title: "工艺特征", body: "面料以罗、绢、织绣为主，纹样见摇翟纹、花钗纹；宋代织绣“轻清典雅”，色彩深蓝、绛紫为贵，反衬礼服的庄严。" },
      { title: "礼制含义", body: "《宋史·舆服志》载命妇礼服之制：皇后褘衣、皇太子妃褕翟，以雉鸟纹样区分等级；大袖礼衣是“服以章德”观念的宋代实践。" },
    ],
  },
  "朱子深衣": {
    relicImage: "/images/relics/relic_song_zhuzishenyi.jpg",
    relicCaption: "朱子深衣结构图（据《朱子家礼》复原） · 裁片尺寸详解",
    sections: [
      { title: "形制结构", body: "朱子深衣：上衣二幅屈为四幅、下裳六幅破为十二片，交领右衽、宽袖，袖口一尺二寸，领缘广一寸半。全衣“衣—裳—缘—带”体系完备，配幅巾为大带礼服。" },
      { title: "史料记载", body: "朱熹据《礼记·深衣》于《家礼》中考定深衣制度，创“朱子深衣”范式，成为宋元明清士人礼服与冠礼、祭礼的常用服。" },
      { title: "象数含义", body: "上衣四幅象四季，下裳十二片象十二月；袖圆以应规、交领矩以应方，喻“无规矩不成方圆”；背缝垂直喻正直，下襟齐地喻权衡。" },
      { title: "工艺特征", body: "面料以布、绢为主，玄色衣裳、素白领缘；衣缘（甲袖口30cm、乙领缘6-7cm、丙衣片55-60cm、丁衣长45-50cm等）均依《家礼》尺寸。" },
    ],
  },
  "辫线袄": {
    relicImage: "/images/relics/relic_yuan_bianxianao.jpg",
    relicCaption: "元代辫线袄（绫绢） · 河北隆化鸽子洞出土 · 中国丝绸博物馆藏",
    sections: [
      { title: "形制结构", body: "辫线袄为元代蒙古男子袍服：交领窄袖，腰间以辫线（编结的窄带）横束数道，腰以下打细褶如裙，便于骑射乘马。" },
      { title: "出土实物", body: "河北隆化鸽子洞出土元代丝织品中即有辫线袄实物，绫、绢质地，交领窄袖、腰下百褶；中国丝绸博物馆、内蒙古博物院均有藏品。" },
      { title: "工艺特征", body: "面料以绫、绢、织金锦为主，纹样见八宝纹、云纹；元代织金（纳石失）工艺发达，蒙古贵族的辫线袄常织金为饰。" },
      { title: "文化含义", body: "辫线袄由蒙古游牧骑射生活催生，随元代统治传入中原，成为“胡服入华”的重要款式，明清“缺胯袍”“行袍”多承其绪。" },
    ],
  },
  "姑姑冠": {
    relicImage: "/images/relics/relic_yuan_guguguan.jpg",
    relicCaption: "元明宗皇帝后画像 · 头戴罟罟冠（姑姑冠） · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "姑姑冠（罟罟冠）：以画木为骨、包红绢金帛，顶插四五尺柳枝或铁枝，覆以青毡，饰以翠花珠玉。已婚蒙古贵妇头戴此冠，高耸如塔。" },
      { title: "史料记载", body: "《蒙古秘史》最早记罟罟冠；《黑鞑事略》载“妇顶故姑……顶之上用四五尺长柳枝或铁打成枝，包以青毡”。《元史·舆服志》列为后妃礼服之首服。" },
      { title: "工艺特征", body: "冠骨用木或铁，外覆红绢金帛，饰珍珠、翠花、五彩帛，贵族间以珠玉多寡争胜；下垂珠帘璎珞，行走时摇曳生辉。" },
      { title: "礼制含义", body: "姑姑冠是蒙古族已婚妇女的标志，装饰华丽者是贵族身份象征；元代后妃画像（如明宗皇帝后）皆戴此冠，为蒙元服饰最鲜明的符号。" },
    ],
  },
  "道袍": {
    relicImage: "/images/relics/relic_ming_daopao.jpg",
    relicCaption: "明代道服肖像（束太带） · 《大明衣冠图鉴》",
    sections: [
      { title: "形制结构", body: "明代道袍：交领右衽、宽袖长身，衣长及足，腰部以丝绦或太带束系，两肋开衩。是明代士人最常用的日常正装，兼为深衣之变体。" },
      { title: "图像证据", body: "明代文人肖像画中，士人多着道袍束太带、头戴幅巾或乌纱帽；衍圣公衣冠像（孔府旧藏）亦见道袍之制。" },
      { title: "工艺特征", body: "面料以绫、绸为主，素色为尚，暗花、云纹为饰；交领处常加护领（白领缘），体现明代士人衣冠的整饬雅致。" },
      { title: "文化含义", body: "道袍之名虽与道家相关，实为明代通用男装；“道袍—直身—曳撒”构成明代男装三大形制，晚明《金瓶梅》《醒世恒言》中屡见其名。" },
    ],
  },
  "补服·官服": {
    relicImage: "/images/relics/relic_ming_bufu.jpg",
    relicCaption: "《徐如珂常服像》 · 二品孔雀补子 · 明代官员常服像",
    sections: [
      { title: "形制结构", body: "明代官员常服：圆领（盘领）大袖袍，胸背缀“补子”一块（约40-50厘米见方）以别品级，头戴乌纱帽，腰束革带。" },
      { title: "图像证据", body: "《徐如珂常服像》（二品孔雀补子）、《石茂华常服像》（一品仙鹤补子）、《沈度写真像》（盘领补服）等明代肖像画完整记录了补服制度。" },
      { title: "品级制度", body: "补子纹样：文官绣禽（一品仙鹤、二品孔雀、三品锦鸡……九品练鹊），武官绣兽（一品麒麟、二品狮子……九品海马）；服色四品以上绯、七品以上青、以下绿。" },
      { title: "礼制含义", body: "《明史·舆服志》详载补服之制，“补子定品”是明代官服最醒目的身份符号，也为清代补服制度所直接继承。" },
    ],
  },
  "袄裙": {
    relicImage: "/images/relics/relic_ming_aoqun.jpg",
    relicCaption: "明孔府旧藏桃红纱地彩绣花鸟纹大袖衫 · 孔子博物馆藏",
    sections: [
      { title: "形制结构", body: "明代女装“袄裙”组合：上着短袄（衫）、下配长裙，裙腰束高、裙身曳地。大袖衫为贵族版本，衣身宽博、袖口广大。" },
      { title: "出土实物", body: "孔府旧藏桃红纱地彩绣花鸟纹大袖衫：桃红纱地轻薄通透，彩绣花鸟纹样繁密，袖缘织金，是存世明代女装中的名品，藏于孔子博物馆。" },
      { title: "工艺特征", body: "面料以纱、绫、缎为主，纹样见花鸟纹、缠枝莲、云肩纹；明代妆花、织金、刺绣工艺并兴，色彩桃红、藕色、靛青层次丰富。" },
      { title: "流行与等级", body: "袄裙自宋代襦裙演化而来，明代普及于各阶层；讲究者以织金妆花为贵，孔府旧藏诸器正是明代服饰“重工艺、尚华美”的缩影。" },
    ],
  },
  "马褂": {
    relicImage: "/images/relics/relic_qing_magua.jpg",
    relicCaption: "清湖色团花事事如意织金缎绵马褂 · 清宫旧藏 · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "清代马褂：圆立领、对襟（或琵琶襟）、平袖，左右及后开裾。身长73厘米、两袖通长120厘米、袖口宽34厘米。原为骑射短衣，后成男子常服。" },
      { title: "出土实物", body: "故宫藏湖色团花事事如意织金缎绵马褂：湖色冰梅纹暗花缎地，织金柿蒂形开光柿与如意纹，谐寓“事事如意”，外镶石青万字织金缎边，为皇帝便服。" },
      { title: "工艺特征", body: "面料以缎、绸、织金为主，领、袖、襟、摆多重镶滚；缀银镀金团龙纹币式扣等，织金工艺与镶滚装饰是清代服饰的典型语言。" },
      { title: "礼制等级", body: "马褂原为“行褂”，乾隆后成为礼服外褂之补充；明黄为帝后专用，服色纹样依等级递减，清宫旧藏中皇后燕居亦多着绣花马褂。" },
    ],
  },
  "氅衣": {
    relicImage: "/images/relics/relic_qing_changyi.jpg",
    relicCaption: "清绿色缂金银万字地蝠寿纹棉氅衣 · 清光绪 · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "清代氅衣：圆领、大襟右衽、平端袖（袖长及肘，亦可作舒袖），左右开裾至腋下的直身式袍服。身长139厘米、两袖通长114厘米，絮薄棉，为后妃冬装。" },
      { title: "出土实物", body: "故宫藏绿色缂金银万字地蝠寿纹棉氅衣（清光绪）：缂金银万字地布蝠、寿纹，缘边织金，内衬品月色素纺丝绸里，襟缀铜镀金錾花币式扣。" },
      { title: "工艺特征", body: "面料以缂丝、绸缎为主，缂丝“通经断纬”织出金银万字地纹；纹样蝠（福）、寿、卍字连缀，寓意吉祥；镶滚绦边层叠，工艺繁缛精美。" },
      { title: "礼制等级", body: "氅衣是晚清后妃最重要的便服类别，慈禧影像中屡见其身影；颜色、纹样与镶滚繁简反映等级，是清代宫廷服饰“重装饰”审美的代表。" },
    ],
  },
  "坎肩": {
    relicImage: "/images/relics/relic_qing_kanjian.jpg",
    relicCaption: "清石青色团牡丹暗八仙纹一字襟坎肩 · 故宫博物院藏",
    sections: [
      { title: "形制结构", body: "一字襟坎肩：前襟于胸部横开呈“一”字形，缀铜鎏金“禄”字扣十三颗（称“十三太保”），圆立领、无袖。满族男女皆着，晚清京师尤盛。" },
      { title: "出土实物", body: "故宫藏石青色团牡丹暗八仙纹一字襟坎肩：石青缎地以圆金线织金团牡丹、卍字与暗八仙纹，织金绦边，质地厚重，尽显皇家气派。" },
      { title: "工艺特征", body: "面料以缎、锦为主，织金、刺绣并用；一字襟钉扣13粒（左右腋下各3粒），源自武将“巴图鲁坎肩”，原为兵卒骑射护身之服。" },
      { title: "文化含义", body: "坎肩（背心、马甲）为清代最具特色的无袖衣；巴图鲁坎肩融合满汉蒙服饰文化，瓦当纹、吉语绣纹体现多元文化交融。" },
    ],
  },
  "定陵织金妆花缎": {
    relicImage: "/images/relics/relic_geo_dingling_zhuanghua.jpg",
    relicCaption: "明·定陵出土织金妆花缎龙袍（北京昌平 · 明十三陵博物馆）",
    sections: [
      { title: "形制结构", body: "织金妆花缎为明代最高等级的织锦之一，以彩色纬纱与捻金线通梭织造，龙纹、海水江崖纹满地铺陈，袍身宽大，对襟或交领，为帝后吉服、朝服面料。" },
      { title: "出土实物", body: "明定陵出土织金孔雀羽妆花纱龙袍：史料记载一件龙袍用捻金线4000米、片金线11300根，龙纹以孔雀羽线绣制，历经数百年依旧清晰，可谓“寸金换寸锦”。" },
      { title: "工艺特征", body: "妆花缎织造集挖花、织金、妆彩于一体：纬线分段换色显花，金线织入形成“浑金”效果，代表明代丝织工艺的最高水平，为研究明代帝后服饰的第一手实物。" },
    ],
  },
  "敦煌供养人像壁画": {
    relicImage: "/images/relics/relic_geo_dunhuang_tang.jpg",
    relicCaption: "敦煌莫高窟壁画供养人像（隋唐 · 敦煌研究院）",
    sections: [
      { title: "形制结构", body: "敦煌壁画供养人像展现了隋唐女子的典型衣冠：高髻簪花，上着窄袖或大袖襦衫，下穿曳地长裙，肩披帛、腰束带，丰腴雍容，是“大袖襦裙”与“披帛”的直接图像证据。" },
      { title: "出土实物", body: "第130窟《都督夫人礼佛图》为盛唐供养人代表作：贵妇着红底花裙、披浅蓝披帛，身后侍女队列衣色纷呈；五代第98窟回鹘公主像着红色圆领拖裾长袍、佩璎珞，与文献互证。" },
      { title: "工艺特征", body: "壁画颜料以矿物色为主（石青、石绿、朱砂），人物衣纹线描流畅，设色浓丽；供养人服饰细节丰富，是复原隋唐服饰形制、色彩与纹样的权威图像史料。" },
    ],
  },
  "集宁路织金锦": {
    relicImage: "/images/relics/relic_geo_jininglu_zhijin.jpg",
    relicCaption: "元·集宁路古城窖藏织金锦（内蒙古集宁 · 集宁博物馆）",
    sections: [
      { title: "形制结构", body: "织金锦即“纳石失”，元代最负盛名的丝织物：以片金线或捻金线织入纬线，满地织金、华彩夺目，多用于质孙服（一色服）、帐幕与靴帽，彰显蒙古贵族气象。" },
      { title: "出土实物", body: "内蒙古集宁路古城遗址窖藏出土大批织金锦：织缠枝莲、团窠纹，金线细密均匀，实物印证元代“纳石失”工艺的成熟与东西方织造技术的交流。" },
      { title: "工艺特征", body: "织金技法分“片金”与“捻金”两种：片金线扁薄闪光、捻金线圆润耐磨；元代织金锦经纬密度大、质地厚重，金线占比高，是元代服饰奢华风尚的典型代表。" },
    ],
  },
  "马山一号楚墓丝袍": {
    relicImage: "/images/relics/relic_geo_mashan_jinpao.jpg",
    relicCaption: "战国·马山一号楚墓凤鸟花卉纹绣浅黄绢面绵袍（荆州 · 荆州博物馆）",
    sections: [
      { title: "形制结构", body: "马山一号楚墓出土战国丝袍：交领右衽、宽袖，衣身以刺绣凤鸟花卉纹装饰，腰束宽带、腹前悬“蔽膝”，是“衣作绣、锦为缘”楚服制度的直接实证。" },
      { title: "出土实物", body: "湖北荆州马山一号楚墓（战国中期）出土大量丝织衣物：凤鸟花卉纹绣浅黄绢面锦袍、对龙对凤纹绣衾等，保存完好、纹样瑰丽，被誉为“地下丝国”。" },
      { title: "工艺特征", body: "楚绣以锁绣针法为主，纹样以凤鸟、花卉、龙蛇为主题，构图繁缛生动、色彩浓艳；锦缘用经线显花，为先秦时期南方丝绸刺绣工艺的巅峰之作。" },
    ],
  },
  "孔府桃红纱大袖衫": {
    relicImage: "/images/relics/relic_geo_kongfu_daxiushan.jpg",
    relicCaption: "明·孔府旧藏桃红纱大袖衫（曲阜 · 孔子博物馆）",
    sections: [
      { title: "形制结构", body: "孔府旧藏明代大袖衫：桃红色纱地，交领或对襟、宽袖，衣长过膝，常与马面裙搭配穿着，是明代贵族女性吉服、礼服的代表形制。" },
      { title: "出土实物", body: "山东曲阜孔府旧藏服饰保存大量明代实物：桃红纱大袖衫、白罗道袍、蓝暗花纱缀绣仙鹤方补袍等，为明代服饰研究提供了最完整的传世标本群。" },
      { title: "工艺特征", body: "纱质轻薄透气，多织暗花纹；袖口、领缘常饰织金或绣边，色彩明丽。孔府服饰兼具礼仪性与生活性，是复原明代女性服饰形制与配色的重要依据。" },
    ],
  },
  "娄睿墓壁画衣冠": {
    relicImage: "/images/relics/relic_geo_lourui_mural.jpg",
    relicCaption: "北齐·太原娄睿墓《鞍马出行图》壁画（武平元年 · 山西博物院）",
    sections: [
      { title: "形制结构", body: "娄睿墓壁画人物衣冠：头戴长尾帽（鲜卑风帽），身穿圆领窄袖长袍，腰间系带，足蹬长靴，佩挂弓囊箭箙，为北齐鲜卑贵族骑射装束的直观写照。" },
      { title: "出土实物", body: "1979年山西太原娄睿墓（北齐武平元年，570年）出土，墓道西壁中栏绘《鞍马出行图》长卷式壁画，人物马匹造型生动，是北朝墓葬壁画艺术的高峰。" },
      { title: "图像证据", body: "壁画中前骑胯枣红马、头戴黑色长尾帽，随从簇拥、马匹矫健；人物服饰兼具鲜卑传统与中原汉服元素，见证北朝胡汉服饰文化交融。" },
    ],
  },
};

/* ===== 分裂三卡补充图（形制结构图 / 史料考古图，均取自权威公开来源，与主实例图不重复） ===== */
const EXTRA_IMAGES: Record<string, { structure: string; literature: string }> = {
  "深衣": { structure: "https://aka.doubaocdn.com/s/4KMvXxfxW7", literature: "https://aka.doubaocdn.com/s/WxIICC8p8N" },
  "素纱单衣": { structure: "https://aka.doubaocdn.com/s/7TWuDUbkTy", literature: "https://aka.doubaocdn.com/s/QE6kKIiA1h" },
  "曲裾深衣": { structure: "https://aka.doubaocdn.com/s/pU84q2lUs8", literature: "https://aka.doubaocdn.com/s/1FUUqQGL0m" },
  "宽衫大袖": { structure: "https://aka.doubaocdn.com/s/zRo9BABlCe", literature: "https://aka.doubaocdn.com/s/6idlIjJKrL" },
  "大袖襦裙": { structure: "https://aka.doubaocdn.com/s/Hwxi2yUesd", literature: "https://aka.doubaocdn.com/s/KDTd8T9GVb" },
  "圆领袍": { structure: "https://aka.doubaocdn.com/s/eIGN2aUiRd", literature: "https://aka.doubaocdn.com/s/SbbS5O14dB" },
  "褙子": { structure: "https://aka.doubaocdn.com/s/1Ihv2sTv57", literature: "https://aka.doubaocdn.com/s/Tk2pnEcqgX" },
  "质孙服": { structure: "https://aka.doubaocdn.com/s/L8hFMxVeGN", literature: "https://aka.doubaocdn.com/s/yMvOWVX144" },
  "马面裙": { structure: "https://aka.doubaocdn.com/s/wHzVfTSxgV", literature: "https://aka.doubaocdn.com/s/sMj36cNc8c" },
  "旗装": { structure: "https://aka.doubaocdn.com/s/Js6ekXhqno", literature: "https://aka.doubaocdn.com/s/EcwtUBJewU" },
  "上衣下裳": { structure: "https://aka.doubaocdn.com/s/ZmnkVq9Mmj", literature: "https://aka.doubaocdn.com/s/fHtQzLYhOU" },
  "冕服": { structure: "https://aka.doubaocdn.com/s/ZmnkVq9Mmj", literature: "https://aka.doubaocdn.com/s/fHtQzLYhOU" },
  "凤鸟纹绣绢䋺衣": { structure: "https://aka.doubaocdn.com/s/fHtQzLYhOU", literature: "https://aka.doubaocdn.com/s/2d1h4ypNcf" },
  "信期绣绵袍": { structure: "https://aka.doubaocdn.com/s/4iOHiJ92iv", literature: "https://aka.doubaocdn.com/s/BZhfbEMteJ" },
  "印花敷彩丝绵袍": { structure: "https://aka.doubaocdn.com/s/BZhfbEMteJ", literature: "https://aka.doubaocdn.com/s/4iOHiJ92iv" },
  "魏晋襦裙": { structure: "https://aka.doubaocdn.com/s/F55BC5kjCv", literature: "https://aka.doubaocdn.com/s/rr4x30hVlD" },
  "裲裆": { structure: "https://aka.doubaocdn.com/s/vKxd8ll7yk", literature: "https://aka.doubaocdn.com/s/aXVos1NyEO" },
  "半臂": { structure: "https://aka.doubaocdn.com/s/mO0o59bNAc", literature: "https://aka.doubaocdn.com/s/sEWl5AvZ29" },
  "胡服·缺胯袍": { structure: "https://aka.doubaocdn.com/s/41FA5hmJei", literature: "https://aka.doubaocdn.com/s/Hkqet3COKR" },
  "幞头": { structure: "https://aka.doubaocdn.com/s/38dmRt2Yej", literature: "https://aka.doubaocdn.com/s/LhqGgiV30F" },
  "大袖·礼衣": { structure: "https://aka.doubaocdn.com/s/KJRQvnXWRT", literature: "https://aka.doubaocdn.com/s/5Qka2xwVG8" },
  "朱子深衣": { structure: "https://aka.doubaocdn.com/s/PjWoxIt9Xt", literature: "https://aka.doubaocdn.com/s/orvNiaYqJb" },
  "辫线袄": { structure: "https://aka.doubaocdn.com/s/iqX8u0E6pp", literature: "https://aka.doubaocdn.com/s/owC8S3nYHD" },
  "姑姑冠": { structure: "https://aka.doubaocdn.com/s/KAiFYJj38g", literature: "https://aka.doubaocdn.com/s/La83QJULFV" },
  "道袍": { structure: "https://aka.doubaocdn.com/s/6pRH5jo5M9", literature: "https://aka.doubaocdn.com/s/LB8tytgh7J" },
  "补服·官服": { structure: "https://aka.doubaocdn.com/s/sMj36cNc8c", literature: "https://aka.doubaocdn.com/s/wHzVfTSxgV" },
  "袄裙": { structure: "https://aka.doubaocdn.com/s/LB8tytgh7J", literature: "https://aka.doubaocdn.com/s/6pRH5jo5M9" },
  "马褂": { structure: "https://aka.doubaocdn.com/s/H6fYT3zgRq", literature: "https://aka.doubaocdn.com/s/NjfnhwPLBE" },
  "氅衣": { structure: "https://aka.doubaocdn.com/s/T5YumtlNIx", literature: "https://aka.doubaocdn.com/s/Js6ekXhqno" },
  "坎肩": { structure: "https://aka.doubaocdn.com/s/NjfnhwPLBE", literature: "https://aka.doubaocdn.com/s/T5YumtlNIx" },
  "定陵织金妆花缎": { structure: "https://aka.doubaocdn.com/s/biSR705YsH", literature: "https://aka.doubaocdn.com/s/fFPmkWW4Zj" },
  "敦煌供养人像壁画": { structure: "https://aka.doubaocdn.com/s/KDTd8T9GVb", literature: "https://aka.doubaocdn.com/s/ySFS25tRsu" },
  "集宁路织金锦": { structure: "https://aka.doubaocdn.com/s/owC8S3nYHD", literature: "https://aka.doubaocdn.com/s/iqX8u0E6pp" },
  "马山一号楚墓丝袍": { structure: "https://aka.doubaocdn.com/s/ddvpPuITdk", literature: "https://aka.doubaocdn.com/s/IW0AyRTVL3" },
  "孔府桃红纱大袖衫": { structure: "https://aka.doubaocdn.com/s/LB8tytgh7J", literature: "https://aka.doubaocdn.com/s/fFPmkWW4Zj" },
  "娄睿墓壁画衣冠": { structure: "https://aka.doubaocdn.com/s/aXVos1NyEO", literature: "https://aka.doubaocdn.com/s/vKxd8ll7yk" },
  "秦陵铠甲武士俑服饰": { structure: "https://aka.doubaocdn.com/s/BZhfbEMteJ", literature: "https://aka.doubaocdn.com/s/pU84q2lUs8" },
  "信阳长台关杯纹绮服": { structure: "https://aka.doubaocdn.com/s/ZmnkVq9Mmj", literature: "https://aka.doubaocdn.com/s/uDjHyPS6dU" },
  "虎丘塔宋代丝织服饰": { structure: "https://aka.doubaocdn.com/s/KJRQvnXWRT", literature: "https://aka.doubaocdn.com/s/PjWoxIt9Xt" },
  "赵伯澐墓大袖衫": { structure: "https://aka.doubaocdn.com/s/5Qka2xwVG8", literature: "https://aka.doubaocdn.com/s/orvNiaYqJb" },
  "德安南宋周氏墓丝绸服": { structure: "https://aka.doubaocdn.com/s/Tk2pnEcqgX", literature: "https://aka.doubaocdn.com/s/1Ihv2sTv57" },
  "老官山汉墓织机服饰": { structure: "https://aka.doubaocdn.com/s/4iOHiJ92iv", literature: "https://aka.doubaocdn.com/s/7TWuDUbkTy" },
  "阿斯塔那唐锦袍": { structure: "https://aka.doubaocdn.com/s/41FA5hmJei", literature: "https://aka.doubaocdn.com/s/SbbS5O14dB" },
  "南越王墓丝织服饰": { structure: "https://aka.doubaocdn.com/s/1FUUqQGL0m", literature: "https://aka.doubaocdn.com/s/QE6kKIiA1h" },
  "都兰热水织锦服饰": { structure: "https://aka.doubaocdn.com/s/Hkqet3COKR", literature: "https://aka.doubaocdn.com/s/eIGN2aUiRd" },
  "定陵孝靖皇后百子衣": { structure: "https://aka.doubaocdn.com/s/fFPmkWW4Zj", literature: "https://aka.doubaocdn.com/s/biSR705YsH" },
  "永泰公主墓侍女半臂": { structure: "https://aka.doubaocdn.com/s/mO0o59bNAc", literature: "https://aka.doubaocdn.com/s/ySFS25tRsu" },
};

const detailData = computed<any>(() => {
  const name = detail.value?.name || "";
  return COSTUME_DETAILS[name] || {
    relicImage: "",
    relicCaption: "",
    sections: [
      { title: "形制结构", body: detail.value?.description || "档案整理中。" },
    ],
  };
});

async function load() {
  loading.value = true;
  try {
    const data: any = await fetchCostumes({ dynasty: dynasty.value, category: category.value, keyword: keyword.value, page_size: 50 });
    costumes.value = data.items;
  } finally { loading.value = false; }
}

async function doWebSearch() {
  const kw = keyword.value.trim();
  if (!kw) return;
  webLoading.value = true;
  webError.value = "";
  webResults.value = [];
  try {
    const data: any = await fetchArchiveWebSearch(`${kw} 服饰 文物`);
    webQuery.value = kw;
    webResults.value = data.results || [];
    if (!webResults.value.length) webError.value = data.error || "全网暂未检索到相关内容";
  } catch {
    webError.value = "全网搜索暂不可用，请稍后重试";
  } finally { webLoading.value = false; }
}

async function loadDetail(id: number) {
  detail.value = await fetchCostumeDetail(id) as any;
  messages.value = [];
}

async function sendChat() {
  if (!question.value.trim() || !currentId.value) return;
  const q = question.value.trim();
  messages.value.push({ role: "user", content: q });
  question.value = "";
  chatLoading.value = true;
  try {
    const res: any = await chatWithCostume(currentId.value, q);
    messages.value.push({ role: "assistant", content: res.answer, source: res.source_ref });
  } finally {
    chatLoading.value = false;
    setTimeout(() => chatBox.value?.scrollTo({ top: 9999, behavior: "smooth" }), 50);
  }
}

onMounted(async () => {
  eras.value = ((await fetchEras() as any).eras || []);
  const id = Number(route.params.id);
  if (id) {
    currentId.value = id;
    loadDetail(id);
  } else {
    load();
    loadUserWorks();
    if (route.query.keyword) {
      keyword.value = String(route.query.keyword);
      load();
    }
  }
});

watch(() => route.params.id, (id) => {
  currentId.value = id ? Number(id) : null;
  if (id) loadDetail(Number(id));
  else load();
});
</script>

<style scoped>
.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.filters { display: flex; gap: 8px; }
.web-results { margin: 14px 0; padding: 14px 16px; }
.web-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.web-item { display: block; padding: 10px 0; border-bottom: 1px dashed var(--ys-border, #e8e0d5); text-decoration: none; }
.web-item:last-child { border-bottom: none; }
.web-item-title { color: var(--ys-primary, #7a4b2a); font-weight: 600; font-size: 14px; }
.web-item-title:hover { text-decoration: underline; }
.web-item-src { font-size: 12px; color: #8a8a6a; margin: 2px 0; }
.web-item-snippet { font-size: 13px; color: #5a544a; line-height: 1.6; margin: 0; }
.costume-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; grid-auto-rows: 1fr; }
.costume-card { cursor: pointer; transition: transform 0.15s; display: flex; flex-direction: column; overflow: hidden; }
.costume-card:hover { transform: translateY(-2px); }
.card-img { position: relative; height: 160px; overflow: hidden; background: #f6efe2; }
.card-img img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.25s ease; }
.costume-card:hover .card-img img { transform: scale(1.05); }
.card-img .img-placeholder { display: flex; align-items: center; justify-content: center; height: 100%; color: #8a7a60; font-size: 13px; }
.card-img .dynasty-badge {
  position: absolute; top: 8px; right: 8px;
  background: rgba(126, 36, 24, 0.85); color: #fff; font-size: 12px;
  padding: 2px 8px; border-radius: 10px;
}
.card-img .user-badge {
  position: absolute; top: 8px; left: 8px;
  background: rgba(36, 96, 126, 0.85); color: #fff; font-size: 11px;
  padding: 2px 7px; border-radius: 10px;
}
.card-body { padding: 12px 14px 14px; display: flex; flex-direction: column; flex: 1; }
.card-head { display: flex; justify-content: space-between; align-items: baseline; }
.card-head h3 { margin: 0; font-size: 17px; }
.ys-tag { align-self: flex-start; }
.dynasty { color: var(--ys-red-deep); font-size: 13px; }
.costume-desc { color: var(--ys-ink-2); font-size: 13px; line-height: 1.6; min-height: 42px; flex: 1;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.costume-meta { display: flex; gap: 10px; font-size: 12px; color: var(--ys-ink-3); margin-bottom: 8px; }

.detail-layout { display: grid; grid-template-columns: 1fr 340px; gap: 20px; }
.detail-main { min-width: 0; }
.detail-head { display: flex; align-items: center; gap: 14px; }
.detail-head h2 { margin: 0; font-size: 22px; }
.body-text { color: var(--ys-ink-2); line-height: 1.8; }
.graph-nodes { display: flex; flex-wrap: wrap; gap: 8px; }
.graph-node { border: 1px solid var(--ys-line); background: #fffdf8; border-radius: 6px; padding: 4px 10px; font-size: 13px; }
.graph-node i { font-style: normal; color: var(--ys-red-deep); margin-right: 4px; }

/* 权威实例图 */
.relic-gallery { margin: 10px 0 18px; }
.relic-card { display: inline-block; max-width: 420px; }
.relic-card img { width: 100%; max-height: 340px; object-fit: contain; border-radius: 8px; box-shadow: 0 8px 20px rgba(122, 60, 30, 0.18); cursor: zoom-in; background: #fffdf6; }
.relic-source { font-size: 12px; color: var(--ys-ink-3); margin-top: 6px; line-height: 1.6; }
.lightbox { position: fixed; inset: 0; z-index: 3000; background: rgba(0, 0, 0, 0.72); display: grid; place-items: center; cursor: zoom-out; }
.lightbox img { max-width: 92vw; max-height: 92vh; object-fit: contain; border-radius: 8px; }

/* 史料详析 */
.detail-sections { margin: 10px 0 16px; display: flex; flex-direction: column; gap: 12px; }
.detail-sec { border-left: 3px solid var(--ys-red); background: rgba(169, 50, 38, 0.04); border-radius: 0 8px 8px 0; padding: 10px 14px; }
.sec-title { margin: 0 0 6px; font-size: 14px; color: var(--ys-red-deep); }
.sec-body { margin: 0; color: var(--ys-ink-2); line-height: 1.8; font-size: 13.5px; }

.chat-card { position: sticky; top: 76px; }
.chat-box { height: 340px; overflow-y: auto; border: 1px solid var(--ys-line); border-radius: 8px; padding: 12px; background: #fffdf8; display: flex; flex-direction: column; gap: 10px; }
.chat-msg { display: flex; flex-direction: column; }
.chat-msg.user { align-items: flex-end; }
.chat-msg.user .chat-bubble { background: var(--ys-red); color: #fff; }
.chat-bubble { max-width: 88%; padding: 8px 12px; border-radius: 10px; font-size: 13px; line-height: 1.7; background: #f1e9d6; }
.chat-source { font-size: 11px; color: var(--ys-ink-3); margin-top: 3px; }
.chat-typing { color: var(--ys-ink-3); font-size: 12px; }
.chat-input { display: flex; gap: 8px; margin-top: 10px; }
.chat-suggests { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.suggest { cursor: pointer; }

/* 用户作品：其他用户创建的服饰档案 */
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

@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
  .chat-card { position: static; }
}
</style>
