<template>
  <div class="user-page">
    <h2 class="ys-title">用户中心与权限体系</h2>

    <!-- 未登录：登录/注册 -->
    <div v-if="!userStore.token" class="auth-layout">
      <div class="ys-card auth-card">
        <el-tabs v-model="authMode" stretch>
          <el-tab-pane label="登录" name="login">
            <el-form label-width="70px" @submit.prevent>
              <el-form-item label="用户名"><el-input v-model="form.username" @keyup.enter="doLogin" /></el-form-item>
              <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password @keyup.enter="doLogin" /></el-form-item>
              <el-button type="primary" style="width: 100%" :loading="loading" @click="doLogin">登 录</el-button>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="注册" name="register">
            <el-form label-width="70px" @submit.prevent>
              <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
              <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
              <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
              <el-button type="primary" style="width: 100%" :loading="loading" @click="doRegister">注 册</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div class="ys-card auth-side">
        <h3 class="ys-title">为什么需要登录？</h3>
        <ul class="benefits">
          <li>保存你的溯源记录与收藏内容</li>
          <li>记录溯源学习行为，生成个性化方案</li>
          <li>参与社区发帖、问答与勘误共治</li>
          <li>管理员可进行内容审核与用户管理</li>
        </ul>
      </div>
    </div>

    <!-- 已登录：个人中心 -->
    <div v-else>
      <div class="profile-card ys-card">
        <div class="profile-head">
          <div class="avatar-wrap" data-lb-native @click="triggerAvatar">
            <img v-if="userStore.avatar" :src="userStore.avatar" class="avatar-img" alt="头像" />
            <div v-else class="avatar">{{ userStore.username?.[0]?.toUpperCase() }}</div>
            <div class="avatar-mask">
              <span v-if="avatarUploading">上传中…</span>
              <span v-else>更换头像</span>
            </div>
          </div>
          <input ref="avatarInput" type="file" accept="image/*" style="display: none" @change="onAvatarChange" />
          <div class="profile-info">
            <h3>
              {{ userStore.username }}
              <el-button size="small" text type="primary" @click="renameVisible = true">修改用户名</el-button>
            </h3>
            <div class="profile-meta">
              <span class="role-badge">{{ userStore.role === "superadmin" ? "总管" : userStore.role === "admin" ? "管理员" : "普通用户" }}</span>
              <span v-if="userStore.email" class="meta">{{ userStore.email }}</span>
              <span v-if="meInfo.create_time" class="meta">注册于 {{ meInfo.create_time.slice(0, 10) }}</span>
            </div>
          </div>
          <el-button size="small" @click="userStore.logout">退出登录</el-button>
        </div>

        <!-- 概览统计 -->
        <div class="stats-row">
          <div class="stat-item" @click="tab = 'posts'">
            <b>{{ stats.posts }}</b><span>我的发帖</span>
          </div>
          <div class="stat-item" @click="tab = 'collections'">
            <b>{{ stats.collections }}</b><span>收藏</span>
          </div>
          <div class="stat-item" @click="tab = 'logs'">
            <b>{{ stats.logs }}</b><span>溯源记录</span>
          </div>
          <div class="stat-item" @click="tab = 'questions'">
            <b>{{ stats.questions }}</b><span>问答</span>
          </div>
        </div>
      </div>

      <el-tabs v-model="tab" class="center-tabs" @tab-change="onTabChange">
        <el-tab-pane label="溯源记录" name="logs">
          <div v-loading="tabLoading" class="log-list" v-if="logs.length">
            <div v-for="(l, i) in logs" :key="i" class="log-item">
              <span class="act-badge" :class="l.action_type">{{ actionText(l.action_type) }}</span>
              <span>{{ l.costume_name ? `《${l.costume_name}》` : `服饰档案 #${l.costume_id}` }}</span>
              <span class="time">{{ l.create_time?.slice(0, 10) }}</span>
            </div>
          </div>
          <div v-else-if="!tabLoading" class="ys-empty">
            暂无溯源记录，<a @click="go('/archive')">去档案页浏览服饰 ›</a>
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的发帖" name="posts">
          <div v-loading="tabLoading" class="log-list" v-if="posts.length">
            <div v-for="p in posts" :key="p.id" class="log-item post-item" @click="go(`/community?post=${p.id}`)">
              <div class="post-title">
                <span class="board-tag">{{ p.board_name }}</span>
                <b>{{ p.title }}</b>
                <span v-if="p.dynasty_tags" class="ys-tag" v-for="t in p.dynasty_tags.split(',')" :key="t" v-show="t">{{ t }}</span>
              </div>
              <span class="post-stats">赞 {{ p.like_count }} · 回 {{ p.reply_count }}</span>
              <span class="time">{{ p.create_time?.slice(0, 10) }} <el-button size="small" type="danger" link @click.stop="delMyPost(p)">删除</el-button></span>
            </div>
          </div>
          <div v-else-if="!tabLoading" class="ys-empty">
            暂无发帖，<a @click="go('/community')">去社区发第一帖 ›</a>
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的收藏" name="collections">
          <div v-loading="tabLoading" class="log-list" v-if="collections.length">
            <div v-for="(c, i) in collections" :key="i" class="log-item post-item"
                 :class="{ clickable: c.post_id }" @click="c.post_id && go(`/community?post=${c.post_id}`)">
              <div class="post-title">
                <b>{{ c.post_title || (c.costume_id ? `服饰档案 #${c.costume_id}` : `作品 #${c.work_id}`) }}</b>
                <span class="folder-tag">{{ c.folder_name || "默认收藏" }}</span>
              </div>
              <span class="time">{{ c.post_time?.slice(0, 10) }}</span>
            </div>
          </div>
          <div v-else-if="!tabLoading" class="ys-empty">
            还没有收藏，<a @click="go('/community')">去社区收藏好帖 ›</a>
          </div>
        </el-tab-pane>

        <el-tab-pane label="我的问答" name="questions">
          <div v-loading="tabLoading" class="log-list" v-if="questions.length">
            <div v-for="q in questions" :key="q.id" class="log-item post-item clickable" @click="go(`/aiqa?question=${q.id}`)">
              <b>{{ q.title }}</b>
              <span class="time">{{ q.create_time?.slice(0, 10) }} <el-button size="small" type="danger" link @click.stop="delMyQuestion(q)">删除</el-button></span>
            </div>
          </div>
          <div v-else-if="!tabLoading" class="ys-empty">
            暂无提问，<a @click="go('/aiqa')">去溯源问答提问 ›</a>
          </div>
        </el-tab-pane>

        <el-tab-pane label="管理员" name="admin" v-if="userStore.role === 'admin' || userStore.role === 'superadmin'">
          <div class="admin-grid">
            <div class="ys-card">
              <h4 class="ys-title">用户管理</h4>
              <div v-for="u in adminUsers" :key="u.id" class="log-item admin-user">
                <b>{{ u.username }}</b><span class="email">{{ u.email }}</span>
                <span class="role-badge">{{ u.role === "superadmin" ? "总管" : u.role === "admin" ? "管理员" : "普通用户" }}</span>
                <el-button size="small" v-if="u.role !== 'superadmin'" @click="toggleRole(u)">{{ u.role === "admin" ? "降为普通" : "设为管理员" }}</el-button>
              </div>
            </div>
            <div class="ys-card">
              <h4 class="ys-title">帖子审核（最新 100 帖）</h4>
              <div v-for="p in auditPosts" :key="p.id" class="log-item admin-post">
                <div class="post-title">
                  <b>{{ p.title }}</b>
                  <span class="email">{{ p.author }}</span>
                </div>
                <span class="audit-snippet">{{ p.content }}</span>
                <el-button size="small" type="danger" plain :loading="delLoading === p.id" @click="deletePost(p)">删除</el-button>
              </div>
              <div v-if="!auditPosts.length" class="ys-empty">暂无帖子</div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 图片灯箱 -->
    <el-dialog v-model="lightboxVisible" width="auto" :show-close="true" align-center>
      <img :src="lightboxUrl" alt="预览大图" style="max-width: 80vw; max-height: 80vh; border-radius: 8px" />
    </el-dialog>

    <!-- 修改用户名 -->
    <el-dialog v-model="renameVisible" title="修改用户名" width="380px" align-center>
      <el-input v-model="newName" placeholder="输入新用户名（2-20 个字符）" maxlength="20" show-word-limit @keyup.enter="doRename" />
      <p class="rename-tip">修改后登录名同步变更，你发布的帖子与作品会跟随显示新用户名。</p>
      <template #footer>
        <el-button @click="renameVisible = false">取消</el-button>
        <el-button type="primary" :loading="renameLoading" @click="doRename">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useUserStore } from "@/store/user";
