<template>
  <div class="community-page">
    <PageHero title="国风文化共治社区" kicker="COMMUNITY · 共治共赏" sub="形制溯源 · 复原作品 · 纹样文创 · 史料求助 · 共治勘误" seal="社" />

    <!-- 版块导航 -->
    <div class="board-tabs anim-rise" style="animation-delay: .5s">
      <span v-for="b in boards" :key="b.id" class="board-tab" :class="{ active: !offlineOnly && boardId === b.id }"
            @click="switchBoard(b.id)">
        {{ b.name }}<i>{{ b.post_count }}</i>
      </span>
      <span v-if="isAdmin" class="board-tab admin-tab" :class="{ active: offlineOnly }" @click="togglePending">
        待审队列<i v-if="pendingCount">{{ pendingCount }}</i>
      </span>
    </div>

    <!-- 信息流工具条：搜索 + 排序 -->
    <div class="feed-bar anim-rise" style="animation-delay: .56s">
      <label class="feed-search">
        <span class="fs-ico">⌕</span>
        <input v-model="keyword" type="search" placeholder="搜索帖子标题，如：曲裾 / 马王堆 / 缂丝"
               @keyup.enter="loadPosts" />
        <button class="fs-go" type="button" @click="loadPosts">搜索</button>
      </label>
      <div class="sort-tabs">
        <span class="sort-tab" :class="{ active: sortMode === 'new' }" @click="sortMode = 'new'">最新</span>
        <span class="sort-tab" :class="{ active: sortMode === 'hot' }" @click="sortMode = 'hot'">最热</span>
      </div>
      <span class="feed-count" v-if="total">共 {{ total }} 帖</span>
      <span class="feed-reset" v-if="tagFilter || keyword" @click="resetFilter">清除筛选 ✕</span>
    </div>

    <div class="community-layout anim-stagger">
      <div class="post-stream">
        <div v-loading="loading" class="feed-grid">
          <!-- B 站式卡片：封面在上、标题两行、作者与数据在下 -->
          <article v-for="p in displayPosts" :key="p.id" class="vcard">
            <div class="vthumb" @click="openPost(p.id)">
              <img v-if="coverOf(p)" :src="coverOf(p)" :alt="p.title" loading="lazy" />
              <div v-else class="vthumb-fallback">
                <span class="vfb-seal">{{ boardChar(p.board_id) }}</span>
                <p v-if="quoteOf(p)" class="vfb-quote">{{ quoteOf(p) }}</p>
                <div v-else class="vfb-sign">
                  <strong>{{ boardChar(p.board_id) }}</strong>
                  <div>
                    <span class="vfb-tags">{{ tagsOf(p).slice(0, 2).join(" · ") || boardName(p.board_id) }}</span>
                    <span class="vfb-meta">纯文字帖 · {{ postChars(p) }} 字</span>
                  </div>
                </div>
                <em>{{ tagsOf(p)[0] || "国风" }}</em>
              </div>
              <span v-if="moreCount(p)" class="vmore">＋{{ moreCount(p) }}</span>
              <span v-if="p.is_pinned" class="vpin">置顶</span>
              <span class="vcat">{{ boardName(p.board_id) }}</span>
              <span class="vcmt">▤ {{ p.reply_count }}</span>
            </div>
            <div class="vbody">
              <h3 class="vtitle" @click="openPost(p.id)">{{ p.title }}</h3>
              <p class="vsum" v-if="p.content">{{ p.content }}</p>
              <div class="vfoot">
                <span class="vavt">{{ initial(p.author) }}</span>
                <span class="vau">{{ p.author }}</span>
                <span class="vtime">{{ relTime(p.create_time) }}</span>
              </div>
              <div class="vrow">
                <span class="vstat">
                  <b :class="{ on: p.liked }" @click.stop="quickLike(p)">赞 {{ p.like_count }}</b>
                  <b :class="{ on: p.collected }" @click.stop="quickCollect(p)">藏 {{ p.collect_count }}</b>
                  <b @click.stop="openRepost(p)">转 {{ p.repost_count }}</b>
                </span>
                <span v-if="isAdmin" class="vadmin">
                  <b @click.stop="p.is_pinned ? onUnpin(p.id) : onPin(p.id)">{{ p.is_pinned ? "取消置顶" : "置顶" }}</b>
                  <b class="danger" @click.stop="offlineOnly ? onOnline(p.id) : onOffline(p.id)">
                    {{ offlineOnly ? "通过" : "下架" }}
                  </b>
                </span>
                <span v-if="isMyPost(p)" class="vdel" @click.stop="confirmDelete(p)">删除</span>
              </div>
            </div>
          </article>
          <div v-if="!loading && !displayPosts.length" class="ys-empty feed-empty">
            {{ offlineOnly ? "待审队列已清空" : keyword ? "未找到匹配的帖子" : tagFilter ? `标签「${tagFilter}」下暂无帖子` : "该版块暂无帖子，来发第一帖吧" }}
          </div>
        </div>
      </div>

      <aside class="community-side">
        <div class="ys-card side-rules">
          <h3 class="ys-title">社区公约</h3>
          <ul class="rules">
            <li>讨论基于史料，标注出处</li>
            <li>勘误有理有据，严禁人身攻击</li>
            <li>分享复原作品需注明参考来源</li>
            <li>低质广告与违规内容将被审核清理</li>
          </ul>
        </div>
        <div class="ys-card">
          <h3 class="ys-title">热门标签</h3>
          <div class="side-tags">
            <span v-for="(t, i) in hotTags" :key="t" class="ys-tag hot"
                  :class="{ on: tagFilter === t }" @click="toggleTag(t)"
                  :style="{ fontSize: 12 + Math.min(6, i * 1.2) + 'px' }">{{ t }}</span>
            <span v-if="!hotTags.length" class="no-tags">暂无标签</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- 帖子详情（B 站式双栏） -->
    <el-dialog v-model="detailVisible" width="min(1080px, 95vw)" top="3vh" class="bd-dialog" destroy-on-close>
      <template #header>
        <div class="dd-topbar">
          <span class="dd-crumb">社区 / {{ postDetail?.board_name || "讨论区" }}</span>
          <span v-if="fromQa(postDetail)" class="qa-source-badge">源自溯源问答</span>
        </div>
      </template>
      <div v-if="postDetail" class="dd-grid">
        <div class="dd-main">
          <h1 class="dd-title">{{ postDetail.title }}</h1>
          <div class="dd-authorbar">
            <span class="dd-avt">{{ initial(postDetail.author) }}</span>
            <div class="dd-auinfo">
              <b>{{ postDetail.author }}</b>
              <small>{{ postDetail.create_time?.slice(0, 10) }} · {{ postDetail.board_name }}</small>
            </div>
            <div class="dd-tags">
              <span v-for="t in tagsOf(postDetail)" :key="t" class="dd-tag">{{ t }}</span>
            </div>
            <span v-if="isMyPost(postDetail)" class="vdel" @click="confirmDelete(postDetail)">删除本帖</span>
          </div>

          <div class="dd-body markdown-body" v-html="renderMarkdown(postDetail.content)"></div>
          <div v-if="imagesOf(postDetail).length" class="dd-gallery" :class="'g' + Math.min(3, imagesOf(postDetail).length)">
            <el-image
              v-for="(u, i) in imagesOf(postDetail)"
              :key="u + i"
              :src="u"
              fit="cover"
              :preview-src-list="imagesOf(postDetail)"
              :initial-index="i"
              :preview-teleported="true"
              class="dg-item"
            />
          </div>

          <div v-if="postDetail.work" class="dd-work">
            <img :src="postDetail.work.image_url" alt="复原作品" />
            <span class="confidence">复原作品 · 置信度 {{ postDetail.work.confidence }}</span>
          </div>

          <div v-if="linkedCostumes.length" class="dd-linked">
            <span class="dl-label">关联档案</span>
            <span v-for="c in linkedCostumes" :key="c.id" class="dl-chip">{{ c.name }}</span>
          </div>

          <div class="dd-actions">
            <button class="act" :class="{ on: liked }" :disabled="busy.like" @click="doLike">
              <b>{{ postDetail.like_count }}</b><span>点赞</span>
            </button>
            <button class="act" :class="{ on: collected }" :disabled="busy.collect" @click="doCollect">
              <b>{{ postDetail.collect_count }}</b><span>收藏</span>
            </button>
            <button class="act" :disabled="busy.repost" @click="openRepost(postDetail)">
              <b>{{ postDetail.repost_count }}</b><span>转发</span>
            </button>
            <span class="act-static"><b>{{ postDetail.reply_count }}</b><span>评论</span></span>
          </div>

          <div class="dd-comments">
            <h4>评论 {{ postDetail.replies?.length || 0 }}</h4>
            <div class="reply-box">
              <div v-if="replyTo" class="reply-to">
                <span>回复 @{{ replyTo.username }}</span>
                <a @click="replyTo = null">取消</a>
              </div>
              <el-input v-model="replyText" type="textarea" :rows="2"
                        :placeholder="replyTo ? `回复 @${replyTo.username}…` : '基于史料说话，写下你的看法…'" />
              <div class="rb-foot">
                <el-button size="small" type="primary" :loading="busy.reply" @click="doReply">
                  {{ replyTo ? "回复 TA" : "发表评论" }}
                </el-button>
              </div>
            </div>

            <div v-for="r in postDetail.replies" :key="r.id" class="cmt" :class="{ nested: !!r.parent_reply_id }">
              <span class="cmt-avt">{{ initial(r.username) }}</span>
              <div class="cmt-main">
                <div class="cmt-head">
                  <b>{{ r.username }}</b>
                  <span v-if="r.parent_reply_id" class="cmt-at">回复 @{{ parentName(r) }}</span>
                  <span class="cmt-time">{{ r.create_time?.slice(0, 10) }}</span>
                </div>
                <p class="cmt-content">{{ r.content }}</p>
                <span class="cmt-act" @click="setReplyTo(r)">回复</span>
              </div>
            </div>
            <div v-if="!postDetail.replies?.length" class="ys-empty cmt-empty">还没有评论，来说两句</div>
          </div>
        </div>

        <aside class="dd-side">
          <div class="side-card">
            <div class="sc-author">
              <span class="dd-avt">{{ initial(postDetail.author) }}</span>
              <div>
                <b>{{ postDetail.author }}</b>
                <small>发帖于 {{ postDetail.create_time?.slice(0, 10) }}</small>
              </div>
            </div>
          </div>

          <div class="side-card">
            <h4 class="sc-title">同版块推荐</h4>
            <div v-for="r in relatedPosts" :key="r.id" class="rec" @click="openPost(r.id)">
              <div class="rec-thumb">
                <img v-if="coverOf(r)" :src="coverOf(r)" :alt="r.title" loading="lazy" />
                <span v-else>{{ boardChar(r.board_id) }}</span>
              </div>
              <div class="rec-info">
                <p>{{ r.title }}</p>
                <small>{{ r.author }} · 赞 {{ r.like_count }}</small>
              </div>
            </div>
            <div v-if="!relatedPosts.length" class="no-tags">暂无相关帖子</div>
          </div>

          <div class="side-card side-rules">
            <h4 class="sc-title">社区公约</h4>
            <p>讨论基于史料并标注出处，勘误有理有据，严禁人身攻击。</p>
          </div>
        </aside>
      </div>
    </el-dialog>

    <!-- 转发弹窗 -->
    <el-dialog v-model="repostVisible" title="站内转发" width="480px" destroy-on-close>
      <p class="repost-target">转发：《{{ repostTarget?.title }}》</p>
      <el-input v-model="repostComment" type="textarea" :rows="3" placeholder="附言（选填），将生成新帖引用原帖…" />
      <template #footer>
        <el-button size="small" @click="repostVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="busy.repost" @click="confirmRepost">转发</el-button>
      </template>
    </el-dialog>

    <!-- 悬浮发帖球 -->
    <div class="fab-post" title="发布新帖" @click="openComposer">
      <span class="fab-plus">＋</span>
      <span class="fab-text">发帖</span>
    </div>

    <!-- 发帖弹窗（投稿台） -->
    <el-dialog v-model="postVisible" width="min(840px, 95vw)" top="4vh" class="ce-dialog" destroy-on-close
               @open="onComposerOpen">
      <template #header>
        <div class="ce-head">
          <span class="ce-kicker">COMPOSE · 投稿</span>
          <h2>发布新帖</h2>
          <span class="ce-sub">投稿到「{{ boardName(newPost.board_id) || "国风文化共治社区" }}」</span>
        </div>
      </template>

      <div class="ce-body">
        <input v-model="newPost.title" class="ce-title" maxlength="60"
               placeholder="为这帖起个标题：如「马王堆曲裾的绕襟方向再考」" />
        <div class="ce-title-bar">
          <span>{{ newPost.title.length }}/60</span>
          <span>标题写清「朝代 + 对象 + 结论或疑问」，更容易被同好搜到</span>
        </div>

        <div class="ce-row">
          <label class="ce-label">所属版块</label>
          <div class="ce-chips">
            <span v-for="b in boards" :key="b.id" class="ce-chip"
                  :class="{ on: newPost.board_id === b.id }" @click="newPost.board_id = b.id">{{ b.name }}</span>
          </div>
        </div>

        <div class="ce-row">
          <label class="ce-label">起稿模板</label>
          <div class="ce-chips">
            <span v-for="t in templates" :key="t.key" class="ce-chip tmpl"
                  :class="{ on: templateKey === t.key }" @click="applyTemplate(t.key)">{{ t.label }}</span>
          </div>
        </div>

        <div class="ce-editor">
          <div class="ce-editor-head">
            <label class="ce-label">正文 <small>支持分段，图片在下面统一排布</small></label>
          </div>
          <el-input ref="contentInput" v-model="newPost.content" type="textarea" :rows="10"
                    placeholder="写下你的考证、复原过程或讨论问题…&#10;图片可以直接拖进来或 Ctrl+V 粘贴，最多 9 张"
                    @paste="onEditorPaste" />
          <div class="ce-editor-bar">
            <span>{{ newPost.content.length }} 字</span>
            <span>{{ newPost.images.length }} / {{ MAX_IMAGES }} 张图</span>
          </div>
        </div>

        <div class="ce-two">
          <div class="ce-block">
            <label class="ce-label">配图 <small>最多 {{ MAX_IMAGES }} 张，第一张作列表首图</small></label>
            <div class="ce-gallery">
              <div v-for="(u, i) in newPost.images" :key="u + i" class="ce-gitem">
                <img :src="u" :alt="`配图 ${i + 1}`" />
                <span class="ce-gitem-x" title="删除这张" @click="removeImage(i)">✕</span>
                <span v-if="i === 0" class="ce-gitem-cover">首图</span>
                <span v-else class="ce-gitem-set" title="设为首图" @click="makeCover(i)">设首图</span>
              </div>
              <div v-if="newPost.images.length < MAX_IMAGES"
                   class="ce-gitem ce-gadd" @dragover.prevent @drop.prevent="onCoverDrop"
                   @click="postImgInput?.click()">
                <span>＋</span>
                <p>{{ imgUploading ? "上传中…" : "添加图片" }}</p>
              </div>
            </div>
            <input ref="postImgInput" type="file" accept="image/*" multiple style="display: none" @change="onPostImage" />
            <span class="ce-hint">可拖入多张、可粘贴截图；单张 8MB 内</span>
          </div>

          <div class="ce-block">
            <label class="ce-label">朝代 / 主题标签 <small>最多 6 个</small></label>
            <div class="ce-chipwrap">
              <span v-for="t in tagList" :key="t" class="ce-tag on">
                {{ t }}<b @click="removeTag(t)">✕</b>
              </span>
              <input v-if="tagList.length < 6" v-model="tagInput" class="ce-tag-input" maxlength="12"
                     placeholder="输入后回车" @keyup.enter="addTag()" />
            </div>
            <div class="ce-suggest">
              <span v-for="t in suggestedTags" :key="t" class="ce-chip sm" @click="addTag(t)">＋ {{ t }}</span>
            </div>
          </div>
        </div>

        <div class="ce-row">
          <label class="ce-label">关联档案 <small>可选</small></label>
          <div class="ce-cell">
            <el-select v-model="selectedCostumeIds" multiple filterable remote reserve-keyword
                       :remote-method="searchCostumes" :loading="costumeLoading"
                       placeholder="搜索并关联服饰档案（如：曲裾、褙子），可多选" style="width: 100%" size="small">
              <el-option v-for="c in costumeOptions" :key="c.id"
                         :label="`${c.name}${c.dynasty ? ' · ' + c.dynasty : ''}`" :value="c.id" />
            </el-select>
            <span class="ce-hint">关联后帖子会挂上对应档案，读者可一键跳转原条目</span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="ce-foot">
          <span class="ce-draft">{{ draftTip }}</span>
          <div>
            <el-button size="small" @click="postVisible = false">存草稿并关闭</el-button>
            <el-button size="small" type="primary" :loading="posting" @click="doCreatePost">发布</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import MarkdownIt from "markdown-it";
