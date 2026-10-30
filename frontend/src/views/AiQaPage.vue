<template>
  <div class="aiqa-page">
    <PageHero title="AI 智能溯源问答" kicker="AI Q&A · 溯源对话" sub="AI 权威溯源解答 + 社区勘误补充 · 每一个回答都可溯源、可纠错" seal="问" />

    <div class="qa-layout anim-stagger">
      <div class="qa-main">
        <!-- 对话式溯源问答（接入豆包大模型，可连续追问） -->
        <div class="ask-card ys-card chat-card">
          <div class="chat-head">
            <span class="ai-badge">AI 溯源对话</span>
            <span class="chat-sub">已接入豆包大模型 · 可连续追问 · 回答可溯源</span>
            <el-button v-if="userStore.token" size="small" text type="danger" class="chat-clear-btn" @click="clearChat">清空对话</el-button>
          </div>
          <div ref="chatBox" class="chat-box">
            <div v-if="!chatMsgs.length" class="chat-welcome">
              <p>向衣源溯起提问任何与华夏服饰相关的问题，例如：</p>
              <p class="welcome-examples">「马面裙和百褶裙有什么区别？」「唐代女子日常穿什么？」「香云纱是什么面料？」</p>
            </div>
            <template v-for="(m, i) in chatMsgs" :key="i">
              <div :class="['chat-row', m.role]">
                <div class="chat-bubble">
                  <template v-if="m.role === 'assistant'">
                    <span class="chat-ai-tag">AI溯源</span>
                  </template>
                  <img v-if="m.image" class="chat-thumb" :src="m.image" alt="截图" />
                  <p class="chat-content">
                    <template v-for="(seg, si) in contentSegments(m)" :key="si">
                      <component :is="seg.source.external ? 'a' : RouterLink" v-if="seg.source"
                                 v-bind="linkAttrs(seg.source)" class="code-ref">{{ seg.text }}</component>
                      <template v-else>{{ seg.text }}</template>
                    </template>
                  </p>
                  <div v-if="m.sources?.length" class="src-row">
                    <span class="chat-ref">引用：</span>
                    <component :is="s.external ? 'a' : RouterLink" v-for="s in m.sources" :key="s.type + s.id"
                               v-bind="linkAttrs(s)" class="src-chip">
                      {{ s.title }} · {{ s.code }}
                    </component>
                  </div>
                  <p v-else-if="m.ref" class="chat-ref">引用：{{ m.ref }}</p>
                  <div v-if="m.role === 'assistant' && m.question" class="chat-actions">
                    <el-button size="small" text type="warning" @click="publishChat(m)">存为社区问题 ↗</el-button>
                  </div>
                </div>
              </div>
              <!-- 答后推荐检索：四类站内资料卡 + 推荐追问 -->
              <div v-if="m.rec" class="chat-row assistant">
                <div class="rec-wrap" data-lb-native>
                  <template v-if="m.rec.cards?.length">
                    <p class="rec-head">相关资料 · 来自站内档案</p>
                    <div class="rec-cards">
                      <component :is="c.external ? 'a' : RouterLink" v-for="c in m.rec.cards" :key="c.type + c.id"
                                 v-bind="linkAttrs(c)" class="rec-card">
                        <img v-if="c.image_url" :src="c.image_url" :alt="c.title" loading="lazy" />
                        <span v-else class="rec-noimg">{{ c.title.slice(0, 4) }}</span>
                        <span class="rec-type">{{ REC_TYPE_LABEL[c.type] || "资料" }}<i v-if="!c.exact"> · 非精确</i></span>
                        <b>{{ c.title }}</b>
                        <i>{{ c.code }}{{ c.subtitle ? " · " + c.subtitle : "" }}</i>
                      </component>
                    </div>
                  </template>
                  <div v-if="m.rec.asks?.length" class="ask-row">
                    <span class="rec-head">你可能还想问</span>
                    <button v-for="a in m.rec.asks" :key="a" class="ask-chip" @click="askFollowup(a)">{{ a }}</button>
                  </div>
                </div>
              </div>
            </template>
            <div v-if="chatting" class="chat-row assistant">
              <div class="chat-bubble">
                <span class="chat-ai-tag">AI溯源</span>
                <p class="chat-content">正在考据史料，请稍候…</p>
              </div>
            </div>
          </div>
          <div v-if="pendingImage" class="pending-img">
            <img :src="pendingImage" alt="待发截图" />
            <button class="pending-clear" @click="pendingImage = ''" title="移除">×</button>
          </div>

          <!-- AI 快捷功能 -->
          <div class="ai-quick-actions">
            <button class="quick-btn" @click="quickAction('poem')">
              <span class="quick-icon">✍️</span>
              <span class="quick-name">AI 服饰写诗</span>
              <span class="quick-desc">为选中服饰配一首古诗词</span>
            </button>
            <button class="quick-btn" @click="quickAction('compare')">
              <span class="quick-icon">⚖️</span>
              <span class="quick-name">AI 朝代对比</span>
              <span class="quick-desc">对比两个朝代服饰差异</span>
            </button>
            <button class="quick-btn" @click="quickAction('outfit')">
              <span class="quick-icon">👗</span>
              <span class="quick-name">AI 穿搭推荐</span>
              <span class="quick-desc">根据场合推荐汉服搭配</span>
            </button>
            <button class="quick-btn" @click="quickAction('pattern')">
              <span class="quick-icon">🎨</span>
              <span class="quick-name">AI 纹样生成</span>
              <span class="quick-desc">描述风格生成传统纹样</span>
            </button>
            <button class="quick-btn" @click="quickAction('restore')">
              <span class="quick-icon">🏺</span>
              <span class="quick-name">AI 服饰复原</span>
              <span class="quick-desc">上传残片推测完整服饰</span>
            </button>
          </div>

          <div class="chat-input-row">
            <input ref="fileInput" type="file" accept="image/*" hidden @change="onPickImage" />
            <button class="attach-btn" title="上传截图/照片" :disabled="chatting" @click="fileInput?.click()">📎</button>
            <el-input v-model="chatInput" type="textarea" :rows="2" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="输入问题，可粘贴服饰截图让 AI 识图…" @keydown.enter.exact.prevent="sendChat" />
            <el-button type="primary" :loading="chatting" @click="sendChat">发送</el-button>
          </div>

          <!-- 智能推荐问题 -->
          <div class="smart-suggest">
            <span class="ss-label">💡 你可能想问：</span>
            <button v-for="s in smartSuggestions.slice(0, 4)" :key="s" class="ss-chip" @click="chatInput = s">{{ s }}</button>
          </div>

          <!-- 全网相关资讯 -->
          <div v-if="webQaItems !== null" class="web-qa">
            <div class="web-head">
              <span class="web-badge">全网</span>
              “{{ webQaKeyword }}” 相关资讯 · {{ webQaItems.length }} 条
              <el-button text size="small" @click="loadQaWeb">刷新</el-button>
            </div>
            <a v-for="(r, i) in webQaItems" :key="i" class="web-item" :href="r.url" target="_blank" rel="noopener noreferrer">
              <b>{{ r.title }}</b><span>{{ r.source }} · 原文 ↗</span>
            </a>
            <div v-if="!webQaItems.length" class="ys-empty">全网暂无相关资讯</div>
          </div>
        </div>

        <!-- 问题列表 -->
        <h3 class="ys-title" style="margin-top: 20px">社区问题</h3>
        <div v-loading="loading" class="question-list">
          <div v-for="q in questions" :key="q.id" class="question-card ys-card" @click="openQuestion(q.id)">
            <div class="q-head">
              <h4>{{ q.title }}</h4>
              <span class="q-meta">
                <span class="q-user">提问 {{ q.user_name }}</span>
                <span class="q-time">{{ q.create_time?.slice(0, 10) }}</span>
                <el-button
                  v-if="userStore.token && q.user_id === myUserId"
                  size="small" text type="danger" class="q-del-btn" @click.stop="removeQuestion(q)">删除</el-button>
              </span>
            </div>
            <div class="q-tags" v-if="q.dynasty_tags">
              <span class="ys-tag">{{ q.dynasty_tags }}</span>
            </div>
            <div class="q-ai-preview">
              <span class="ai-badge">AI</span>{{ q.ai_answer }}
            </div>
          </div>
          <div v-if="!loading && !questions.length" class="ys-empty">暂无问题，成为第一个提问者</div>
        </div>
      </div>

      <aside class="qa-side">
        <div class="ys-card">
          <h3 class="ys-title">档案编号查找</h3>
          <p class="side-text" style="font-size:12px;color:#999;margin-bottom:10px">输入档案编号快速跳转，如 0009、档案-0009、衣制-09</p>
          <div class="lookup-row">
            <el-input v-model="lookupCode" placeholder="输入编号…" size="default" @keyup.enter="goLookup" />
            <el-button type="primary" @click="goLookup">跳转</el-button>
          </div>
          <div v-if="lookupResult" class="lookup-result" v-html="lookupResult"></div>
        </div>

        <div class="ys-card">
          <h3 class="ys-title">社区勘误机制</h3>
          <p class="side-text">
            用户可对任何回答提交补充与纠错；系统通过 AI 纠错标记者检测回答与权威知识库的冲突，
            保障社区科普内容的严谨性。
          </p>
          <el-divider />
          <h4>AI 三重角色</h4>
          <ul class="role-list">
            <li>初步回答生成者（RAG 知识库）</li>
            <li>辅助回答者（提供史料参考）</li>
            <li>纠错标记者（冲突检测）</li>
          </ul>
        </div>
      </aside>
    </div>

    <!-- 问题详情对话框 -->
    <el-dialog v-model="detailVisible" :title="questionDetail?.title" width="760px">
      <div v-if="questionDetail">
        <div class="ai-block">
          <span class="ai-badge">AI溯源回答</span>
          <p class="ai-text">{{ questionDetail.ai_answer }}</p>
          <p class="ai-ref">引用：{{ questionDetail.ai_source_ref }}</p>
        </div>
        <el-divider />
        <h4>社区回答（{{ questionDetail.answers?.length || 0 }}）</h4>
        <div v-for="a in questionDetail.answers" :key="a.id" class="answer-item">
          <div class="a-head">
            <span :class="{ 'is-ai': a.is_ai_answer }">{{ a.is_ai_answer ? "AI" : `用户 #${a.user_id}` }}</span>
            <el-button size="small" text type="warning" @click="verify(a.id)">AI纠错检测</el-button>
          </div>
          <p class="a-content">{{ a.content }}</p>
          <p v-if="a.source_ref" class="ai-ref">引用：{{ a.source_ref }}</p>
        </div>
        <div v-if="!questionDetail.answers?.length" class="ys-empty">暂无社区回答</div>
        <el-input v-model="myAnswer" type="textarea" :rows="2" placeholder="补充你的回答 / 勘误" style="margin-top: 10px" />
        <div class="dialog-foot" style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center">
          <el-button type="warning" plain :loading="toPosting" @click="toPost">
            转社区讨论 ↗
          </el-button>
          <el-button type="primary" @click="submitAnswer">提交回答</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { createQuestion, fetchAiChat, fetchAiRecommend, fetchQuestions, fetchQuestionDetail, addAnswer, aiVerifyAnswer, fetchWebSearch, questionToPost, deleteQuestion, fetchMe } from "@/api/modules";