import {
  fetchMyLogs, fetchMyStats, fetchMyCollections,
  fetchMyPosts, fetchMyQuestions, adminDeletePost, fetchAuditPosts, updateAvatar,
  uploadImage, deletePost, deleteQuestion,
} from "@/api/modules";
import request from "@/api/request";

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const authMode = ref("login");
const form = ref({ username: "", password: "", email: "" });
const loading = ref(false);
const tab = ref("logs");
const tabLoading = ref(false);
const meInfo = ref<any>({});
const stats = ref<any>({ logs: 0, posts: 0, collections: 0, questions: 0 });
const logs = ref<any[]>([]);
const posts = ref<any[]>([]);
const collections = ref<any[]>([]);
const questions = ref<any[]>([]);
const adminUsers = ref<any[]>([]);
const auditPosts = ref<any[]>([]);
const delLoading = ref<number | null>(null);
const lightboxVisible = ref(false);
const lightboxUrl = ref("");
const avatarInput = ref<HTMLInputElement | null>(null);
const avatarUploading = ref(false);
const renameVisible = ref(false);
const newName = ref("");
const renameLoading = ref(false);

const loadedTabs = new Set<string>();

const ACTION_TEXT: Record<string, string> = {
  view: "浏览", search: "搜索", draft: "打版", like: "点赞", post: "发帖", restore: "复原",
};