import {
  fetchBoards, fetchPosts, fetchPostDetail, createPost, createReply, deletePost,
  toggleLike, toggleCollect, repost, fetchMyInteractions, uploadImage,
  onlinePost, offlinePost, pinPost, unpinPost, fetchCostumes, fetchCostumeDetail,
} from "@/api/modules";
import PageHero from "@/components/PageHero.vue";
import { useUserStore } from "@/store/user";

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });
const MAX_IMAGES = 9;

/** 帖子配图统一解析：新帖存 JSON 数组，老帖存单条 URL，都兼容 */
function imagesOf(p: any): string[] {
  const raw = (p?.image_url || "").toString().trim();
  if (!raw) return [];
  if (raw.startsWith("[")) {
    try {
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr.filter((u) => typeof u === "string" && u) : [];
    } catch {
      return [];
    }
  }
  return raw
    .split(/[,;，；\s]+/)
    .map((s) => s.trim())
    .filter((s) => s.startsWith("http") || s.startsWith("/"));
}
const coverOf = (p: any) => imagesOf(p)[0] || "";
const moreCount = (p: any) => Math.max(0, imagesOf(p).length - 1);

/* 无配图帖：卡片封面区改为「引文卡」；正文与标题重合时改印题签，避免标题显示两次 */
const quoteOf = (p: any) => {
  let s = String(p.content || "")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/[#>*`~\-|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  s = s
    .replace(/^【[^】]{0,24}】\s*/, "")
    .replace(/^(问题|原帖|标题|内容)[:：]\s*/, "");
  /* AI 溯源回答帖的开头套话，只留问题本身 */
  s = s.split(/AI\s*溯源回答[:：]?/)[0].replace(/^[，。、；：\s]+/, "").trim();
  if (s.length < 8) s = String(p.summary || "").replace(/\s+/g, " ").trim();
  const bare = (x: string) => String(x || "").replace(/^转发[:：]\s*/, "").replace(/[\s？?！!。，,、：:；;「」“”"'’《》]/g, "");
  const a = bare(s), b = bare(p.title);
  if (!a || !b) return s.length > 62 ? s.slice(0, 62) + "…" : s;
  if (a === b || a.indexOf(b) === 0 || b.indexOf(a) === 0) return "";
  return s.length > 62 ? s.slice(0, 62) + "…" : s;
};
const postChars = (p: any) => String(p.content || "").replace(/\s+/g, "").length;

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const boards = ref<any[]>([]);
const boardId = ref<number | null>(null);
const posts = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const keyword = ref("");
const offlineOnly = ref(false);  // 管理员看已下架/待审帖子
const pendingCount = ref(0);
/** 只有真正带着 token 的管理员才显示管理员入口，避免未登录时用错接口口径 */
const isAdmin = computed(() => !!userStore.token && (userStore.role === "admin" || userStore.role === "superadmin"));

/* ---- 信息流：排序 + 标签筛选 ---- */
const sortMode = ref<"new" | "hot">("new");
const tagFilter = ref("");

const newPost = ref({ board_id: 0, title: "", content: "", dynasty_tags: "", image_url: "", costume_ids: "", images: [] as string[] });
const postVisible = ref(false);
const postImgInput = ref<HTMLInputElement | null>(null);
const imgUploading = ref(false);
const posting = ref(false);
const contentInput = ref<any>(null);
const detailVisible = ref(false);
const postDetail = ref<any>(null);
const replyText = ref("");
const replyTo = ref<any>(null);
const liked = ref(false);
const collected = ref(false);
const repostVisible = ref(false);
const repostTarget = ref<any>(null);
const repostComment = ref("");
const busy = ref({ like: false, collect: false, repost: false, reply: false });
const myInter = ref<{ liked_posts: number[]; collected: number[] }>({ liked_posts: [], collected: [] });

/* ---- 投稿台：模板 / 标签 / 封面 / 关联档案 / 草稿 ---- */
const templateKey = ref("");
const tagInput = ref("");
const selectedCostumeIds = ref<number[]>([]);
const costumeOptions = ref<any[]>([]);
const costumeLoading = ref(false);
const draftTip = ref("草稿会自动存在本机，关掉弹窗也不会丢");
const DRAFT_KEY = "community:draft:v2";

const templates = [
  {
    key: "kaoju",
    label: "形制考据",
    body: `【考证对象】\n\n【史料依据】\n> 出处：《》卷·页\n\n【实物 / 图像证据】\n\n【结论】\n\n【存疑】\n`,
  },
  {
    key: "fuyuan",
    label: "复原作品",
    body: `【复原对象】\n\n【形制结构】\n- 领型：\n- 袖型：\n- 裙/裤：\n\n【面料与色彩】\n\n【参考来源】\n> \n\n【制作心得】\n`,
  },
  {
    key: "qiujian",
    label: "求鉴定",
    body: `【对象描述】\n\n【图片 / 细节】\n\n【我的判断】\n\n【想请教的问题】\n1. \n2. \n`,
  },
  {
    key: "ziliao",
    label: "资料整理",
    body: `【主题】\n\n【时间线 / 文献脉络】\n\n【要点】\n- \n- \n\n【延伸阅读】\n> \n`,
  },
];

const suggestedTags = ["先秦", "秦汉", "魏晋", "隋唐", "两宋", "明代", "清代", "马王堆", "缂丝", "云锦", "纹样", "复原"];

const tagList = computed(() =>
  (newPost.value.dynasty_tags || "").split(",").map((s) => s.trim()).filter(Boolean),
);

/* ---- 展示用派生数据 ---- */
const displayPosts = computed(() => {
  let arr = posts.value.slice();
  if (tagFilter.value) {
    arr = arr.filter((p) => tagsOf(p).includes(tagFilter.value));
  }
  const hotScore = (p: any) => (p.like_count || 0) * 2 + (p.collect_count || 0) * 3
    + (p.reply_count || 0) * 2 + (p.repost_count || 0);
  if (sortMode.value === "hot") {
    arr.sort((a, b) => Number(!!b.is_pinned) - Number(!!a.is_pinned) || hotScore(b) - hotScore(a));
  } else {
    arr.sort((a, b) => Number(!!b.is_pinned) - Number(!!a.is_pinned)
      || String(b.create_time || "").localeCompare(String(a.create_time || "")));
  }
  return arr;
});

const relatedPosts = computed(() => {
  if (!postDetail.value) return [];
  return posts.value
    .filter((p) => p.id !== postDetail.value.id && boardName(p.board_id) === postDetail.value.board_name)
    .slice(0, 4);
});

const linkedCostumes = computed(() => detailCostumes.value);
const detailCostumes = ref<any[]>([]);

const hotTags = computed(() => {
  const map = new Map<string, number>();
  for (const p of posts.value) {
    for (const t of tagsOf(p)) map.set(t, (map.get(t) || 0) + 1);
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t]) => t);
});

/* ---- 小工具 ---- */
function boardName(id: number) {
  return boards.value.find((b) => b.id === id)?.name || "";
}
function boardChar(id: number) {
  return (boardName(id) || "社").slice(0, 1);
}
function initial(name?: string) {
  return (name || "客").trim().slice(0, 1).toUpperCase();
}
function tagsOf(p: any) {
  return String(p?.dynasty_tags || "").split(",").map((s) => s.trim()).filter(Boolean);
}
/** 相对时间：刚 / N 分钟前 / N 小时前 / N 天前 / 日期 */
function relTime(iso?: string) {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso.slice(0, 10);
  const diff = Date.now() - t;
  const min = Math.floor(diff / 60000);
  if (min < 1) return "刚刚";
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  return iso.slice(0, 10);
}

function toggleTag(t: string) {
  tagFilter.value = tagFilter.value === t ? "" : t;
}
function resetFilter() {
  tagFilter.value = "";
  keyword.value = "";
  loadPosts();
}

/* ---- 发帖配图：图文帖为主，最多 9 张，第一张作列表首图 ---- */
function syncImageUrl() {
  newPost.value.image_url = newPost.value.images.length
    ? JSON.stringify(newPost.value.images)
    : "";
}

async function uploadImages(files: File[]) {
  const imgs = files.filter((f) => f.type.startsWith("image/"));
  const room = MAX_IMAGES - newPost.value.images.length;
  if (!imgs.length) {
    ElMessage.warning("请选择图片文件");
    return;
  }
  if (room <= 0) {
    ElMessage.warning(`最多 ${MAX_IMAGES} 张图片`);
    return;
  }
  const pick = imgs.slice(0, room);
  if (imgs.length > room) ElMessage.warning(`最多 ${MAX_IMAGES} 张，多出的已忽略`);
  imgUploading.value = true;
  try {
    for (const f of pick) {
      if (f.size > 8 * 1024 * 1024) {
        ElMessage.warning(`${f.name} 超过 8MB，已跳过`);
        continue;
      }
      const dataUrl = await compressImage(f, 1400, 0.86);
      const url = await uploadImage(dataUrlToFile(dataUrl, "post.jpg"));
      newPost.value.images.push(url);
    }
    syncImageUrl();
    ElMessage.success(pick.length > 1 ? `已添加 ${pick.length} 张图片` : "图片已添加");
  } catch {
    ElMessage.error("图片上传失败");
  } finally {
    imgUploading.value = false;
  }
}

function removeImage(i: number) {
  newPost.value.images.splice(i, 1);
  syncImageUrl();
}

function makeCover(i: number) {
  if (i === 0) return;
  const arr = newPost.value.images;
  const [pick] = arr.splice(i, 1);
  arr.unshift(pick);
  syncImageUrl();
}

async function onPostImage(e: Event) {
  const input = e.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  input.value = "";
  if (files.length) await uploadImages(files);
}

async function onCoverDrop(e: DragEvent) {
  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length) await uploadImages(files);
}