import PageHero from "@/components/PageHero.vue";
import { useUserStore } from "@/store/user";

const router = useRouter();
const userStore = useUserStore();
const toPosting = ref(false);

/* ---- 对话式溯源问答 ---- */
const CHAT_KEY = "yisu_aiqa_chat_v1";
const WEBQA_KEY = "yisu_aiqa_webqa_v1";

function loadChat(): any[] {
  try { const v = JSON.parse(localStorage.getItem(CHAT_KEY) || "[]"); return Array.isArray(v) ? v : []; } catch { return []; }
}
function persistChat() {
  try { localStorage.setItem(CHAT_KEY, JSON.stringify(chatMsgs.value.slice(-60))); } catch { /* ignore */ }
}

const chatInput = ref("");
const chatting = ref(false);
const chatMsgs = ref<any[]>(loadChat());
const chatBox = ref<HTMLElement | null>(null);
const pendingImage = ref("");
const lookupCode = ref("");
const lookupResult = ref("");

async function goLookup() {
  const code = lookupCode.value.trim();
  if (!code) return;
  lookupResult.value = "搜索中…";
  try {
    const res: any = await fetch(`/api/archive/lookup?code=${encodeURIComponent(code)}`);
    const data = await res.json();
    if (data.found) {
      lookupResult.value = `✅ 找到：<b>${data.title}</b>（${data.code}）<br><a href="${data.url}" target="_blank">查看详情 ↗</a>`;
    } else {
      lookupResult.value = "❌ 未找到该编号，请检查后重试";
    }
  } catch {
    lookupResult.value = "搜索失败，请稍后重试";
  }
}
const fileInput = ref<HTMLInputElement | null>(null);