function actionText(a: string) {
  return ACTION_TEXT[a] || a;
}

function go(path: string) {
  router.push(path);
}

function lightbox(url: string) {
  lightboxUrl.value = url;
  lightboxVisible.value = true;
}

/* ---- 头像上传 ---- */
function triggerAvatar() {
  avatarInput.value?.click();
}

async function doRename() {
  const name = newName.value.trim();
  if (!name) { ElMessage.warning("请输入新用户名"); return; }
  if (name.length < 2 || name.length > 20) { ElMessage.warning("用户名长度需为 2-20 个字符"); return; }
  renameLoading.value = true;
  try {
    await userStore.updateUsername(name);
    ElMessage.success("用户名已更新");
    renameVisible.value = false;
    newName.value = "";
    loadProfile();
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "修改失败");
  } finally {
    renameLoading.value = false;
  }
}

async function onAvatarChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (!file.type.startsWith("image/")) { ElMessage.warning("请选择图片文件"); return; }
  if (file.size > 8 * 1024 * 1024) { ElMessage.warning("图片过大，请选择 8MB 以内的图片"); return; }
  avatarUploading.value = true;
  try {
    const dataUrl = await compressImage(file, 256, 0.82);
    const url = await uploadImage(dataUrlToFile(dataUrl, "avatar.jpg"));
    const res: any = await updateAvatar(url);
    userStore.saveAvatar(res.avatar);
    ElMessage.success("头像已更新");
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "头像上传失败");
  } finally {
    avatarUploading.value = false;
  }
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
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, width, height);
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

async function doLogin() {
  loading.value = true;
  try {
    await userStore.login(form.value.username, form.value.password);
    ElMessage.success("登录成功");
    initAfterAuth();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "登录失败");
  } finally { loading.value = false; }
}

async function doRegister() {
  loading.value = true;
  try {
    await userStore.register(form.value.username, form.value.password, form.value.email);
    ElMessage.success("注册成功");
    initAfterAuth();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "注册失败");
  } finally { loading.value = false; }
}