/** dataURL → File（用于 FormData 上传） */
function dataUrlToFile(dataUrl: string, name: string): File {
  const [head, body] = dataUrl.split(",");
  const mime = head.match(/data:(.*?);/)?.[1] || "image/jpeg";
  const bin = atob(body);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new File([arr], name, { type: mime });
}

function compressImage(file: File, maxSize: number, quality: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        let { width, height } = img;
        const scale = Math.min(1, maxSize / Math.max(width, height));
        width = Math.max(1, Math.round(width * scale));
        height = Math.max(1, Math.round(height * scale));
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        if (!ctx) { reject(new Error("canvas 不可用")); return; }
        ctx.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL("image/jpeg", quality));
      };
      img.onerror = () => reject(new Error("图片解析失败"));
      img.src = reader.result as string;
    };
    reader.onerror = () => reject(new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

function fromQa(p: any) {
  return !!p?.content && p.content.includes("【本讨论源自溯源问答】");
}

function isMyPost(p: any) {
  return !!userStore.token && !!p && p.author === userStore.username;
}

async function confirmDelete(p: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  try {
    await ElMessageBox.confirm(`确定删除帖子《${p.title || "未命名"}》吗？删除后不可恢复。`, "删除帖子", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch {
    return;
  }
  try {
    await deletePost(p.id);
    ElMessage.success("帖子已删除");
    if (postDetail.value && postDetail.value.id === p.id) {
      detailVisible.value = false;
      postDetail.value = null;
    }
    loadBoards();
    loadPosts();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败，请稍后再试");
  }
}

function renderMarkdown(text: string) {
  return md.render(text || "");
}

function parentName(r: any) {
  const pid = r.parent_reply_id;
  const parent = postDetail.value?.replies?.find((x: any) => x.id === pid);
  return parent ? parent.username : `#${pid}`;
}

async function loadMyInter() {
  if (!userStore.token) return;
  try { myInter.value = (await fetchMyInteractions()) as any; } catch { /* 未登录忽略 */ }
}

function applyInter() {
  const lk = new Set(myInter.value.liked_posts || []);
  const cl = new Set(myInter.value.collected || []);
  posts.value.forEach((p) => {
    p.liked = lk.has(p.id);
    p.collected = cl.has(p.id);
  });
}

async function loadBoards() {
  const data: any = await fetchBoards();
  boards.value = data.items;
  if (boards.value.length && !newPost.value.board_id) {
    newPost.value.board_id = boards.value[0].id;
  }
  await loadPendingCount();
}

async function loadPendingCount() {
  if (!isAdmin.value) { pendingCount.value = 0; return; }
  try {
    const data: any = await fetchPosts({ status: "pending", page: 1, page_size: 1 });
    pendingCount.value = data.total || 0;
  } catch { /* 忽略 */ }
}

async function loadPosts() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      board_id: boardId.value, page: 1, page_size: 50, keyword: keyword.value || undefined,
    };
    if (isAdmin.value && offlineOnly.value) params.status = "pending";
    const data: any = await fetchPosts(params);
    posts.value = data.items;
    total.value = data.total || 0;
    applyInter();
  } finally { loading.value = false; }
}

