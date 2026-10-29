<template>
  <div class="community-page">
    <PageHero title="国风文化共治社区" kicker="COMMUNITY · 共治共赏" sub="形制溯源 · 复原作品 · 纹样文创 · 史料求助 · 共治勘误" seal="社" />

    <!-- 版块导航 -->
    <div class="board-tabs anim-rise" style="animation-delay: .5s">
      <span v-for="b in boards" :key="b.id" class="board-tab" :class="{ active: !pendingOnly && boardId === b.id }"
            @click="switchBoard(b.id)">
        {{ b.name }}<i>{{ b.post_count }}</i>
      </span>
      <span v-if="isAdmin" class="board-tab" :class="{ active: offlineOnly }" @click="togglePending">
        已下架<i style="background:#c0392b">藏</i>
      </span>
    </div>

    <!-- 用户作品已迁移至「档案」「面料」页 -->

    <div class="community-layout anim-stagger">
      <div class="post-stream">
        <!-- 列表工具条：搜索 -->
        <div class="list-toolbar">
          <el-input v-model="keyword" placeholder="搜索帖子标题…" clearable size="small" style="width: 260px"
                    @keyup.enter="loadPosts" @clear="loadPosts" />
          <el-button size="small" @click="loadPosts">搜索</el-button>
          <span class="post-total" v-if="total">共 {{ total }} 帖</span>
        </div>

        <!-- 帖子列表 -->
        <div v-loading="loading" class="post-list">
          <article v-for="p in posts" :key="p.id" class="post-card ys-card">
            <div class="post-main" @click="openPost(p.id)">
              <div class="post-head">
                <span v-if="p.is_pinned" class="pin">置顶</span>
                <span class="board-name">{{ boardName(p.board_id) }}</span>
                <h3>{{ p.title }}</h3>
              </div>
              <p class="post-content">{{ p.content }}</p>
              <div class="post-img" v-if="p.image_url">
                <img :src="p.image_url" :alt="p.title" loading="lazy" />
              </div>
              <div class="post-tags" v-if="p.dynasty_tags">
                <span class="ys-tag" v-for="t in p.dynasty_tags.split(',')" :key="t" v-show="t">{{ t }}</span>
              </div>
            </div>
            <div class="post-foot">
              <span class="author">{{ p.author }}</span>
              <span class="time">{{ p.create_time?.slice(0, 10) }}</span>
              <span v-if="offlineOnly && isAdmin" class="audit-btns">
                <b class="approve" @click.stop="onOnline(p.id)">✓ 恢复</b>
              </span>
              <span v-if="!offlineOnly && isAdmin && p.author_id !== userStore.userId" class="audit-btns">
                <b class="reject" @click.stop="onOffline(p.id)">↓ 下架</b>
              </span>
              <span v-if="isMyPost(p)" class="del-post" @click.stop="confirmDelete(p)">删除</span>
              <span class="interact">
                <b class="like" :class="{ liked: p.liked }" @click.stop="quickLike(p)">赞 {{ p.like_count }}</b>
                <b class="collect" :class="{ collected: p.collected }" @click.stop="quickCollect(p)">藏 {{ p.collect_count }}</b>
                <b class="repost" @click.stop="openRepost(p)">转 {{ p.repost_count }}</b>
                <b>回 {{ p.reply_count }}</b>
              </span>
            </div>
          </article>
          <div v-if="!loading && !posts.length" class="ys-empty">
            {{ keyword ? "未找到匹配的帖子" : "该版块暂无帖子，来发第一帖吧" }}
          </div>
        </div>
      </div>

      <aside class="community-side">
        <div class="ys-card">
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
            <span v-for="(t, i) in hotTags" :key="t" class="ys-tag hot" :style="{ fontSize: 12 + Math.min(6, i * 1.2) + 'px' }">{{ t }}</span>
            <span v-if="!hotTags.length" class="no-tags">暂无标签</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- 帖子详情对话框 -->
    <el-dialog v-model="detailVisible" :title="postDetail?.title" width="820px" top="4vh">
      <div v-if="postDetail">
        <div class="d-post-meta">
          <span v-if="fromQa(postDetail)" class="qa-source-badge">源自AI溯源问答</span>
          <span>作者 {{ postDetail.author }}</span>
          <span>版块 {{ postDetail.board_name }}</span>
          <span>{{ postDetail.create_time?.slice(0, 10) }}</span>
          <span v-if="postDetail.dynasty_tags" class="ys-tag" v-for="t in postDetail.dynasty_tags.split(',')" :key="t" v-show="t">{{ t }}</span>
          <span v-if="isMyPost(postDetail)" class="del-post del-in-detail" @click="confirmDelete(postDetail)">删除本帖</span>
        </div>
        <div class="d-content markdown-body" v-html="renderMarkdown(postDetail.content)"></div>
        <div v-if="postDetail.image_url" class="d-image">
          <img :src="postDetail.image_url" alt="帖子配图" />
        </div>

        <div v-if="postDetail.work" class="d-work">
          <img :src="postDetail.work.image_url" alt="复原作品" style="max-height: 260px; border-radius: 8px" />
          <span class="confidence">置信度 {{ postDetail.work.confidence }}</span>
        </div>

        <el-divider />
        <h4>回复（{{ postDetail.replies?.length || 0 }}）</h4>
        <div v-for="r in postDetail.replies" :key="r.id" class="reply-item" :class="{ nested: !!r.parent_reply_id }">
          <div class="r-head">
            <span class="r-user">{{ r.username }}</span>
            <span v-if="r.parent_reply_id" class="r-parent">回复 @{{ parentName(r) }}</span>
            <span class="r-time">{{ r.create_time?.slice(0, 10) }}</span>
            <span class="r-act" @click="setReplyTo(r)">回复</span>
          </div>
          <p class="r-content">{{ r.content }}</p>
        </div>
        <div v-if="!postDetail.replies?.length" class="ys-empty">暂无回复</div>

        <div class="reply-box">
          <div v-if="replyTo" class="reply-to">
            <span>回复 @{{ replyTo.username }} 的回复</span>
            <a @click="replyTo = null">取消</a>
          </div>
          <el-input v-model="replyText" type="textarea" :rows="2"
                    :placeholder="replyTo ? `回复 @${replyTo.username}…` : '写下你的回复…'"
                    style="margin-top: 6px" />
        </div>
        <div class="d-foot" style="display: flex; justify-content: space-between; margin-top: 10px">
          <div>
            <el-button size="small" :type="liked ? 'primary' : 'default'" :loading="busy.like" @click="doLike">赞 {{ postDetail.like_count }}</el-button>
            <el-button size="small" :type="collected ? 'primary' : 'default'" :loading="busy.collect" @click="doCollect">收藏</el-button>
            <el-button size="small" :loading="busy.repost" @click="openRepost(postDetail)">转发</el-button>
          </div>
          <el-button type="primary" :loading="busy.reply" @click="doReply">{{ replyTo ? "回复 TA" : "回复" }}</el-button>
        </div>
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

    <!-- 悬浮发帖小球 -->
    <div class="fab-post" title="发布新帖" @click="postVisible = true">
      <span class="fab-plus">＋</span>
      <span class="fab-text">发帖</span>
    </div>

    <!-- 发帖弹窗 -->
    <el-dialog v-model="postVisible" title="发布新帖" width="680px" destroy-on-close>
      <div class="editor-head" style="display: flex; gap: 10px; margin-bottom: 10px">
        <el-input v-model="newPost.title" placeholder="帖子标题（建议 10-30 字）" size="large" maxlength="60" show-word-limit style="flex: 1" />
        <el-select v-model="newPost.board_id" size="small" style="width: 170px" placeholder="选择版块" clearable>
          <el-option v-for="b in boards" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
      </div>
      <!-- Markdown 快捷工具栏 -->
      <div class="md-toolbar">
        <button type="button" class="md-btn" title="加粗" @click="mdWrap('**','**')"><b>B</b></button>
        <button type="button" class="md-btn" title="斜体" @click="mdWrap('*','*')"><i>I</i></button>
        <button type="button" class="md-btn" title="引用" @click="mdLine('> ')">❝</button>
        <button type="button" class="md-btn" title="无序列表" @click="mdLine('- ')">•</button>
        <button type="button" class="md-btn" title="有序列表" @click="mdLine('1. ')">1.</button>
        <button type="button" class="md-btn" title="分隔线" @click="mdInsert('\n---\n')">―</button>
        <span class="md-tip">支持 Markdown</span>
      </div>
      <el-input ref="contentInput" v-model="newPost.content" type="textarea" :rows="7"
                placeholder="分享你的服饰复原/考据作品，或提出讨论问题…&#10;支持 Markdown：**加粗**、`代码`、- 列表、&gt; 引用；可直接 Ctrl+V 粘贴截图"
                @paste="onEditorPaste" />
      <div class="editor-meta">
        <span class="char-count">{{ newPost.content.length }} 字</span>
      </div>
      <div class="editor-img" v-if="newPost.image_url" style="margin-top: 10px">
        <div class="img-preview">
          <img :src="newPost.image_url" alt="配图预览" />
          <span class="img-remove" @click="newPost.image_url = ''">✕ 移除</span>
        </div>
      </div>
      <div class="editor-mid" style="display: flex; gap: 10px; margin-top: 10px; align-items: center">
        <el-input v-model="newPost.dynasty_tags" placeholder="朝代/主题标签（逗号分隔，如：唐,襦裙）" size="small" style="max-width: 300px" />
        <input ref="postImgInput" type="file" accept="image/*" style="display: none" @change="onPostImage" />
        <el-button size="small" @click="postImgInput?.click()" :loading="imgUploading">📷 添加配图</el-button>
      </div>
      <template #footer>
        <span class="note" style="float: left; color: var(--ys-ink-3); font-size: 12px">分享服饰复原/考据作品 · 讨论请标注史料出处</span>
        <el-button size="small" @click="postVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="posting" @click="doCreatePost">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import MarkdownIt from "markdown-it";
