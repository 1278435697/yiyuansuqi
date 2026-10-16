<template>
  <div class="app-shell" :class="{ bare: isBare }">
    <!-- 全局背景层：桌面大图 / 小屏平铺纹理 + 纸白遮罩 -->
    <div class="app-bg"></div>
    <header v-if="!isBare" class="app-header">
      <div class="brand" @click="$router.push('/')">
        <span class="brand-seal">衣溯</span>
        <div class="brand-text">
          <h1>衣溯AI</h1>
          <p>华夏服饰溯源与复原平台</p>
        </div>
      </div>
      <nav class="app-nav">
        <router-link to="/">首页</router-link>
        <router-link to="/archive">档案</router-link>
        <router-link to="/museum">博物馆</router-link>
        <router-link to="/fabric">面料</router-link>
        <router-link to="/pattern">纹样</router-link>
        <router-link to="/timeline">时间轴</router-link>
        <router-link to="/geomap">出土地图</router-link>
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
        <transition name="page-enter" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <footer v-if="!isBare" class="app-footer">
      衣溯AI · 让每一件华夏服饰有史可查、亲手可复 — AI Web 网页开发挑战赛作品
    </footer>

    <!-- 全站图片点击放大 -->
    <ImageLightbox />

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

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 数字博物馆等沉浸式页面走裸布局：隐藏站点头部/页脚，让 3D 舞台占满视口
const isBare = computed(() => Boolean(route.meta.bareLayout));

const showPreloader = ref(false);

onMounted(() => {
  // 开场动画：只在“输入网址进入”时播放（浏览器导航加载）；刷新 / 前进后退 / 站内跳转不播
  try {
    const nav = performance.getEntriesByType("navigation")[0] as any;
    const navType = nav ? nav.type : "";
    if (navType === "navigate") {
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