async function initAfterAuth() {
  loadedTabs.clear();
  tab.value = "logs";
  await loadProfile();
  await loadTab("logs");
  if (userStore.role === "admin" || userStore.role === "superadmin") loadAdmin();
}

async function loadProfile() {
  try { meInfo.value = await request.get("/user/me") as any; } catch { /* ignore */ }
  try {
    stats.value = (await fetchMyStats()) as any;
    userStore.email = meInfo.value?.email || "";
  } catch { /* ignore */ }
}

async function loadTab(name: string) {
  tabLoading.value = true;
  try {
    if (name === "logs" && !loadedTabs.has("logs")) {
      logs.value = ((await fetchMyLogs()) as any).items || [];
      loadedTabs.add("logs");
    } else if (name === "posts" && !loadedTabs.has("posts")) {
      posts.value = ((await fetchMyPosts()) as any).items || [];
      loadedTabs.add("posts");
    } else if (name === "collections" && !loadedTabs.has("collections")) {
      collections.value = ((await fetchMyCollections()) as any).items || [];
      loadedTabs.add("collections");
    } else if (name === "questions" && !loadedTabs.has("questions")) {
      questions.value = ((await fetchMyQuestions()) as any).items || [];
      loadedTabs.add("questions");
    }
  } finally { tabLoading.value = false; }
}

function onTabChange(name: string | number) {
  if (userStore.token && !loadedTabs.has(String(name))) {
    loadTab(String(name));
  }
}

async function delMyPost(p: any) {
  try {
    await deletePost(p.id);
    ElMessage.success("已删除");
    posts.value = posts.value.filter((x: any) => x.id !== p.id);
  } catch (e: any) {
    ElMessage.error("删除失败：" + (e?.response?.data?.detail || e.message));
  }
}
async function delMyQuestion(q: any) {
  try {
    await deleteQuestion(q.id);
    ElMessage.success("已删除");
    questions.value = questions.value.filter((x: any) => x.id !== q.id);
  } catch (e: any) {
    ElMessage.error("删除失败：" + (e?.response?.data?.detail || e.message));
  }
}

async function loadAdmin() {
  try { adminUsers.value = ((await request.get("/user/admin/users")) as any).items || []; } catch { /* ignore */ }
  try { auditPosts.value = (await fetchAuditPosts() as any).items || []; } catch { /* ignore */ }
}

async function toggleRole(u: any) {
  const role = u.role === "admin" ? "user" : "admin";
  await request.post(`/user/admin/users/${u.id}/role`, null, { params: { role } });
  ElMessage.success(`已切换 ${u.username} 为${role === "admin" ? "管理员" : "普通用户"}`);
  loadAdmin();
}

async function deletePost(p: any) {
  delLoading.value = p.id;
  try {
    await adminDeletePost(p.id);
    ElMessage.success(`已删除帖子「${p.title}」`);
    auditPosts.value = auditPosts.value.filter((x) => x.id !== p.id);
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败");
  } finally { delLoading.value = null; }
}

onMounted(async () => {
  await userStore.loadMe();
  if (userStore.token) {
    initAfterAuth();
    const qp = route.query.post;
    if (qp) tab.value = "posts";
  }
});

watch(() => userStore.token, (v) => {
  if (v) initAfterAuth();
});
</script>