import { fetchBoards, fetchPosts, fetchPostDetail, createPost, createReply, deletePost, toggleLike, toggleCollect, repost, fetchMyInteractions, uploadImage, onlinePost, offlinePost } from "@/api/modules";
import PageHero from "@/components/PageHero.vue";
import { useUserStore } from "@/store/user";

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const boards = ref<any[]>([]);
const boardId = ref<number | null>(null);
const posts = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const keyword = ref("");
const offlineOnly = ref(false);  // 管理员看已下架帖子
const isAdmin = computed(() => userStore.role === "admin" || userStore.role === "superadmin");
const newPost = ref({ board_id: 0, title: "", content: "", dynasty_tags: "", image_url: "" });
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

/* ---- 用户作品已迁移至「档案」「面料」页 ---- */

const hotTags = computed(() => {
  const map = new Map<string, number>();
  for (const p of posts.value) {
    for (const t of (p.dynasty_tags || "").split(",")) {
      const tag = t.trim();
      if (tag) map.set(tag, (map.get(tag) || 0) + 1);
    }
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t]) => t);
});

function boardName(id: number) {
  return boards.value.find((b) => b.id === id)?.name || "";
}

/* ---- 发帖配图 ---- */
async function onPostImage(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (!file.type.startsWith("image/")) { ElMessage.warning("请选择图片文件"); return; }
  if (file.size > 8 * 1024 * 1024) { ElMessage.warning("图片过大，请选择 8MB 以内"); return; }
  imgUploading.value = true;
  try {
    const dataUrl = await compressImage(file, 900, 0.82);
    const url = await uploadImage(dataUrlToFile(dataUrl, "post.jpg"));
    newPost.value.image_url = url;
    ElMessage.success("配图已上传");
  } catch {
    ElMessage.error("图片上传失败");
  } finally { imgUploading.value = false; }
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
  return !!p.content && p.content.includes("【本讨论源自溯源问答】");
}

