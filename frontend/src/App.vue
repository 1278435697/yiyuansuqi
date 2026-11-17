<template>
  <div class="app-shell" :class="{ bare: isBare }">
    <!-- 全局背景层：桌面大图 / 小屏平铺纹理 + 纸白遮罩 -->
    <div class="app-bg"></div>
    <header v-if="!isBare" class="app-header">
      <div class="brand" @click="$router.push('/')">
        <img src="/logo.png" class="brand-logo" alt="衣源溯起" />
        <div class="brand-text">
          <h1>衣源溯起</h1>
          <p>华夏服饰溯源与复原平台</p>
        </div>
      </div>
      <nav class="app-nav">
        <router-link to="/">首页</router-link>
        <router-link to="/archive">档案</router-link>
        <router-link to="/fabric">面料</router-link>
        <router-link to="/pattern">纹样</router-link>
        <router-link to="/accessories">衣冠</router-link>
        <router-link to="/museum">博物馆</router-link>
        <router-link to="/fitview">虚拟试穿</router-link>
        <router-link to="/timeline">时空图谱</router-link>
        <router-link to="/aiqa">溯源问答</router-link>
        <router-link to="/community">社区</router-link>
        <router-link to="/heritage">传承</router-link>
      </nav>
      <div class="header-right">
        <el-button v-if="!userStore.token" type="primary" size="small" @click="$router.push('/user')">
          登录
        </el-button>
        <el-dropdown v-else @command="onUserCommand">
          <span class="user-chip">
            <img v-if="userStore.avatar" :src="userStore.avatar" class="chip-avatar" alt="头像" />
            {{ userStore.username }}
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="center">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="app-main" :class="{ bare: isBare }">
      <router-view v-slot="{ Component }">
        <component :is="Component" :key="route.path" class="page-fade" />
      </router-view>
    </main>

    <footer v-if="!isBare" class="app-footer">
      衣源溯起 — 衣冠有史，华服可溯
      <span class="footer-sub">让每一件华夏服饰有史可查、亲手可复 · 网页开发挑战赛作品</span>
    </footer>

    <!-- 全站图片点击放大 -->
    <ImageLightbox />

    <!-- 全局悬浮助手（沉浸式裸布局页面不显示；数字馆内已有「问导览」与深度解读，避免压住馆内面板） -->
    <AiAssistantFloat v-if="!isBare && !inMuseum" />

    <!-- 全局浮动返回按钮（首页不显示；数字馆内舞台是 WebGL 画布，全局 fixed 会被画布盖住，改由馆页自己出返回） -->
    <button v-if="showBackFab" class="ys-back-fab" @click="goBack" title="返回上一页">
      <span class="ys-back-arrow">←</span>
      <span class="ys-back-text">返回</span>
    </button>

    <!-- 全站加载页：圆形预加载器 → 点击进入 → 扫描退场 -->
    <Preloader v-if="showPreloader" @done="onPreloaderDone" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/store/user";
import ImageLightbox from "@/components/ImageLightbox.vue";
import Preloader from "@/components/Preloader.vue";
import AiAssistantFloat from "@/components/AiAssistantFloat.vue";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 浮动返回：有历史回退，无历史回首页
const goBack = () => {
  if (window.history.length > 1) router.back();
  else router.push("/");
};

// 数字博物馆等沉浸式页面走裸布局：隐藏站点头部/页脚，让 3D 舞台占满视口
const isBare = computed(() => Boolean(route.meta.bareLayout));

/** 数字馆（漫游馆）：馆页自己在左下出返回（全局 fixed 会被 WebGL 画布盖住）；AI 球让位给馆内导览 */
const inMuseum = computed(() => route.path.startsWith("/museum"));
const BACK_FAB_EXCLUDED = ["/museum", "/museum3d", "/museum-app"];
const showBackFab = computed(
  () => !isBare.value && route.path !== "/" && !BACK_FAB_EXCLUDED.includes(route.path),
);

const showPreloader = ref(false);

onMounted(() => {
  // 直接进入首页，不播开场动画
  window.dispatchEvent(new CustomEvent("preloader-done"));
});

function onPreloaderDone() {
  showPreloader.value = false;
  (window as any).__preloaderActive = false;
  // 通知各页面：开场动画已结束，现在才播放首页/模块的入场动效
  window.dispatchEvent(new CustomEvent("preloader-done"));
}

function onUserCommand(cmd: string) {
  if (cmd === "center") router.push("/user");
  if (cmd === "logout") userStore.logout();
}
</script>