<style scoped>
.auth-layout { display: grid; grid-template-columns: 420px 1fr; gap: 20px; }
.auth-card { max-width: 460px; }
.benefits { line-height: 2.2; color: var(--ys-ink-2); font-size: 14px; }
.profile-card { margin-bottom: 16px; padding: 20px 24px; }
.profile-head { display: flex; align-items: center; gap: 16px; }
.avatar { width: 58px; height: 58px; border-radius: 50%; background: var(--ys-red); color: #fff; display: grid; place-items: center; font-size: 26px; font-weight: 700; }
.avatar-wrap { position: relative; width: 58px; height: 58px; border-radius: 50%; cursor: pointer; overflow: hidden; flex-shrink: 0; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.avatar-wrap .avatar { width: 100%; height: 100%; border-radius: 50%; }
.avatar-mask { position: absolute; inset: 0; border-radius: 50%; background: rgba(0,0,0,.45); color: #fff; font-size: 11px; display: grid; place-items: center; opacity: 0; transition: opacity .2s; }
.avatar-wrap:hover .avatar-mask { opacity: 1; }
.profile-info { flex: 1; }
.profile-info h3 { margin: 0 0 6px; display: flex; align-items: center; gap: 8px; }
.rename-tip { font-size: 12px; color: var(--ys-ink-3); margin: 8px 0 0; line-height: 1.6; }
.profile-meta { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.meta { font-size: 12px; color: var(--ys-ink-3); }
.role-badge { background: var(--ys-bg-deep); color: var(--ys-red-deep); font-size: 12px; padding: 1px 10px; border-radius: 10px; }
.stats-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-top: 18px; }
.stat-item { background: #f6efe4; border: 1px solid var(--ys-line); border-radius: 10px; padding: 12px 8px; text-align: center; cursor: pointer; transition: all .2s; }
.stat-item:hover { background: #fffdf8; border-color: var(--ys-red); transform: translateY(-2px); }
.stat-item b { display: block; font-size: 22px; color: var(--ys-red-deep); }
.stat-item span { font-size: 12px; color: var(--ys-ink-3); }
.center-tabs { margin-top: 8px; }
.log-list { display: flex; flex-direction: column; gap: 8px; }
.log-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #fffdf8; border: 1px solid var(--ys-line); border-radius: 8px; font-size: 13px; }
.log-item .time { margin-left: auto; color: var(--ys-ink-3); font-size: 12px; }
.act-badge { font-size: 11px; color: #fff; border-radius: 4px; padding: 1px 8px; background: var(--ys-ink-3); white-space: nowrap; }
.act-badge.view { background: #8a6d5a; }
.act-badge.search { background: #5d7a8a; }
.act-badge.draft { background: #8a7a5d; }
.act-badge.like { background: #b0564a; }
.act-badge.post { background: #5d8a68; }
.grid-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.mini-card h4 { margin: 0 0 6px; font-size: 14px; }
.mini-card .time { font-size: 12px; color: var(--ys-ink-3); }
.draft-preview img { max-width: 140px; border-radius: 6px; }
.work-img { position: relative; }
.work-img img { width: 100%; max-height: 170px; object-fit: cover; border-radius: 6px; cursor: zoom-in; }
.no-img { height: 120px; display: grid; place-items: center; background: #f4ecdf; color: var(--ys-ink-3); border-radius: 6px; font-size: 12px; }
.public-badge { position: absolute; top: 6px; right: 6px; background: rgba(126,36,24,.85); color: #fff; font-size: 11px; padding: 1px 8px; border-radius: 10px; }
.work-meta { display: flex; flex-direction: column; gap: 2px; margin-top: 6px; font-size: 12px; color: var(--ys-ink-2); }
.post-item { cursor: default; }
.post-item.clickable { cursor: pointer; }
.post-item.clickable:hover { border-color: var(--ys-red); background: #fdf8f0; }
.post-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; }
.board-tag { font-size: 11px; color: #fff; background: var(--ys-gold); border-radius: 4px; padding: 1px 6px; }
.folder-tag { font-size: 11px; color: var(--ys-ink-3); border: 1px solid var(--ys-line); border-radius: 10px; padding: 0 8px; }
.post-stats { font-size: 12px; color: var(--ys-ink-3); white-space: nowrap; }
.ys-empty a { color: var(--ys-red-deep); cursor: pointer; text-decoration: underline; }
.admin-grid { display: grid; grid-template-columns: 1fr 1.4fr; gap: 16px; }
.admin-user { flex-wrap: wrap; }
.email { color: var(--ys-ink-3); font-size: 12px; }
.admin-post { flex-wrap: wrap; }
.audit-snippet { flex: 1; color: var(--ys-ink-2); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 900px) {
  .stats-row { grid-template-columns: repeat(3, 1fr); }
  .admin-grid { grid-template-columns: 1fr; }
  .auth-layout { grid-template-columns: 1fr; }
}
</style>