function switchBoard(id: number) {
  boardId.value = id;
  offlineOnly.value = false;
  keyword.value = "";
  tagFilter.value = "";
  loadPosts();
}
function togglePending() {
  offlineOnly.value = !offlineOnly.value;
  boardId.value = null;
  keyword.value = "";
  tagFilter.value = "";
  loadPosts();
}

/* ---- Markdown 快捷（旧帖渲染仍在用，编辑器已改为图文直写） ---- */
function mdWrap(before: string, after: string) {
  const el = contentInput.value?.textarea || contentInput.value?.$el?.querySelector("textarea");
  if (!el) { newPost.value.content += before + after; return; }
  const s = el.selectionStart, e = el.selectionEnd;
  const sel = newPost.value.content.slice(s, e) || "文字";
  newPost.value.content = newPost.value.content.slice(0, s) + before + sel + after + newPost.value.content.slice(e);
  nextTick(() => { el.focus(); el.selectionStart = s + before.length; el.selectionEnd = s + before.length + sel.length; });
}
function mdLine(prefix: string) {
  const el = contentInput.value?.textarea || contentInput.value?.$el?.querySelector("textarea");
  if (!el) { newPost.value.content += "\n" + prefix; return; }
  const s = el.selectionStart;
  const lineStart = newPost.value.content.lastIndexOf("\n", s - 1) + 1;
  newPost.value.content = newPost.value.content.slice(0, lineStart) + prefix + newPost.value.content.slice(lineStart);
  nextTick(() => { el.focus(); el.selectionStart = el.selectionEnd = s + prefix.length; });
}
function mdInsert(text: string) {
  newPost.value.content += text;
}

async function onEditorPaste(e: ClipboardEvent) {
  const imgs = [...(e.clipboardData?.items || [])]
    .filter((it) => it.type.startsWith("image/"))
    .map((it) => it.getAsFile())
    .filter((f): f is File => !!f);
  if (!imgs.length) return;
  e.preventDefault();
  await uploadImages(imgs);
}

/* ---- 模板 / 标签 / 档案关联 ---- */
function applyTemplate(key: string) {
  const t = templates.find((x) => x.key === key);
  if (!t) return;
  templateKey.value = templateKey.value === key ? "" : key;
  if (!newPost.value.content.trim()) {
    newPost.value.content = t.body;
    ElMessage.success(`已套用「${t.label}」骨架`);
  } else {
    ElMessageBox.confirm("当前正文已有内容，套用模板会追加骨架，继续吗？", "套用模板", {
      confirmButtonText: "追加", cancelButtonText: "取消",
    }).then(() => { newPost.value.content += "\n\n" + t.body; }).catch(() => {});
  }
}

function addTag(t?: string) {
  const val = (t ?? tagInput.value).trim().replace(/,/g, "");
  tagInput.value = "";
  if (!val) return;
  if (tagList.value.includes(val)) return;
  if (tagList.value.length >= 6) return ElMessage.warning("标签最多 6 个");
  newPost.value.dynasty_tags = [...tagList.value, val].join(",");
}
function removeTag(t: string) {
  newPost.value.dynasty_tags = tagList.value.filter((x) => x !== t).join(",");
}

async function searchCostumes(kw: string) {
  costumeLoading.value = true;
  try {
    const data: any = await fetchCostumes({ keyword: kw || undefined, page_size: 20 });
    const incoming = (data.items || []).map((c: any) => ({ id: c.id, name: c.name, dynasty: c.dynasty }));
    // 合并已有选项，避免已选项在远程搜索后丢失名称
    const seen = new Set(costumeOptions.value.map((o) => o.id));
    costumeOptions.value = [...costumeOptions.value, ...incoming.filter((c: any) => !seen.has(c.id))];
  } catch { /* 忽略 */ } finally { costumeLoading.value = false; }
}