function readImageFile(f: File) {
  const r = new FileReader();
  r.onload = () => { pendingImage.value = String(r.result); };
  r.readAsDataURL(f);
}
function onPickImage(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0];
  if (f) readImageFile(f);
  (e.target as HTMLInputElement).value = "";
}
function onPaste(e: ClipboardEvent) {
  const item = [...(e.clipboardData?.items || [])].find((it) => it.type.startsWith("image/"));
  if (!item) return;
  const f = item.getAsFile();
  if (f) { readImageFile(f); e.preventDefault(); }
}
const questions = ref<any[]>([]);
const loading = ref(false);
const route = useRoute();

const detailVisible = ref(false);
const questionDetail = ref<any>(null);
const myAnswer = ref("");
const myUserId = ref<number | null>(null);

/** 登录后获取当前用户 id，用于显示"仅自己的问题可删除" */
onMounted(async () => {
  if (userStore.token) {
    try {
      const me: any = await fetchMe();
      myUserId.value = me?.id ?? null;
    } catch { /* 忽略 */ }
  }
});

function scrollChat() {
  setTimeout(() => {
    chatBox.value?.scrollTo({ top: chatBox.value.scrollHeight, behavior: "smooth" });
  }, 60);
}

/** 从用户问题中提取全网搜索关键词：优先引号内容 → 去疑问词 → 截前6字 */
function pickKeyword(q: string) {
  const m = q.match(/[“"「『]([^”"」』]{1,12})[”"」』]/);
  if (m) return m[1];
  let s = q.replace(/[，。？?、！!：:；;·\s"'“”‘’]/g, "");
  s = s.replace(/(为什么|怎么|是什么|有啥|有什么区别|区别|如何|多少|哪些|哪个|怎样|它|他|她|吗|呢|吧|的|了|与|和)/g, "");
  return s.slice(0, 6) || q.replace(/[，。？?、！!：:；;·\s"'“”‘’]/g, "").slice(0, 6);
}

const quickPrompts: Record<string, string[]> = {
  poem: [
    "请为一件明代马面裙写一首七言绝句，要体现它的形制特点和文化寓意。",
    "请为唐代齐胸襦裙写一首五言律诗，描绘它飘逸的美感。",
    "请为清代旗袍写一首词，词牌自选，体现它的曲线美。",
    "请为宋代褙子写一首七言绝句，体现它清雅素净的风格。",
  ],
  compare: [
    "请对比唐代和宋代女子常服在形制、色彩、面料上的主要区别，分点说明。",
    "请对比明代和清代女子服饰的主要差异，从形制、装饰、穿着场合三方面分析。",
    "请对比汉服和和服在版型、系带方式、穿着场合上的区别。",
    "请对比先秦深衣和后世汉服的形制传承与演变。",
  ],
  outfit: [
    "我要参加一个传统汉服文化活动，请帮我搭配一套适合春季的宋制汉服，包括上衣、下裙、配饰和面料建议。",
    "我要参加婚礼做伴娘，请帮我选一套明制汉服，要求端庄大气，给出具体搭配方案。",
    "夏天快到了，请推荐一套适合日常穿着的轻量化汉服，要透气舒适。",
    "我要拍一组古风写真，请帮我搭配一套魏晋风汉服，给出妆造和道具建议。",
  ],
  pattern: [
    "请描述一种适合用在明代女子襦裙上的传统纹样，要求：名称、寓意、常见配色、构图特点。",
    "请详细介绍唐代盛行的卷草纹，包括它的起源、寓意和典型应用场景。",
    "请描述云纹在中国传统服饰中的演变历史，从先秦到明清各有什么特点。",
    "请介绍百子图纹的寓意和常见使用场景，为什么它常出现在婚服上。",
  ],
  restore: [
    "假设我有一块出土的唐代半臂残片，上面能看到卷草纹和红色颜料痕迹，请推测这件半臂的完整形制、面料和穿着场合。",
    "假设我发现了一块战国时期的锦袍残片，上面有龙凤纹，请推测完整形制和使用者身份。",
    "假设我有一件明代披风的残片，面料是织金缎，请复原它的完整样式和穿着场景。",
    "假设出土了一件汉代曲裾深衣的彩绘俑，请根据俑像复原它的剪裁结构和穿着方式。",
  ],
};

const smartSuggestions = [
  "马面裙为什么在明代流行？",
  "汉服的交领右衽有什么讲究？",
  "香云纱是怎么制作的？",
  "唐代女子为什么喜欢穿齐胸襦裙？",
  "为什么旗袍在民国成为国服？",
  "汉服和胡服有什么相互影响？",
  "传统汉服的颜色等级怎么区分？",
  "深衣为什么被称为圣人之服？",
];

function quickAction(type: string) {
  const arr = quickPrompts[type] || [];
  if (!arr.length) return;
  chatInput.value = arr[Math.floor(Math.random() * arr.length)];
}

async function sendChat() {
  const q = chatInput.value.trim();
  if (chatting.value) return;
  if (!q && !pendingImage.value) return;
  const b64 = pendingImage.value;
  chatMsgs.value.push({ role: "user", content: q || "（看图识服饰）", image: b64 });
  pendingImage.value = "";
  persistChat();
  chatInput.value = "";
  chatting.value = true;
  try {
    const history = chatMsgs.value.slice(0, -1).map((m) => ({ role: m.role, content: m.content }));
    const res: any = await fetchAiChat({ question: q, history, image_base64: b64 });
    chatMsgs.value.push({
      role: "assistant", content: res.answer, ref: res.source_ref,
      sources: res.sources || [], question: q, imageNote: res.image_note || "",
    });
    persistChat();
    loadRecommend(chatMsgs.value.length - 1, q);
    webQaKeyword.value = q;
    await loadQaWeb();
  } catch {
    chatMsgs.value.push({ role: "assistant", content: "（服务暂不可用，请稍后再试）", ref: "", question: q });
    persistChat();
  } finally {
    chatting.value = false;
    scrollChat();
  }
}

const REC_TYPE_LABEL: Record<string, string> = {
  costume: "服饰档案", pattern: "纹样", fabric: "面料", news: "资讯", accessory: "配饰",
};

const CODE_SPLIT = /(〔[^〔〕]+〕)/g;

/** 答案正文切段：只有本次引用里出现过的〔编号〕才做成链接，模型自己编的留纯文本 */
function contentSegments(m: any): { text: string; source: any | null }[] {
  const known: Record<string, any> = {};
  for (const s of m.sources || []) known[s.code] = s;
  return String(m.content || "").split(CODE_SPLIT).reduce<{ text: string; source: any | null }[]>((acc, piece) => {
    if (!piece) return acc;
    const source = piece.startsWith("〔") && piece.endsWith("〕") ? known[piece.slice(1, -1).trim()] : null;
    acc.push({ text: piece, source: source || null });
    return acc;
  }, []);
}

/** 配饰九卷是独立静态子页，不在单页路由表里，得用普通链接跳 */
function linkAttrs(item: { link: string; external?: boolean }) {
  return item.external ? { href: item.link } : { to: item.link };
}

/** 答后推荐：抽词命中站内资料则出卡；拉不到或没料就不占位，不打断对话 */
async function loadRecommend(index: number, q: string) {
  try {
    const data: any = await fetchAiRecommend({ q });
    const cards = data?.cards || [];
    const asks = data?.asks || [];
    if (!cards.length && !asks.length) return;
    chatMsgs.value[index] = { ...chatMsgs.value[index], rec: { keywords: data?.keywords || [], cards, asks } };
    persistChat();
  } catch { /* 静默失败 */ }
}

/** 点追问 = 直接把这句话发出去 */
function askFollowup(text: string) {
  if (chatting.value) return;
  chatInput.value = text;
  sendChat();
}

/** 清空本地对话记录（仅登录后可操作） */
async function clearChat() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  try {
    await ElMessageBox.confirm("确定清空全部对话记录吗？此操作不可恢复。", "清空对话", { type: "warning", confirmButtonText: "清空", cancelButtonText: "取消" });
  } catch { return; }
  chatMsgs.value = [];
  try { localStorage.removeItem(CHAT_KEY); } catch { /* ignore */ }
  ElMessage.success("对话记录已清空");
}

/** 删除问题（仅提问者本人或管理员），级联删除回答与同步社区帖 */
async function removeQuestion(q: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  try {
    await ElMessageBox.confirm(`确定删除问题「${q.title}」吗？其回答与同步到社区的帖子将一并删除。`, "删除问题", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch { return; }
  try {
    await deleteQuestion(q.id);
    ElMessage.success("问题已删除");
    load();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败");
  }
}

async function publishChat(m: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  const created: any = await createQuestion({ title: m.question.slice(0, 50), content: "", dynasty_tags: "" });
  if (created?.id) await questionToPost(created.id);
  ElMessage.success("已发布到社区「形制溯源」板块，可去社区参与讨论");
  load();
}

async function load() {
  loading.value = true;
  try {
    const data: any = await fetchQuestions({ page: 1, page_size: 20 });
    questions.value = data.items;
  } finally { loading.value = false; }
}

const webQaItems = ref<any[] | null>(null);
const webQaKeyword = ref("");
try { const w = JSON.parse(localStorage.getItem(WEBQA_KEY) || "{}"); if (w && w.keyword) webQaKeyword.value = w.keyword; } catch { /* ignore */ }

async function loadQaWeb() {
  if (!webQaKeyword.value) return;
  try {
    const data: any = await fetchWebSearch({ keyword: webQaKeyword.value, limit: 5 });
    webQaItems.value = data.items || [];
    try { localStorage.setItem(WEBQA_KEY, JSON.stringify({ keyword: webQaKeyword.value })); } catch { /* ignore */ }
  } catch {
    webQaItems.value = [];
  }
}

async function openQuestion(id: number) {
  questionDetail.value = await fetchQuestionDetail(id) as any;
  detailVisible.value = true;
  myAnswer.value = "";
}

async function toPost() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (!questionDetail.value) return;
  toPosting.value = true;
  try {
    const res: any = await questionToPost(questionDetail.value.id);
    ElMessage.success(`已转为社区讨论帖（${res.board_name}），正在跳转…`);
    detailVisible.value = false;
    router.push(`/community?post=${res.post_id}`);
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "转换失败");
  } finally {
    toPosting.value = false;
  }
}

async function submitAnswer() {
  if (!myAnswer.value.trim() || !questionDetail.value) return;
  await addAnswer(questionDetail.value.id, myAnswer.value);
  ElMessage.success("回答已提交，感谢参与社区共治");
  myAnswer.value = "";
  questionDetail.value = await fetchQuestionDetail(questionDetail.value.id) as any;
}

async function verify(aid: number) {
  const res: any = await aiVerifyAnswer(aid);
  ElMessage[res.conflict_detected ? "warning" : "success"](res.verdict);
}

onMounted(async () => {
  window.addEventListener("paste", onPaste);
  await load();
  // 恢复上次对话：滚动到底部 + 重刷全网资讯
  scrollChat();
  if (webQaKeyword.value) loadQaWeb();
  // 支持 ?question=id 直达：从个人中心"我的问答"点击跳转时自动打开对应问答详情
  const qid = Number(route.query.question);
  if (qid > 0) {
    await openQuestion(qid);
    history.replaceState(null, "", "/aiqa");
  }
});
</script>

<style scoped>
.page-sub { color: var(--ys-ink-3); margin: -6px 0 16px; }
.qa-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 16px; }
.ask-foot { display: flex; justify-content: space-between; align-items: center; }
.ai-answer { margin-top: 14px; border: 1px solid var(--ys-line); border-left: 4px solid var(--ys-red); border-radius: 8px; padding: 14px; background: #fffdf8; }
.ai-badge { background: var(--ys-red); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; margin-right: 6px; }
.ai-text { line-height: 1.8; color: var(--ys-ink-2); margin: 8px 0; }
.ai-ref { font-size: 12px; color: var(--ys-ink-3); }
.ai-note { font-size: 12px; color: var(--ys-red-deep); }
.web-qa { margin-top: 14px; padding: 12px 14px 0; border-top: 1px dashed var(--ys-line); }
.web-head { display: flex; align-items: center; gap: 8px; font-size: 13px; flex-wrap: wrap; }
.web-badge { background: var(--ys-red); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; margin-right: 6px; }
.web-item { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 8px 4px; border-bottom: 1px dashed var(--ys-line); font-size: 14px; color: var(--ys-ink-1); }
.web-item:hover { color: var(--ys-red-deep); }
.web-item span { color: var(--ys-ink-3); font-size: 12px; flex-shrink: 0; }
.question-card { cursor: pointer; }
.question-card:hover { transform: translateY(-1px); }
.q-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.q-head h4 { margin: 0; }
.q-meta { display: flex; align-items: baseline; gap: 10px; flex-shrink: 0; }
.q-del-btn { margin-left: 4px; }
.q-user { color: var(--ys-red-deep); font-size: 12px; }
.q-time { color: var(--ys-ink-3); font-size: 12px; }
.q-ai-preview { margin-top: 8px; font-size: 13px; color: var(--ys-ink-3); line-height: 1.7; }
.qa-side { display: flex; flex-direction: column; }
.side-text { font-size: 13px; line-height: 1.8; color: var(--ys-ink-2); }
.lookup-row { display: flex; gap: 8px; margin-bottom: 10px; }
.lookup-row .el-input { flex: 1; }
.lookup-result { font-size: 13px; line-height: 1.8; padding: 10px; background: rgba(201,162,39,.06); border-radius: 8px; }
.lookup-result a { color: #c9a227; }
.smart-suggest { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 10px; }
.ss-label { font-size: 12px; color: #999; }
.ss-chip { background: rgba(201,162,39,.08); border: 1px solid rgba(201,162,39,.2); border-radius: 999px; padding: 4px 12px; font-size: 12px; color: #7a221c; cursor: pointer; transition: all .2s; }
.ss-chip:hover { background: rgba(201,162,39,.18); border-color: rgba(201,162,39,.4); }
.role-list { margin: 0; padding-left: 18px; color: var(--ys-ink-2); font-size: 13px; line-height: 2; }
.ai-block { border-left: 4px solid var(--ys-red); padding: 10px 14px; background: #fffdf8; border-radius: 8px; }
.answer-item { border-bottom: 1px dashed var(--ys-line); padding: 10px 0; }
.a-head { display: flex; justify-content: space-between; align-items: center; }
.a-head span { font-size: 12px; color: var(--ys-ink-3); background: #eee5d2; padding: 1px 8px; border-radius: 10px; }
.a-head .is-ai { background: var(--ys-red); color: #fff; }
.a-content { line-height: 1.7; margin: 6px 0; }

/* ---- 对话式溯源问答 ---- */
.chat-card { padding: 16px 18px; }
.chat-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.chat-sub { font-size: 12px; color: var(--ys-ink-3); margin-right: auto; }
.chat-clear-btn { flex-shrink: 0; }
.chat-box { max-height: 480px; min-height: 220px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 4px 2px 8px; }
.chat-welcome { color: var(--ys-ink-3); font-size: 13px; line-height: 1.9; padding: 18px 6px; }
.welcome-examples { color: var(--ys-red-deep); margin: 4px 0 0; }
.chat-row { display: flex; }
.chat-row.user { justify-content: flex-end; }
.chat-row.assistant { justify-content: flex-start; }
.chat-bubble { max-width: 86%; padding: 10px 14px; border-radius: 12px; line-height: 1.75; font-size: 14px; }
.chat-row.user .chat-bubble { background: linear-gradient(135deg, #a8322c, #c74b3f); color: #fff; border-bottom-right-radius: 4px; }
.chat-row.assistant .chat-bubble { background: #fffdf6; border: 1px solid var(--ys-line); border-bottom-left-radius: 4px; }
.chat-ai-tag { display: inline-block; background: var(--ys-red); color: #fff; font-size: 11px; padding: 1px 8px; border-radius: 10px; margin-bottom: 6px; }
.chat-content { margin: 0; white-space: pre-wrap; word-break: break-word; }
.chat-ref { margin: 8px 0 0; font-size: 12px; color: var(--ys-ink-3); }
.src-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 8px; }
.src-chip { display: inline-flex; align-items: center; min-height: 26px; padding: 2px 10px; border: 1px solid var(--ys-line); border-radius: 16px; background: #fffdf6; color: var(--ys-red-deep); font-size: 12px; text-decoration: none; }
.src-chip:hover { border-color: var(--ys-red); color: var(--ys-red); }
.code-ref { color: var(--ys-red-deep); text-decoration: none; border-bottom: 1px dashed var(--ys-red); }
.code-ref:hover { color: var(--ys-red); }
.chat-actions { margin-top: 8px; }
.ai-quick-actions { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-top: 12px; }
.quick-btn { background: rgba(201,162,39,.08); border: 1px solid rgba(201,162,39,.25); border-radius: 10px; padding: 10px 8px; cursor: pointer; text-align: center; transition: all .2s; }
.quick-btn:hover { background: rgba(201,162,39,.16); border-color: rgba(201,162,39,.5); transform: translateY(-1px); }
.quick-icon { font-size: 20px; display: block; margin-bottom: 4px; }
.quick-name { display: block; font-size: 13px; font-weight: 600; color: #7a221c; margin-bottom: 2px; }
.quick-desc { display: block; font-size: 11px; color: #999; line-height: 1.3; }
@media (max-width: 768px) { .ai-quick-actions { grid-template-columns: repeat(2, 1fr); } }

.chat-input-row { display: flex; gap: 10px; align-items: center; margin-top: 12px; }
.chat-input-row .el-input { flex: 1; }
.attach-btn {
  flex: none; width: 40px; height: 40px; border-radius: 8px;
  border: 1px solid var(--ys-line, #e5d9c3); background: #fffdf8;
  cursor: pointer; font-size: 18px;
}
.attach-btn:hover:not(:disabled) { background: #f6ecd4; }
.pending-img { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.pending-img img { width: 56px; height: 56px; object-fit: cover; border-radius: 8px; border: 1px solid var(--ys-line, #e5d9c3); }
.pending-clear { border: none; background: #7a221c; color: #fff; width: 20px; height: 20px; border-radius: 50%; cursor: pointer; }
.chat-thumb { max-width: 180px; max-height: 180px; border-radius: 8px; margin: 0 0 6px; display: block; border: 1px solid var(--ys-line, #e5d9c3); }

/* ---- 答后推荐检索 ---- */
.rec-wrap { width: 100%; max-width: 86%; min-width: 0; display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.rec-head { margin: 0; font-size: 12px; color: var(--ys-ink-3); }
.rec-cards { display: grid; grid-auto-flow: column; grid-auto-columns: 150px; gap: 8px; overflow-x: auto; min-width: 0; padding-bottom: 4px; }
.rec-card { display: flex; flex-direction: column; border: 1px solid var(--ys-line); border-radius: 8px; overflow: hidden; background: #fffdf6; color: var(--ys-ink-1); text-decoration: none; }
.rec-card:hover { border-color: var(--ys-red); }
.rec-card img { display: block; width: 100%; height: 84px; object-fit: cover; background: #eee5d2; }
.rec-noimg { display: grid; place-items: center; height: 84px; background: #eee5d2; color: var(--ys-red-deep); font-size: 13px; }
.rec-type { align-self: flex-start; margin: 6px 8px 0; font-size: 10px; color: var(--ys-red); }
.rec-type i { font-style: normal; color: var(--ys-ink-3); }
.rec-card b { padding: 2px 8px 0; font-size: 13px; line-height: 1.4; }
.rec-card > i { padding: 2px 8px 8px; font-style: normal; font-size: 11px; color: var(--ys-ink-3); line-height: 1.5; }
.ask-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.ask-chip { min-height: 44px; padding: 4px 12px; border: 1px dashed var(--ys-line); border-radius: 16px; background: #fffdf6; color: var(--ys-ink-2); font-size: 13px; cursor: pointer; }
.ask-chip:hover { color: var(--ys-red-deep); border-color: var(--ys-red); }
@media (max-width: 900px) {
  .qa-layout { grid-template-columns: minmax(0, 1fr); }
  .rec-wrap { max-width: 100%; }
  .rec-cards { grid-auto-columns: 132px; }
}
</style>