/* 是否当前登录用户自己的帖子 */
function isMyPost(p: any) {
  return !!userStore.token && !!p && p.author === userStore.username;
}

/* 删除自己的帖子（列表卡片 / 详情弹窗共用） */
async function confirmDelete(p: any) {
  if (!userStore.token) return ElMessage.warning("请先登录");
  try {
    await ElMessageBox.confirm(`确定删除帖子《${p.title || "未命名"}》吗？删除后不可恢复。`, "删除帖子", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch {
    return; // 用户取消
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
  if (boards.value.length) { newPost.value.board_id = boards.value[0].id; }
}

async function loadPosts() {
  loading.value = true;
  try {
    const params: Record<string, any> = { board_id: boardId.value, page: 1, page_size: 50, keyword: keyword.value || undefined };
    if (isAdmin.value && offlineOnly.value) params.status = "rejected";
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
  loadPosts();
}
function togglePending() {
  offlineOnly.value = !offlineOnly.value;
  boardId.value = null;
  keyword.value = "";
  loadPosts();
}

/* ---- Markdown 工具栏 ---- */
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
  // 在光标所在行开头加前缀
  const lineStart = newPost.value.content.lastIndexOf("\n", s - 1) + 1;
  newPost.value.content = newPost.value.content.slice(0, lineStart) + prefix + newPost.value.content.slice(lineStart);
  nextTick(() => { el.focus(); el.selectionStart = el.selectionEnd = s + prefix.length; });
}
function mdInsert(text: string) {
  newPost.value.content += text;
}

/* 编辑器内粘贴图片 */
async function onEditorPaste(e: ClipboardEvent) {
  const item = [...(e.clipboardData?.items || [])].find((it) => it.type.startsWith("image/"));
  if (!item) return;
  const f = item.getAsFile();
  if (!f) return;
  e.preventDefault();
  if (f.size > 8 * 1024 * 1024) { ElMessage.warning("图片过大，请选择 8MB 以内"); return; }
  imgUploading.value = true;
  try {
    const dataUrl = await compressImage(f, 900, 0.82);
    const url = await uploadImage(dataUrlToFile(dataUrl, "post.jpg"));
    newPost.value.image_url = url;
    ElMessage.success("已粘贴图片");
  } catch { ElMessage.error("图片上传失败"); }
  finally { imgUploading.value = false; }
}

async function doCreatePost() {
  if (!userStore.token) return ElMessage.warning("请先登录");
  if (!newPost.value.title.trim()) return ElMessage.warning("请输入标题");
  if (!newPost.value.content.trim()) return ElMessage.warning("请输入内容");
  posting.value = true;
  try {
    const res: any = await createPost({ ...newPost.value });
    ElMessage.success("发布成功");
    newPost.value = { board_id: 0, title: "", content: "", dynasty_tags: "", image_url: "" };
    postVisible.value = false;
    loadBoards();
    loadPosts();
  } finally { posting.value = false; }
}

/* ---- 管理员下架/恢复 ---- */
async function onOnline(id: number) {
  await onlinePost(id);
  ElMessage.success("已恢复");
  loadPosts();
}
async function onOffline(id: number) {
  await offlinePost(id);
  ElMessage.success("已下架");
  loadPosts();
}

async function openPost(id: number) {
  postDetail.value = await fetchPostDetail(id) as any;
  const lk = new Set(myInter.value.liked_posts || []);
  const cl = new Set(myInter.value.collected || []);
  liked.value = lk.has(id);
  collected.value = cl.has(id);
  detailVisible.value = true;
  replyText.value = "";
  replyTo.value = null;
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
    ElMessage.success(replyTo.value ? "已回复该条评论" : "回复成功");
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
  // 支持 ?post=id 直达：从个人中心收藏/发帖点击跳转时自动打开对应帖子
  const qp = Number(route.query.post);
  if (qp > 0) {
    await openPost(qp);
    routerReplace(qp);
  }
});

function routerReplace(id: number) {
  // 清除 query 参数，避免刷新后重复弹窗
  history.replaceState(null, "", "/community");
  void id;
}
</script>

<style scoped>
.page-sub { color: var(--ys-ink-3); margin: -6px 0 14px; }
.board-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.board-tab { padding: 6px 14px; border: 1px solid var(--ys-line); border-radius: 20px; cursor: pointer; background: #fffdf8; font-size: 14px; transition: all .2s; }
.board-tab:hover { border-color: var(--ys-red); color: var(--ys-red-deep); }
.board-tab.active { background: var(--ys-red); color: #fff; border-color: var(--ys-red); }
.board-tab i { font-style: normal; font-size: 11px; margin-left: 4px; opacity: 0.8; }
.community-layout { display: grid; grid-template-columns: 1fr 280px; gap: 16px; }
/* 用户作品区已迁移至「档案」「面料」页 */
.editor-head { display: flex; gap: 10px; }
.editor-mid { margin-bottom: 4px; display: flex; gap: 10px; align-items: center; }
.editor-img { margin: 8px 0; }
.img-preview { position: relative; display: inline-block; }
.img-preview img { max-width: 240px; max-height: 160px; border-radius: 8px; border: 1px solid var(--ys-line); display: block; }
.img-remove { position: absolute; top: 6px; right: 6px; background: rgba(0,0,0,.6); color: #fff; font-size: 12px; padding: 2px 8px; border-radius: 12px; cursor: pointer; }
.post-img { margin-top: 8px; }
.post-img img { max-width: 320px; max-height: 200px; border-radius: 8px; border: 1px solid var(--ys-line); object-fit: cover; }
.d-image { margin-top: 12px; }
.d-image img { max-width: 100%; max-height: 420px; border-radius: 8px; border: 1px solid var(--ys-line); }
.editor-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }
.editor-foot .note { font-size: 12px; color: var(--ys-ink-3); }
.list-toolbar { display: flex; align-items: center; gap: 8px; margin-top: 14px; }
.post-total { font-size: 12px; color: var(--ys-ink-3); }
.post-list { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
.post-card { padding: 14px 16px; transition: box-shadow .2s; }
.post-card:hover { box-shadow: 0 4px 16px rgba(122, 58, 32, .1); }
.post-main { cursor: pointer; }
.post-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.post-head h3 { margin: 0; font-size: 16px; }
.board-name { font-size: 11px; color: #fff; background: var(--ys-gold); border-radius: 4px; padding: 1px 6px; }
.qa-source-badge { font-size: 11px; color: #fff; background: var(--ys-red); border-radius: 4px; padding: 1px 8px; }
.pin { background: var(--ys-red); color: #fff; font-size: 11px; padding: 1px 8px; border-radius: 4px; }
.post-content { color: var(--ys-ink-2); font-size: 13px; line-height: 1.7; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.post-tags { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }
.post-foot { display: flex; align-items: center; gap: 14px; font-size: 12px; color: var(--ys-ink-3); margin-top: 10px; }
.interact { margin-left: auto; display: flex; gap: 10px; }
.interact b { font-weight: 400; cursor: pointer; user-select: none; }
.interact b:hover { color: var(--ys-red-deep); }
.interact b.liked { color: var(--ys-red-deep); font-weight: 600; }
.interact b.collected { color: var(--ys-red-deep); font-weight: 600; }
.del-post { color: var(--ys-red-deep); font-size: 12px; cursor: pointer; user-select: none; }
.del-post:hover { text-decoration: underline; }
.del-in-detail { margin-left: auto; }
.community-side { display: flex; flex-direction: column; gap: 14px; }
.rules { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ys-ink-2); line-height: 2; }
.side-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.side-tags .ys-tag.hot { cursor: default; }
.no-tags { font-size: 12px; color: var(--ys-ink-3); }
.d-post-meta { display: flex; gap: 12px; align-items: center; font-size: 13px; color: var(--ys-ink-3); flex-wrap: wrap; }
.d-content { margin: 12px 0; line-height: 1.9; }
.markdown-body :deep(p) { margin: 6px 0; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin: 10px 0 6px; font-size: 1.15em; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 20px; }
.markdown-body :deep(li) { margin: 3px 0; }
.markdown-body :deep(code) { background: #f4ecdf; padding: 1px 5px; border-radius: 4px; font-size: 12px; }
.markdown-body :deep(blockquote) { border-left: 3px solid var(--ys-gold); margin: 8px 0; padding: 4px 12px; color: var(--ys-ink-2); background: #f6efe4; }
.d-work { position: relative; display: inline-block; }
.confidence { position: absolute; right: 6px; bottom: 6px; background: rgba(46,36,26,.8); color: #fff; font-size: 12px; padding: 2px 10px; border-radius: 12px; }
.reply-item { border-bottom: 1px dashed var(--ys-line); padding: 8px 0; }
.reply-item.nested { margin-left: 30px; }
.r-head { display: flex; gap: 10px; font-size: 12px; color: var(--ys-ink-3); align-items: center; }
.r-user { color: var(--ys-red-deep); font-weight: 500; }
.r-parent { color: var(--ys-ink-3); }
.r-act { cursor: pointer; color: var(--ys-red-deep); font-size: 12px; }
.r-act:hover { text-decoration: underline; }
.r-time { margin-left: auto; }
.r-content { margin: 4px 0 0; line-height: 1.7; }
.reply-to { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--ys-ink-3); margin-top: 6px; }
.reply-to a { color: var(--ys-red-deep); cursor: pointer; }
.repost-target { font-size: 14px; color: var(--ys-ink-2); margin-bottom: 10px; }

/* Markdown 工具栏 */
.md-toolbar { display: flex; align-items: center; gap: 4px; margin-bottom: 8px; }
.md-btn {
  width: 30px; height: 30px; border: 1px solid var(--ys-line); background: #fbf6ec;
  border-radius: 6px; cursor: pointer; font-size: 13px; color: var(--ys-ink-2);
  display: flex; align-items: center; justify-content: center; transition: all .15s;
}
.md-btn:hover { background: #f3e6c8; border-color: var(--ys-gold); color: var(--ys-red-deep); }
.md-tip { margin-left: auto; font-size: 11px; color: var(--ys-ink-3); }
.editor-meta { text-align: right; font-size: 11px; color: var(--ys-ink-3); margin-top: 4px; }

.audit-btns b { cursor: pointer; margin-right: 10px; font-size: 13px; }
.audit-btns .approve { color: #2e7d32; }
.audit-btns .approve:hover { text-decoration: underline; }
.audit-btns .reject { color: #c0392b; }
.audit-btns .reject:hover { text-decoration: underline; }

/* 悬浮发帖小球 */
.fab-post {
  position: fixed;
  right: 30px;
  bottom: 34px;
  z-index: 60;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a8322c, #c74b3f);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 22px rgba(168, 50, 44, 0.38);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.fab-post:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 10px 26px rgba(168, 50, 44, 0.45); }
.fab-plus { font-size: 20px; line-height: 1; font-weight: 700; }
.fab-text { font-size: 12px; letter-spacing: 2px; margin-top: 2px; }
@media (max-width: 900px) {
  .community-layout { grid-template-columns: 1fr; }
  .fab-post { right: 18px; bottom: 22px; width: 56px; height: 56px; }
}
</style>
