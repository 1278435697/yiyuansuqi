import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/store/user";

const routes = [
  { path: "/", name: "home", component: () => import("@/views/HomeIndex.vue"), meta: { title: "文博资讯首页" } },
  { path: "/news/:id", name: "news-detail", component: () => import("@/views/NewsDetail.vue"), meta: { title: "资讯详情" } },
  { path: "/archive", name: "archive", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "华夏衣冠志 · 档案" } },
  { path: "/archive/:id", name: "archive-detail", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "档案详情" } },
  { path: "/timeline", name: "timeline", component: () => import("@/views/TimeGeo.vue"), meta: { title: "千年衣脉 · 时空图谱" } },
  { path: "/geomap", redirect: { path: "/timeline", query: { tab: "geo" } } },
  { path: "/aiqa", name: "aiqa", component: () => import("@/views/AiQaPage.vue"), meta: { title: "AI溯源问答" } },
  { path: "/community", name: "community", component: () => import("@/views/CommunityIndex.vue"), meta: { title: "国风社区" } },
  { path: "/community/:id", name: "post-detail", component: () => import("@/views/CommunityIndex.vue"), meta: { title: "帖子详情" } },
  { path: "/user", name: "user", component: () => import("@/views/UserCenter.vue"), meta: { title: "用户中心" } },
  { path: "/heritage", name: "heritage", component: () => import("@/views/HeritageGenerate.vue"), meta: { title: "文化传承" } },
  { path: "/fabric", name: "fabric", component: () => import("@/views/FabricArchive.vue"), meta: { title: "服装面料" } },
  { path: "/fabric/:id", name: "fabric-detail", component: () => import("@/views/FabricArchive.vue"), meta: { title: "面料详情" } },
  { path: "/pattern", name: "pattern-library", component: () => import("@/views/PatternLibrary.vue"), meta: { title: "纹样资料库" } },
  { path: "/pattern/:id", name: "pattern-detail", component: () => import("@/views/PatternLibrary.vue"), meta: { title: "纹样详情" } },
  { path: "/museum", name: "museum", component: () => import("@/views/MuseumView.vue"), meta: { title: "数字博物馆", bareLayout: true } },
  // 虚拟试穿模块（sidecar tryon_service:8000）：布局自带子导航与后端健康标签。
  // 不能挂在 /museum/ 下：那一段整目录由 3D 博物馆子站接管，同路径会落到它的占位页。
  {
    path: "/tryon",
    component: () => import("@/tryon/TryonLayout.vue"),
    meta: { title: "虚拟试穿" },
    children: [
      { path: "", name: "tryon", component: () => import("@/tryon/views/TryOnView.vue"), meta: { title: "虚拟试穿" } },
      { path: "gallery", name: "tryon-gallery", component: () => import("@/tryon/views/GalleryView.vue"), meta: { title: "服饰素材库" } },
      { path: "history", name: "tryon-history", component: () => import("@/tryon/views/HistoryView.vue"), meta: { title: "试穿记录" } },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const base = "衣溯 · 华夏衣冠志";
  document.title = to.meta.title ? `${String(to.meta.title)} · ${base}` : base;
  const userStore = useUserStore();
  // 未登录访问受保护页 → 跳用户中心（登录+个人中心二合一页）；登录页自身不触发守卫循环
  if (to.meta.requiresAuth && !userStore.token && to.path !== "/user") {
    return { path: "/user", query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;