/* ---- 详情里展示关联档案（按 id 反查） ---- */
async function resolveCostumeNames(ids: number[]) {
  const out: any[] = [];
  for (const id of ids.slice(0, 6)) {
    try {
      const c: any = await fetchCostumeDetail(id);
      if (c && (c.name || c.id)) out.push({ id: c.id ?? id, name: c.name || `条目 #${id}` });
    } catch { /* 单条失败忽略 */ }
  }
  detailCostumes.value = out;
}

/* ---- 草稿 ---- */
function saveDraftNow() {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({
      ...newPost.value, tagInput: "", ids: selectedCostumeIds.value,
    }));
    draftTip.value = "草稿已保存";
  } catch { /* 忽略 */ }
}

function restoreDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return;
    const d = JSON.parse(raw);
    if (!d || !(d.title || d.content)) return;
    newPost.value = {
      board_id: d.board_id || (boards.value[0]?.id ?? 0),
      title: d.title || "",
      content: d.content || "",
      dynasty_tags: d.dynasty_tags || "",
      image_url: d.image_url || "",
      costume_ids: d.costume_ids || "",
      images: Array.isArray(d.images) ? d.images.filter(Boolean) : imagesOf(d),
    };
    selectedCostumeIds.value = (d.ids || []).map(Number).filter(Boolean);
    draftTip.value = "已恢复上次未发布的草稿";
  } catch { /* 忽略 */ }
}

function openComposer() {
  postVisible.value = true;
}

function onComposerOpen() {
  restoreDraft();
}

watch(() => [newPost.value.title, newPost.value.content, newPost.value.dynasty_tags, newPost.value.image_url],
  () => {
    if (!postVisible.value) return;
    draftTip.value = "正在保存…";
    saveDraftNow();
  });

async function doCreatePost() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (!newPost.value.title.trim()) return ElMessage.warning("请输入标题");
  if (newPost.value.content.trim().length < 10) return ElMessage.warning("正文至少写 10 个字");
  posting.value = true;
  try {
    syncImageUrl();
    const payload = { ...newPost.value, costume_ids: selectedCostumeIds.value.join(",") };
    await createPost(payload);
    ElMessage.success("发布成功");
    localStorage.removeItem(DRAFT_KEY);
    newPost.value = { board_id: boards.value[0]?.id ?? 0, title: "", content: "", dynasty_tags: "", image_url: "", costume_ids: "", images: [] };
    selectedCostumeIds.value = [];
    templateKey.value = "";
    postVisible.value = false;
    loadBoards();
    loadPosts();
  } finally { posting.value = false; }
}

/* ---- 管理员下架/恢复 ---- */
async function onOnline(id: number) {
  await onlinePost(id);
  ElMessage.success("已上架");
  loadPendingCount();
  loadPosts();
}
async function onOffline(id: number) {
  await offlinePost(id);
  ElMessage.success("已下架");
  loadPendingCount();
  loadPosts();
}
async function onPin(id: number) {
  await pinPost(id);
  ElMessage.success("已置顶");
  loadPosts();
}
async function onUnpin(id: number) {
  await unpinPost(id);
  ElMessage.success("已取消置顶");
  loadPosts();
}
async function onReject(id: number) {
  await offlinePost(id);
  ElMessage.success("已拒绝申请");
  loadPendingCount();
  loadPosts();
}

async function openPost(id: number) {
  postDetail.value = await fetchPostDetail(id) as any;
  const lk = new Set(myInter.value.liked_posts || []);
  const cl = new Set(myInter.value.collected || []);
  liked.value = lk.has(id);
  collected.value = cl.has(id);
  detailCostumes.value = [];
  detailVisible.value = true;
  replyText.value = "";
  replyTo.value = null;
  const ids = String(postDetail.value?.costume_ids || "").split(",").filter(Boolean).map(Number);
  if (ids.length) void resolveCostumeNames(ids);
}

function setReplyTo(r: any) {
  replyTo.value = r;
  replyText.value = "";
}

async function quickLike(p: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (p._busy) return;
  p._busy = true;
  try {
    const res: any = await toggleLike(p.id);
    p.like_count = res.like_count;
    p.liked = res.liked;
  } finally { p._busy = false; }
}

async function quickCollect(p: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (p._busy) return;
  p._busy = true;
  try {
    const res: any = await toggleCollect(p.id);
    p.collect_count = res.collect_count;
    p.collected = res.collected;
    ElMessage.success(res.collected ? "已收藏" : "已取消收藏");
  } finally { p._busy = false; }
}

function openRepost(p: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  repostTarget.value = p;
  repostComment.value = "";
  repostVisible.value = true;
}

async function confirmRepost() {
  if (!repostTarget.value) return;
  busy.value.repost = true;
  try {
    const res: any = await repost(repostTarget.value.id, repostComment.value);
    repostVisible.value = false;
    ElMessage.success(`已站内转发，生成新帖 #${res.new_post_id}`);
    if (postDetail.value && postDetail.value.id === repostTarget.value.id) {
      postDetail.value.repost_count = res.repost_count;
    }
    syncPostCount(repostTarget.value.id, "repost_count", res.repost_count);
    loadBoards();
    loadPosts();
  } finally { busy.value.repost = false; }
}

function syncPostCount(id: number, field: string, val: number) {
  const p = posts.value.find((x) => x.id === id);
  if (p) (p as any)[field] = val;
}

async function doReply() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (!replyText.value.trim()) return ElMessage.warning("请输入回复内容");
  busy.value.reply = true;
  try {
    await createReply(postDetail.value.id, replyText.value, replyTo.value?.id);
    ElMessage.success(replyTo.value ? "已回复该条评论" : "评论成功");
    replyText.value = "";
    replyTo.value = null;
    postDetail.value = await fetchPostDetail(postDetail.value.id) as any;
    syncPostCount(postDetail.value.id, "reply_count", postDetail.value.reply_count);
    loadPosts();
  } finally { busy.value.reply = false; }
}

async function doLike() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (busy.value.like) return;
  busy.value.like = true;
  try {
    const res: any = await toggleLike(postDetail.value.id);
    postDetail.value.like_count = res.like_count;
    liked.value = res.liked;
    syncPostCount(postDetail.value.id, "like_count", res.like_count);
    syncPostCount(postDetail.value.id, "liked", res.liked);
  } finally { busy.value.like = false; }
}

async function doCollect() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (busy.value.collect) return;
  busy.value.collect = true;
  try {
    const res: any = await toggleCollect(postDetail.value.id);
    postDetail.value.collect_count = res.collect_count;
    collected.value = res.collected;
    syncPostCount(postDetail.value.id, "collect_count", res.collect_count);
    syncPostCount(postDetail.value.id, "collected", res.collected);
    ElMessage.success(res.collected ? "已收藏" : "已取消收藏");
  } finally { busy.value.collect = false; }
}

onMounted(async () => {
  await loadBoards();
  await loadMyInter();
  await loadPosts();
  const qp = Number(route.query.post);
  if (qp > 0) {
    await openPost(qp);
    routerReplace(qp);
  }
});

function routerReplace(id: number) {
  history.replaceState(null, "", "/community");
  void id;
}
</script>

