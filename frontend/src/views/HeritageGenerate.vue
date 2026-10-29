<template>
  <div class="heritage-page">
    <!-- Hero：衣脉传承 -->
    <section class="heritage-hero">
      <div class="hero-inner">
        <div class="hero-text">
          <span class="hero-kicker">衣冠上国 · 礼仪之邦</span>
          <h2 class="hero-title">
            <span v-for="(ch, i) in heroTitleChars" :key="i" class="ht-ch"
                  :style="{ animationDelay: (0.18 + i * 0.06) + 's' }">{{ ch }}</span>
          </h2>
          <p class="hero-sub" style="animation-delay: .9s">黄帝垂衣裳而天下治，衣冠文明绵延五千载——让每一次溯源，都成为一次传承</p>
          <p class="hero-sub sub2" style="animation-delay: 1.1s">浏览档案、参与问答、复刻复原，你的每一步都在为华夏衣冠续写当代注脚</p>
        </div>
        <div class="hero-seal" aria-hidden="true">承</div>
      </div>
      <div class="hero-fret" aria-hidden="true"></div>
    </section>

    <div class="heritage-layout">
      <!-- 左列：传承画像 + 承诺书 -->
      <div class="heritage-col">
        <!-- 个性化画像 -->
        <div class="ys-card profile-card">
          <div class="card-head">
            <h3 class="ys-title">你的传承画像</h3>
            <span class="card-badge" v-if="profile">已解锁</span>
          </div>
          <p class="card-tip">你的每一次浏览、问答与复原，都在为这幅画像添一笔</p>
          <template v-if="profile">
            <div class="profile-stats">
              <div class="stat"><b>{{ profile.total_interactions }}</b><span>溯源学习互动</span></div>
              <div class="stat"><b>{{ profile.revival_works }}</b><span>复原作品</span></div>
              <div class="stat"><b>{{ profile.focus_costumes?.length || 0 }}</b><span>重点关注服饰</span></div>
            </div>
            <div class="focus-block" v-if="profile.focus_costumes?.length">
              <span class="focus-label">重点关注</span>
              <div class="focus-list">
                <span v-for="c in profile.focus_costumes" :key="c.id" class="ys-tag"
                      @click="$router.push(`/archive/${c.id}`)">{{ c.dynasty }} · {{ c.name }}</span>
              </div>
            </div>
            <el-button type="primary" :loading="genPlan" @click="doGenPlan" class="action-btn">生成个性化学习方案</el-button>
          </template>
          <div v-else class="ys-empty heritage-empty">
            <div class="empty-icon">衣</div>
            <p>登录并开始你的溯源之旅：浏览档案、参与问答、创作复原，画像将随你的足迹生长</p>
            <el-button size="small" type="primary" @click="$router.push('/user')">去登录</el-button>
          </div>
        </div>

        <!-- 传承承诺 -->
        <div class="ys-card commitment-card">
          <div class="card-head">
            <h3 class="ys-title">文化传承承诺书</h3>
            <span class="card-badge" v-if="commitment">已立约</span>
          </div>
          <p class="card-tip">以一份承诺立心——衣脉绵延，始于吾辈</p>
          <template v-if="commitment">
            <div class="commitment-body">
              <div class="commitment-seal">承</div>
              <p class="commitment-text">{{ commitment }}</p>
            </div>
            <el-button size="small" text type="danger" @click="regenerateCommitment">重新生成</el-button>
          </template>
          <el-button v-else type="primary" :loading="genCommit" @click="doCommitment" class="action-btn">生成我的传承承诺</el-button>
        </div>
      </div>

      <!-- 右列：学习方案 + 科普卡片 -->
      <div class="heritage-col">
        <!-- 学习方案 -->
        <div class="ys-card plan-card">
          <div class="card-head">
            <h3 class="ys-title">两周服饰文化学习方案</h3>
            <span class="card-badge" v-if="plan">量身定制</span>
          </div>
          <template v-if="plan">
            <pre class="plan-text">{{ plan }}</pre>
          </template>
          <div v-else class="plan-hint">
            <p>从朝代脉络到形制裁剪，从纹样色彩到礼俗象征——AI 将结合你的溯源足迹，排布两周可执行的学习路径，每一程都落在衣冠之上。</p>
            <p class="hint-sub">点击下方"生成个性化学习方案"即刻开启。</p>
          </div>
        </div>

        <!-- 科普卡片生成 -->
        <div class="ys-card card-gen">
          <div class="card-head">
            <h3 class="ys-title">生成科普分享卡片</h3>
            <span class="card-badge">一键成图</span>
          </div>
          <p class="card-tip">把一件服饰之美写成一段话，生成可分享的古风卡片，让衣冠走出档案</p>
          <el-input v-model="cardForm.title" placeholder="卡片标题，如「明代马面裙之美」「曲裾深衣的绕襟之谜」" size="small" />
          <el-input v-model="cardForm.text" type="textarea" :rows="3" placeholder="卡片内容要点，如：形制特征、纹样寓意、历史出处…" style="margin: 10px 0" />
          <div class="card-foot">
            <el-select v-model="cardForm.theme" size="small" style="width: 120px">
              <el-option label="古风" value="古风" />
              <el-option label="现代简约" value="现代简约" />
            </el-select>
            <el-button type="primary" :loading="genCard" @click="doGenCard">生成文案</el-button>
          </div>
          <div v-if="cardResult" class="card-preview">
            <div class="card-art" :class="{ modern: cardResult.card.theme === '现代简约' }">
              <span class="card-brand">衣溯 · 华夏衣冠志</span>
              <h3>{{ cardResult.card.title }}</h3>
              <p>{{ cardResult.card.text }}</p>
              <div class="card-meta">
                <span>—— {{ cardResult.card.username }}</span>
                <span class="watermark">{{ cardResult.card.watermark }}</span>
              </div>
            </div>
            <el-button size="small" @click="downloadCard">下载分享卡片</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useUserStore } from "@/store/user";
