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
        <a href="/accessories/index.html">衣冠</a>
        <a href="/museum?v=20261018#/museum">博物馆</a>
        <router-link to="/tryon">虚拟试穿</router-link>
        <router-link to="/timeline">时空图谱</router-link>
        <router-link to="/aiqa">溯源问答</router-link>
        <router-link to="/community">社区</router-link>
        <a href="/heritage/index.html">传承</a>
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
        <transition name="page-enter" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <footer v-if="!isBare" class="app-footer">
      衣源溯起 — 衣冠有史，华服可溯
      <span class="footer-sub">让每一件华夏服饰有史可查、亲手可复 · AI Web 网页开发挑战赛作品</span>
    </footer>

    <!-- 全站图片点击放大 -->
    <ImageLightbox />

    <!-- 全局悬浮 AI 助手（沉浸式裸布局页面不显示） -->
    <AiAssistantFloat v-if="!isBare" />

    <!-- 全局浮动返回按钮（首页不显示） -->
    <button v-if="!isBare && route.path !== '/'" class="ys-back-fab" @click="goBack" title="返回上一页">
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

const showPreloader = ref(false);
const PRELOADER_SEEN_KEY = "yisu-preloader-seen";

onMounted(() => {
  // 开场动画只在「第一次进入首页」时播：整页加载 + 落在首页 + 本机没播过，三者都满足才播
  // 用 location 而不是 route.path：main.js 没有 await router.isReady()，挂载瞬间路由还停在初始 "/"
  try {
    const nav = performance.getEntriesByType("navigation")[0] as any;
    const navType = nav ? nav.type : "";
    const atHome = window.location.pathname === "/" || window.location.pathname === "/index.html";
    if (navType === "navigate" && atHome && !localStorage.getItem(PRELOADER_SEEN_KEY)) {
      localStorage.setItem(PRELOADER_SEEN_KEY, "1");
      showPreloader.value = true;
      (window as any).__preloaderActive = true;
    }
  } catch (e) {
    // 环境不支持时降级为不播，避免阻塞页面
  }
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