<style scoped>
/* ==================== 信息流工具条 ==================== */
.board-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.board-tab { padding: 6px 14px; border: 1px solid var(--ys-line); border-radius: 20px; cursor: pointer; background: #fffdf8; font-size: 14px; transition: all .2s; }
.board-tab:hover { border-color: var(--ys-red); color: var(--ys-red-deep); }
.board-tab.active { background: var(--ys-red); color: #fff; border-color: var(--ys-red); }
.board-tab i { font-style: normal; font-size: 11px; margin-left: 5px; opacity: .85; }
.board-tab.admin-tab i { background: #c0392b; color: #fff; padding: 0 5px; border-radius: 8px; }

.feed-bar { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }

.feed-search {
  flex: 1 1 340px; max-width: 580px; min-width: 240px;
  display: flex; align-items: center; gap: 10px;
  background: #fffdf8; border: 1.5px solid var(--ys-line);
  border-radius: 999px; padding: 5px 5px 5px 16px;
  transition: border-color .2s, box-shadow .2s;
}
.feed-search:focus-within { border-color: var(--ys-gold); box-shadow: 0 2px 14px rgba(201, 162, 39, .18); }
.fs-ico { font-size: 16px; color: var(--ys-ink-3); line-height: 1; }
.feed-search input {
  flex: 1; min-width: 0; border: none; outline: none; background: transparent;
  font-size: 14px; color: var(--ys-ink); font-family: inherit;
}
.feed-search input::-webkit-search-cancel-button { -webkit-appearance: none; }
.fs-go {
  flex: none; border: none; cursor: pointer; font-family: inherit;
  padding: 8px 20px; border-radius: 999px; font-size: 13.5px; letter-spacing: .08em;
  color: #fff; background: linear-gradient(135deg, #a8322c, #c2543f);
  transition: filter .2s, transform .2s;
}
.fs-go:hover { filter: brightness(1.08); transform: translateY(-1px); }

.sort-tabs { display: flex; gap: 2px; background: #fffdf8; border: 1px solid var(--ys-line); border-radius: 999px; padding: 3px; }
.sort-tab { padding: 5px 14px; border-radius: 999px; font-size: 13px; color: var(--ys-ink-2); cursor: pointer; transition: all .18s; }
.sort-tab:hover { color: var(--ys-red-deep); }
.sort-tab.active { background: var(--ys-gold); color: #4a3115; font-weight: 600; }
.feed-count { font-size: 12px; color: var(--ys-ink-3); }
.feed-reset { font-size: 12px; color: var(--ys-red-deep); cursor: pointer; }
.feed-reset:hover { text-decoration: underline; }

/* ==================== 布局 ==================== */
.community-layout { display: grid; grid-template-columns: 1fr 280px; gap: 20px; align-items: start; }
.post-stream { min-width: 0; }

/* ==================== B 站式卡片网格 ==================== */
.feed-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px 18px; }
.feed-empty { grid-column: 1 / -1; }
.vcard {
  display: flex; flex-direction: column; min-width: 0;
  border: 1px solid var(--ys-line); border-radius: 12px; overflow: hidden;
  background: #fffdf8; transition: transform .22s ease, box-shadow .22s ease;
}
.vcard:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(122, 58, 32, .16); }

.vthumb { position: relative; aspect-ratio: 16 / 9; cursor: pointer; overflow: hidden; background: #7a221c; }
.vthumb img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .45s ease; }
.vcard:hover .vthumb img { transform: scale(1.045); }
.vthumb-fallback {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: flex-start; justify-content: flex-start;
  padding: 24px 26px 18px;
  background:
    radial-gradient(circle at 82% 8%, rgba(232, 199, 126, .22), transparent 52%),
    repeating-linear-gradient(45deg, rgba(168, 50, 44, .05) 0 7px, transparent 7px 14px),
    linear-gradient(160deg, #fdf8ee 0%, #f4e9d6 62%, #eedec2 100%);
  overflow: hidden;
}
.vthumb-fallback::before {
  content: ""; position: absolute; inset: 13px; border: 1px solid rgba(168, 50, 44, .2); border-radius: 8px; pointer-events: none;
}
.vthumb-fallback::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 42px;
  background: linear-gradient(to top, rgba(168, 50, 44, .075), transparent);
  pointer-events: none;
}
.vfb-seal {
  position: relative; z-index: 1; width: 30px; height: 30px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-family: "STKaiti", "KaiTi", serif; font-size: 17px; color: #fffaf0;
  background: linear-gradient(150deg, #b23a30, #8d201a);
  box-shadow: 0 2px 7px rgba(122, 58, 32, .3);
}
.vfb-quote {
  position: relative; z-index: 1; margin: 10px 0 0; min-width: 0;
  font-family: "STKaiti", "KaiTi", serif; font-size: 16.5px; line-height: 1.95;
  color: #4a3220; letter-spacing: .02em; text-align: left;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.vfb-quote::before { content: "「"; color: #a8322c; }
.vfb-quote::after { content: "」"; color: #a8322c; }
.vfb-sign {
  position: relative; z-index: 1; margin: 12px 0 0; display: flex; align-items: center; gap: 14px;
}
.vfb-sign strong {
  font-family: "STKaiti", "KaiTi", serif; font-weight: 400; font-size: 52px; line-height: 1;
  color: rgba(168, 50, 44, .42); letter-spacing: .06em;
}
.vfb-sign > div { display: flex; flex-direction: column; gap: 7px; }
.vfb-tags { font-size: 12.5px; letter-spacing: .16em; color: #8a6a3c; }
.vfb-meta { font-size: 11.5px; letter-spacing: .1em; color: #a08a68; }
.vthumb-fallback em {
  position: relative; z-index: 1; margin-top: auto; padding-top: 7px;
  font-style: normal; font-size: 11px; letter-spacing: .2em; color: #8a6a3c;
  border-top: 1px solid rgba(138, 106, 60, .26);
}
.vmore {
  position: absolute; right: 8px; bottom: 8px; z-index: 2;
  padding: 1px 8px; border-radius: 999px; font-size: 11.5px; line-height: 1.7;
  color: #fff; background: rgba(40, 18, 12, .62); border: 1px solid rgba(232, 199, 126, .5);
  backdrop-filter: blur(2px);
}

.vpin {
  position: absolute; top: 8px; left: 8px; z-index: 2;
  background: var(--ys-red); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 4px;
}
.vcat {
  position: absolute; top: 8px; right: 8px; z-index: 2;
  background: rgba(46, 36, 26, .62); color: #f7e8cd; font-size: 11px; padding: 2px 8px; border-radius: 4px;
  backdrop-filter: blur(4px);
}
.vcmt {
  position: absolute; right: 8px; bottom: 8px; z-index: 2;
  background: rgba(20, 14, 10, .55); color: #fff; font-size: 11px; padding: 2px 7px; border-radius: 4px;
}

.vbody { padding: 11px 12px 10px; display: flex; flex-direction: column; gap: 7px; flex: 1; }
.vtitle {
  margin: 0; font-size: 14.5px; line-height: 1.5; font-weight: 600; cursor: pointer;
  color: var(--ys-ink); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; transition: color .18s;
}
.vtitle:hover { color: var(--ys-red-deep); }
.vsum {
  margin: 0; font-size: 12px; line-height: 1.65; color: var(--ys-ink-3);
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.vfoot { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ys-ink-3); margin-top: auto; }
.vavt {
  width: 20px; height: 20px; border-radius: 50%; flex: none;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #c9a227, #a8322c); color: #fff; font-size: 10px;
}
.vau { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 88px; }
.vtime { margin-left: auto; flex: none; }

.vrow {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  border-top: 1px dashed var(--ys-line); padding-top: 7px; font-size: 12px; color: var(--ys-ink-3);
}
.vstat { display: flex; gap: 12px; }
.vstat b { font-weight: 400; cursor: pointer; user-select: none; transition: color .15s; }
.vstat b:hover { color: var(--ys-red-deep); }
.vstat b.on { color: var(--ys-red-deep); font-weight: 600; }
.vadmin { display: flex; gap: 10px; margin-left: auto; }
.vadmin b { font-weight: 400; cursor: pointer; color: var(--ys-gold); }
.vadmin b.danger { color: #c0392b; }
.vadmin b:hover { text-decoration: underline; }
.vdel { color: var(--ys-red-deep); cursor: pointer; }
.vdel:hover { text-decoration: underline; }

/* ==================== 侧栏 ==================== */
.community-side { display: flex; flex-direction: column; gap: 14px; position: sticky; top: 84px; }
.rules { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ys-ink-2); line-height: 2; }
.side-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.side-tags .ys-tag.hot { cursor: pointer; transition: all .18s; }
.side-tags .ys-tag.hot:hover { background: #f3e6c8; border-color: var(--ys-gold); }
.side-tags .ys-tag.hot.on { background: var(--ys-red); color: #fff; border-color: var(--ys-red); }
.no-tags { font-size: 12px; color: var(--ys-ink-3); }

/* ==================== 详情（双栏） ==================== */
.dd-topbar { display: flex; align-items: center; gap: 10px; }
.dd-crumb { font-size: 12px; letter-spacing: .12em; color: var(--ys-ink-3); }
.qa-source-badge { font-size: 11px; color: #fff; background: var(--ys-red); border-radius: 4px; padding: 1px 8px; }

.dd-grid { display: grid; grid-template-columns: minmax(0, 1fr) 288px; gap: 30px; align-items: start; }
.dd-main { min-width: 0; }
.dd-title { margin: 2px 0 14px; font-size: 24px; line-height: 1.45; font-weight: 700; color: var(--ys-ink); letter-spacing: .01em; }

.dd-authorbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding-bottom: 14px; border-bottom: 1px solid var(--ys-line); }
.dd-avt {
  width: 34px; height: 34px; border-radius: 50%; flex: none;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #c9a227, #a8322c); color: #fff; font-size: 14px;
}
.dd-auinfo { display: flex; flex-direction: column; line-height: 1.35; }
.dd-auinfo b { font-size: 13.5px; color: var(--ys-ink); }
.dd-auinfo small { font-size: 11.5px; color: var(--ys-ink-3); }
.dd-tags { display: flex; gap: 5px; flex-wrap: wrap; margin-left: 6px; }
.dd-tag { font-size: 11.5px; color: #7a221c; background: #f7ecd8; border: 1px solid #e6d3ae; border-radius: 10px; padding: 1px 8px; }
.dd-authorbar .vdel { margin-left: auto; font-size: 12px; }

.dd-body { margin: 18px 0 4px; line-height: 1.95; font-size: 15px; color: var(--ys-ink); word-break: break-word; }
.markdown-body :deep(p) { margin: 9px 0; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin: 16px 0 8px; font-size: 1.12em; color: var(--ys-red-deep); }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 22px; margin: 8px 0; }
.markdown-body :deep(li) { margin: 4px 0; }
.markdown-body :deep(code) { background: #f4ecdf; padding: 1px 5px; border-radius: 4px; font-size: 12.5px; }
.markdown-body :deep(blockquote) { border-left: 3px solid var(--ys-gold); margin: 10px 0; padding: 6px 14px; color: var(--ys-ink-2); background: #f8f1e4; border-radius: 0 6px 6px 0; }
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; }

.dd-image { margin: 14px 0; }
.dd-gallery { margin: 16px 0; display: grid; gap: 8px; }
.dd-gallery.g1 { grid-template-columns: 1fr; }
.dd-gallery.g2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.dd-gallery.g3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.dd-gallery .dg-item { border-radius: 10px; overflow: hidden; border: 1px solid var(--ys-line); cursor: zoom-in; width: 100%; }
.dd-gallery.g1 .dg-item { max-height: 560px; }
.dd-gallery.g1 :deep(.el-image__inner) { max-height: 560px; object-fit: contain; background: #fffdf8; }
.dd-gallery.g2 :deep(.el-image__inner),
.dd-gallery.g3 :deep(.el-image__inner) { aspect-ratio: 1 / 1; }
.dd-image img { max-width: 100%; max-height: 520px; border-radius: 10px; border: 1px solid var(--ys-line); display: block; }
.dd-work { position: relative; display: inline-block; margin: 6px 0 12px; }
.dd-work img { max-height: 300px; border-radius: 8px; display: block; }
.confidence { position: absolute; right: 8px; bottom: 8px; background: rgba(46, 36, 26, .8); color: #fff; font-size: 12px; padding: 2px 10px; border-radius: 12px; }

.dd-linked { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 12px 0 2px; }
.dl-label { font-size: 12px; color: var(--ys-ink-3); letter-spacing: .1em; }
.dl-chip { font-size: 12px; color: #7a221c; border: 1px solid #e6d3ae; background: #fbf3e5; border-radius: 4px; padding: 2px 9px; }

.dd-actions {
  display: flex; align-items: center; gap: 8px; margin: 20px 0 6px;
  padding: 12px 0; border-top: 1px solid var(--ys-line); border-bottom: 1px solid var(--ys-line);
}
.act {
  display: inline-flex; align-items: center; gap: 6px; cursor: pointer; font-family: inherit;
  border: 1px solid var(--ys-line); background: #fffdf8; border-radius: 999px;
  padding: 6px 16px; color: var(--ys-ink-2); font-size: 13px; transition: all .18s;
}
.act b { font-weight: 600; }
.act span { font-size: 12px; }
.act:hover { border-color: var(--ys-gold); color: var(--ys-red-deep); transform: translateY(-1px); }
.act.on { background: var(--ys-red); border-color: var(--ys-red); color: #fff; }
.act-static { display: inline-flex; align-items: center; gap: 6px; color: var(--ys-ink-3); font-size: 13px; padding: 6px 4px; }
.act-static b { font-weight: 600; }
.act-static span { font-size: 12px; }

.dd-comments { margin-top: 10px; }
.dd-comments h4 { margin: 18px 0 10px; font-size: 15px; color: var(--ys-ink); }
.reply-box { margin-bottom: 14px; }
.reply-to { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--ys-ink-3); margin: 0 0 6px; }
.reply-to a { color: var(--ys-red-deep); cursor: pointer; }
.rb-foot { display: flex; justify-content: flex-end; margin-top: 6px; }

.cmt { display: flex; gap: 10px; padding: 12px 0; border-top: 1px dashed var(--ys-line); }
.cmt.nested { margin-left: 34px; padding-left: 8px; border-left: 2px solid #f0e4cc; }
.cmt-avt {
  width: 30px; height: 30px; border-radius: 50%; flex: none;
  display: inline-flex; align-items: center; justify-content: center;
  background: #f3e6c8; color: #8a5a1f; font-size: 12px;
}
.cmt-main { flex: 1; min-width: 0; }
.cmt-head { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--ys-ink-3); flex-wrap: wrap; }
.cmt-head b { font-size: 12.5px; color: var(--ys-red-deep); font-weight: 600; }
.cmt-at { font-size: 11.5px; color: var(--ys-ink-3); }
.cmt-time { margin-left: auto; }
.cmt-content { margin: 5px 0 4px; font-size: 13.5px; line-height: 1.75; color: var(--ys-ink-2); word-break: break-word; }
.cmt-act { font-size: 11.5px; color: var(--ys-ink-3); cursor: pointer; }
.cmt-act:hover { color: var(--ys-red-deep); text-decoration: underline; }
.cmt-empty { border: none; }

.dd-side { display: flex; flex-direction: column; gap: 14px; }
.side-card { background: #fffdf8; border: 1px solid var(--ys-line); border-radius: 10px; padding: 13px 14px; }
.sc-author { display: flex; align-items: center; gap: 10px; }
.sc-author b { display: block; font-size: 13.5px; }
.sc-author small { font-size: 11.5px; color: var(--ys-ink-3); }
.sc-title { margin: 0 0 10px; font-size: 13px; color: var(--ys-red-deep); letter-spacing: .06em; }
.rec { display: flex; gap: 8px; padding: 7px 0; cursor: pointer; border-top: 1px dashed var(--ys-line); }
.rec:first-of-type { border-top: none; }
.rec-thumb {
  width: 68px; height: 42px; flex: none; border-radius: 6px; overflow: hidden;
  background: linear-gradient(135deg, #a8322c, #7a221c);
  display: flex; align-items: center; justify-content: center;
  color: #f6e2b8; font-size: 14px; font-family: "STKaiti", "KaiTi", serif;
}
.rec-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.rec-info { min-width: 0; }
.rec-info p {
  margin: 0 0 3px; font-size: 12.5px; line-height: 1.45; color: var(--ys-ink);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.rec-info small { font-size: 11px; color: var(--ys-ink-3); }
.rec:hover .rec-info p { color: var(--ys-red-deep); }
.side-rules p { margin: 0; font-size: 12.5px; line-height: 1.9; color: var(--ys-ink-2); }

/* ==================== 投稿台 ==================== */
.ce-head { display: flex; flex-direction: column; gap: 2px; }
.ce-kicker { font-size: 11px; letter-spacing: .26em; color: var(--ys-gold); }
.ce-head h2 { margin: 0; font-size: 20px; color: var(--ys-ink); }
.ce-sub { font-size: 12px; color: var(--ys-ink-3); }

.ce-body { display: flex; flex-direction: column; gap: 14px; max-height: 66vh; overflow-y: auto; padding-right: 4px; }
/* 关键：让子块保持自身高度，超高时由 .ce-body 滚动，而不是把正文框压成一条线 */
.ce-body > * { flex: 0 0 auto; }
.ce-title {
  width: 100%; border: none; border-bottom: 2px solid var(--ys-line); outline: none;
  background: transparent; font-family: inherit; font-size: 19px; font-weight: 600;
  color: var(--ys-ink); padding: 6px 2px 10px; transition: border-color .2s;
}
.ce-title:focus { border-color: var(--ys-gold); }
.ce-title::placeholder { color: #c3b49c; font-weight: 400; }
.ce-title-bar { display: flex; justify-content: space-between; gap: 10px; font-size: 11.5px; color: var(--ys-ink-3); margin-top: -6px; }

.ce-row { display: flex; gap: 12px; align-items: flex-start; }
.ce-label { flex: none; width: 84px; font-size: 12.5px; color: var(--ys-ink-2); padding-top: 6px; letter-spacing: .06em; }
.ce-label small { color: var(--ys-ink-3); font-size: 11px; }
.ce-cell { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 5px; }
.ce-hint { font-size: 11px; color: var(--ys-ink-3); }
.ce-chips { display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }
.ce-chip {
  font-size: 12.5px; padding: 4px 12px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--ys-line); background: #fffdf8; color: var(--ys-ink-2); transition: all .16s;
}
.ce-chip:hover { border-color: var(--ys-gold); color: var(--ys-red-deep); }
.ce-chip.on { background: var(--ys-red); border-color: var(--ys-red); color: #fff; }
.ce-chip.sm { font-size: 11.5px; padding: 2px 9px; color: var(--ys-ink-3); }
.ce-chip.tmpl { border-style: dashed; }

.ce-editor { border: 1px solid var(--ys-line); border-radius: 10px; background: #fffdf8; overflow: hidden; }
.md-toolbar { display: flex; align-items: center; gap: 4px; padding: 7px 9px; border-bottom: 1px solid var(--ys-line); background: #fbf6ec; }
.md-btn {
  width: 28px; height: 28px; border: 1px solid var(--ys-line); background: #fffdf8;
  border-radius: 6px; cursor: pointer; font-size: 12.5px; color: var(--ys-ink-2);
  display: flex; align-items: center; justify-content: center; transition: all .15s;
}
.md-btn:hover { background: #f3e6c8; border-color: var(--ys-gold); color: var(--ys-red-deep); }
.md-spacer { flex: 1; }
.md-tab {
  border: none; background: transparent; cursor: pointer; font-family: inherit;
  font-size: 12px; color: var(--ys-ink-3); padding: 4px 10px; border-radius: 6px;
}
.md-tab.on { background: var(--ys-gold); color: #4a3115; font-weight: 600; }
.md-tip { margin-left: auto; font-size: 11px; color: var(--ys-ink-3); }
.editor-meta { text-align: right; font-size: 11px; color: var(--ys-ink-3); margin-top: 4px; }

/* 审核/置顶操作（管理员） */
.audit-btns b { cursor: pointer; margin-right: 10px; font-size: 13px; }
.audit-btns .approve { color: #2e7d32; }
.audit-btns .approve:hover { text-decoration: underline; }
.audit-btns .reject { color: #c0392b; }
.audit-btns .reject:hover { text-decoration: underline; }
.audit-btns .pin-btn { color: #c9a227; cursor: pointer; margin-right: 8px; }
.audit-btns .pin-btn:hover { text-decoration: underline; }
.ce-preview { padding: 14px 16px; min-height: 220px; font-size: 14px; line-height: 1.85; }
.ce-editor-bar { display: flex; justify-content: space-between; padding: 6px 12px; font-size: 11px; color: var(--ys-ink-3); border-top: 1px dashed var(--ys-line); }

.ce-two { display: grid; grid-template-columns: minmax(300px, 1.15fr) minmax(0, 1fr); gap: 16px; }
.ce-block { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.ce-block .ce-label { width: auto; padding-top: 0; }

.ce-editor-head { display: flex; align-items: center; padding: 8px 12px; border-bottom: 1px solid var(--ys-line); background: #fbf6ec; }
.ce-editor-head .ce-label { width: auto; padding: 0; }

.ce-gallery { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.ce-gitem {
  position: relative; aspect-ratio: 1 / 1; border-radius: 8px; overflow: hidden;
  border: 1px solid var(--ys-line); background: #fffdf8;
}
.ce-gitem img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ce-gitem-x {
  position: absolute; top: 4px; right: 4px; z-index: 2;
  width: 20px; height: 20px; line-height: 20px; text-align: center;
  border-radius: 50%; background: rgba(20, 14, 10, .62); color: #fff;
  font-size: 11px; cursor: pointer;
}
.ce-gitem-x:hover { background: rgba(168, 50, 44, .9); }
.ce-gitem-cover {
  position: absolute; left: 4px; bottom: 4px; z-index: 2;
  padding: 0 6px; border-radius: 4px; font-size: 10.5px; line-height: 1.6;
  color: #4a3115; background: rgba(232, 199, 126, .92);
}
.ce-gitem-set {
  position: absolute; left: 4px; bottom: 4px; z-index: 2;
  padding: 0 6px; border-radius: 4px; font-size: 10.5px; line-height: 1.7;
  color: #fff; background: rgba(40, 18, 12, .6); cursor: pointer; opacity: 0; transition: opacity .18s;
}
.ce-gitem:hover .ce-gitem-set { opacity: 1; }
.ce-gadd {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
  border: 1.5px dashed #d9c7a4; cursor: pointer; color: var(--ys-ink-3); transition: border-color .2s;
}
.ce-gadd:hover { border-color: var(--ys-gold); }
.ce-gadd span { font-size: 20px; color: var(--ys-gold); line-height: 1; }
.ce-gadd p { margin: 0; font-size: 11.5px; }

.ce-chipwrap {
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  min-height: 34px; padding: 5px 8px; border: 1px solid var(--ys-line);
  border-radius: 8px; background: #fffdf8;
}
.ce-tag { font-size: 12px; background: #f7ecd8; border: 1px solid #e6d3ae; color: #7a221c; border-radius: 999px; padding: 2px 6px 2px 10px; }
.ce-tag b { margin-left: 5px; cursor: pointer; opacity: .65; font-weight: 400; }
.ce-tag b:hover { opacity: 1; }
.ce-tag-input { flex: 1; min-width: 90px; border: none; outline: none; background: transparent; font-family: inherit; font-size: 12.5px; color: var(--ys-ink); }
.ce-suggest { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }

.ce-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ce-draft { font-size: 11.5px; color: var(--ys-ink-3); }

/* ==================== 悬浮发帖球 ==================== */
.fab-post {
  position: fixed; right: 30px; bottom: 118px; z-index: 60;
  width: 64px; height: 64px; border-radius: 50%;
  background: linear-gradient(135deg, #a8322c, #c74b3f); color: #fff;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 6px 22px rgba(168, 50, 44, .38);
  transition: transform .2s ease, box-shadow .2s ease;
}
.fab-post:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 10px 26px rgba(168, 50, 44, .45); }
.fab-plus { font-size: 20px; line-height: 1; font-weight: 700; }
.fab-text { font-size: 12px; letter-spacing: 2px; margin-top: 2px; }

.repost-target { font-size: 14px; color: var(--ys-ink-2); margin-bottom: 10px; }

/* ==================== 响应式 ==================== */
@media (max-width: 1280px) {
  .feed-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dd-grid { grid-template-columns: minmax(0, 1fr) 250px; gap: 22px; }
}
@media (max-width: 980px) {
  .community-layout { grid-template-columns: 1fr; }
  .community-side { position: static; }
  .dd-grid { grid-template-columns: 1fr; }
  .dd-side { order: 2; }
  .ce-two { grid-template-columns: 1fr; }
  .ce-row { flex-direction: column; gap: 6px; }
  .ce-label { width: auto; padding-top: 0; }
  .fab-post { right: 30px; bottom: 100px; width: 56px; height: 56px; }
}
@media (max-width: 720px) {
  .feed-grid { grid-template-columns: 1fr; }
  .fab-post { right: 16px; bottom: 108px; width: 56px; height: 56px; }
  .dd-title { font-size: 20px; }
}
</style>

<style>
/* Element Plus 的弹窗会 teleport 到 body 外层，scoped 样式够不到，
   这里用弹窗自身 class 收口：详情内容超高时在弹窗内部滚动，不顶出视口 */
.bd-dialog .el-dialog__body {
  max-height: calc(100vh - 160px);
  overflow-y: auto;
  padding-top: 2px;
  overscroll-behavior: contain;
}
.bd-dialog .el-dialog__header { padding: 14px 20px 4px; }
.ce-dialog .el-dialog__header { padding: 16px 22px 6px; }
.ce-dialog .el-dialog__body { padding-top: 10px; }
</style>