import { fetchHeritageProfile, generatePlan, generateCard, generateCommitment } from "@/api/modules";

const userStore = useUserStore();
/* 首屏开场：标题逐字浮现（空格用不换行空格保证字形动画） */
const heroTitleChars = "衣脉传承 · 文化共创".split("").map((ch) => (ch === " " ? "\u00A0" : ch));
const profile = ref<any>(null);
const plan = ref("");
const genPlan = ref(false);
const cardForm = ref({ title: "", text: "", theme: "古风" });
const cardResult = ref<any>(null);
const genCard = ref(false);
const commitment = ref("");
const genCommit = ref(false);

async function loadProfile() {
  if (!userStore.token) return;
  profile.value = await fetchHeritageProfile() as any;
}

async function doGenPlan() {
  genPlan.value = true;
  try {
    plan.value = (await generatePlan() as any).plan;
  } finally { genPlan.value = false; }
}

async function doGenCard() {
  if (!cardForm.value.title.trim()) return ElMessage.warning("请输入卡片标题");
  genCard.value = true;
  try {
    cardResult.value = await generateCard({ ...cardForm.value }) as any;
  } finally { genCard.value = false; }
}

function downloadCard() {
  if (!cardResult.value) return;
  const el = document.createElement("canvas");
  const ctx = el.getContext("2d")!;
  el.width = 1080; el.height = 1350;
  ctx.fillStyle = "#f5efe4";
  ctx.fillRect(0, 0, 1080, 1350);
  ctx.strokeStyle = "#a93226"; ctx.lineWidth = 6;
  ctx.strokeRect(40, 40, 1000, 1270);
  ctx.fillStyle = "#7e2418";
  ctx.font = "bold 64px serif";
  ctx.textAlign = "center";
  ctx.fillText(cardResult.value.card.title, 540, 180);
  ctx.font = "36px serif";
  ctx.fillStyle = "#5b5144";
  const lines = cardResult.value.card.text.match(/.{1,16}/g) || [];
  lines.slice(0, 12).forEach((line: string, i: number) => ctx.fillText(line, 540, 280 + i * 64));
  ctx.fillStyle = "#8c806e";
  ctx.font = "28px serif";
  ctx.fillText(`—— ${cardResult.value.card.username}`, 540, 1150);
  ctx.fillText(cardResult.value.card.watermark, 540, 1210);
  const a = document.createElement("a");
  a.download = "衣溯·华夏衣冠志分享卡片.png";
  a.href = el.toDataURL("image/png");
  a.click();
}

async function doCommitment() {
  genCommit.value = true;
  try {
    commitment.value = (await generateCommitment() as any).commitment;
  } finally { genCommit.value = false; }
}

function regenerateCommitment() { doCommitment(); }

onMounted(loadProfile);
</script>

<style scoped>
/* ---- Hero ---- */
.heritage-hero {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background:
    radial-gradient(1100px 360px at 85% -60%, rgba(185, 138, 47, .34), transparent 62%),
    linear-gradient(135deg, #7e2418 0%, #a93226 55%, #b98a2f 130%);
  color: #fff;
  padding: 30px 34px 34px;
  margin-bottom: 18px;
  box-shadow: 0 10px 26px rgba(122, 58, 32, .22);
}
.hero-inner { position: relative; z-index: 2; display: flex; justify-content: space-between; align-items: center; gap: 20px; }
.hero-kicker {
  display: inline-block; font-size: 12px; letter-spacing: 3px; opacity: 0;
  animation: kickerIn .7s ease-out forwards;
}
@keyframes kickerIn {
  from { opacity: 0; letter-spacing: 10px; }
  to { opacity: .85; letter-spacing: 3px; }
}
.hero-title { margin: 8px 0 6px; font-size: 30px; letter-spacing: 2px; font-weight: 800; line-height: 1.35; }
.ht-ch { display: inline-block; opacity: 0; transform: translateY(16px); animation: charIn .55s cubic-bezier(.22, .9, .3, 1.2) forwards; }
@keyframes charIn {
  to { opacity: 1; transform: translateY(0); }
}
.hero-sub { margin: 0; font-size: 14px; opacity: 0; transform: translateY(10px); animation: subIn .7s ease-out forwards; }
.hero-sub.sub2 { font-size: 12.5px; opacity: 0; margin-top: 4px; color: rgba(255, 255, 255, .82); }
@keyframes subIn {
  to { opacity: .92; transform: translateY(0); }
}
.hero-seal {
  flex: none; width: 64px; height: 64px; border: 3px solid rgba(255, 255, 255, .85);
  display: grid; place-items: center; border-radius: 10px; font-size: 30px; font-weight: 800;
  transform: rotate(8deg); color: #ffe9c9; background: rgba(126, 36, 24, .35);
  opacity: 0; animation: sealIn .8s cubic-bezier(.3, 1.4, .5, 1) .25s forwards, sealFloat 5s ease-in-out 1.4s infinite;
}
@keyframes sealIn {
  0% { opacity: 0; transform: scale(.5) rotate(-24deg); }
  60% { opacity: 1; transform: scale(1.12) rotate(12deg); }
  100% { opacity: 1; transform: scale(1) rotate(8deg); }
}
@keyframes sealFloat {
  0%, 100% { transform: rotate(8deg); }
  50% { transform: rotate(11deg) translateY(-3px); }
}
.hero-fret {
  position: absolute; inset: -40px; z-index: 1; pointer-events: none; opacity: .16;
  background-image:
    repeating-linear-gradient(45deg, transparent 0 18px, rgba(255, 255, 255, .5) 18px 20px),
    repeating-linear-gradient(-45deg, transparent 0 18px, rgba(255, 255, 255, .5) 18px 20px);
  mask-image: linear-gradient(to bottom, transparent, #000 40%);
  animation: fretDrift 26s linear infinite;
}
@keyframes fretDrift {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(40px, 40px, 0); }
}

/* ---- 布局 ---- */
.heritage-layout { display: grid; grid-template-columns: minmax(300px, 380px) 1fr; gap: 16px; align-items: start; }
.heritage-col { display: grid; gap: 16px; }
.heritage-col .ys-card { animation: cardUp .6s ease-out both; }
.heritage-col:nth-child(1) .ys-card:nth-child(1) { animation-delay: 1.25s; }
.heritage-col:nth-child(1) .ys-card:nth-child(2) { animation-delay: 1.4s; }
.heritage-col:nth-child(2) .ys-card:nth-child(1) { animation-delay: 1.32s; }
.heritage-col:nth-child(2) .ys-card:nth-child(2) { animation-delay: 1.47s; }
@keyframes cardUp {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-head .ys-title { margin: 0; font-size: 17px; }
.card-tip { margin: -6px 0 12px; font-size: 12px; color: var(--ys-ink-3); line-height: 1.7; }
.hint-sub { margin-top: 6px; color: var(--ys-red-deep); font-size: 12px; }
.card-badge {
  font-size: 12px; color: var(--ys-red-deep); border: 1px solid var(--ys-red);
  border-radius: 12px; padding: 2px 10px; background: rgba(169, 50, 38, .06);
}
.action-btn { width: 100%; margin-top: 4px; }

/* ---- 画像 ---- */
.profile-stats { display: flex; gap: 10px; margin: 6px 0 12px; }
.stat { text-align: center; flex: 1; border: 1px solid var(--ys-line); border-radius: 10px; padding: 12px 6px; background: #fffdf8; }
.stat b { display: block; font-size: 26px; color: var(--ys-red-deep); }
.stat span { font-size: 12px; color: var(--ys-ink-3); }
.focus-block { margin: 4px 0 12px; }
.focus-label { font-size: 12px; color: var(--ys-ink-3); display: block; margin-bottom: 6px; }
.focus-list { display: flex; flex-wrap: wrap; gap: 6px; }
.heritage-empty { padding: 26px 10px; }
.empty-icon {
  width: 52px; height: 52px; margin: 0 auto 10px; border-radius: 50%;
  display: grid; place-items: center; font-size: 26px; color: var(--ys-red);
  border: 2px solid var(--ys-red); opacity: .8;
}

/* ---- 学习方案 ---- */
.plan-text {
  background: #fffdf8; border: 1px solid var(--ys-line); border-left: 4px solid var(--ys-red);
  border-radius: 8px; padding: 14px 16px; font-family: inherit; line-height: 1.9;
  white-space: pre-wrap; font-size: 14px; margin: 0;
}
.plan-hint { color: var(--ys-ink-3); font-size: 13px; line-height: 1.9; margin: 0; }

/* ---- 科普卡片 ---- */
.card-foot { display: flex; justify-content: space-between; align-items: center; }
.card-preview { margin-top: 16px; display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }
.card-art {
  width: 100%; max-width: 380px; background: linear-gradient(160deg, #7e2418, #a93226 60%, #b98a2f);
  color: #fff; border-radius: 12px; padding: 28px; min-height: 300px;
  display: flex; flex-direction: column; border: 4px double rgba(255, 255, 255, 0.4);
  box-shadow: 0 8px 20px rgba(122, 58, 32, .18);
}
.card-art.modern { background: linear-gradient(160deg, #2f6b5e, #2f2a24); border: none; }
.card-brand { align-self: flex-end; font-size: 13px; opacity: 0.9; }
.card-art h3 { margin: 20px 0 12px; font-size: 24px; }
.card-art p { flex: 1; font-size: 15px; line-height: 1.9; }
.card-meta { display: flex; justify-content: space-between; font-size: 12px; opacity: 0.9; }
.watermark { font-size: 11px; }

/* ---- 承诺书 ---- */
.commitment-body { position: relative; }
.commitment-seal {
  position: absolute; top: -6px; right: -4px; width: 52px; height: 52px;
  border: 3px solid var(--ys-red); color: var(--ys-red); display: grid; place-items: center;
  border-radius: 8px; font-size: 26px; font-weight: 700; transform: rotate(10deg);
  opacity: .8; background: rgba(169, 50, 38, .05);
}
.commitment-text {
  font-size: 15px; line-height: 2.1; padding: 18px 20px; border-left: 4px solid var(--ys-red);
  background: #fffdf8; border-radius: 8px; margin: 0 0 10px;
}

@media (max-width: 960px) {
  .heritage-layout { grid-template-columns: 1fr; }
  .hero-title { font-size: 24px; }
}
</style>
