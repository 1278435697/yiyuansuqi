import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/store/user";

const routes = [
  { path: "/", name: "home", component: () => import("@/views/HomeIndex.vue"), meta: { title: "文博资讯首页" } },
  { path: "/news/:id", name: "news-detail", component: () => import("@/views/NewsDetail.vue"), meta: { title: "资讯详情" } },
  { path: "/archive", name: "archive", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "华夏衣冠志 · 档案" } },
  // 文物实例独立考证页（96 件实物的七字段详情）
  { path: "/archive/inst/:no", name: "archive-inst", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "文物实例考证" } },
  { path: "/archive/:id", name: "archive-detail", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "档案详情" } },
  // 衣冠频道：由独立静态站（public/accessories）迁入主工程，源码在 src/sites/accessories，图片在 public/acc-assets
  { path: "/accessories", name: "accessories", component: () => import("@/views/AccessoriesView.vue"), meta: { title: "服饰与配饰 · 九卷" } },
  { path: "/timeline", name: "timeline", component: () => import("@/views/TimeGeo.vue"), meta: { title: "千年衣脉 · 时空图谱" } },
  // 时空图谱：/geomap 是旧入口，重定向到时间轴页的出土地图 tab，并保留 relic 等查询参数
  { path: "/geomap", redirect: (to) => ({ path: "/timeline", query: { ...to.query, tab: "geo" } }) },
  { path: "/aiqa", name: "aiqa", component: () => import("@/views/AiQaPage.vue"), meta: { title: "溯源问答" } },
  { path: "/community", name: "community", component: () => import("@/views/CommunityIndex.vue"), meta: { title: "国风社区" } },
  { path: "/community/:id", name: "post-detail", component: () => import("@/views/CommunityIndex.vue"), meta: { title: "帖子详情" } },
  { path: "/user", name: "user", component: () => import("@/views/UserCenter.vue"), meta: { title: "用户中心" } },
  // 旧链接 /login 统一落到用户中心（登录 + 个人中心二合一页），避免旧入口点不动
  { path: "/login", redirect: (to) => ({ path: "/user", query: to.query }) },
  // 传承六卷：由独立静态站（public/heritage）迁入主工程，源码在 src/sites/heritage，图片在 public/her-assets
  { path: "/heritage", name: "heritage", component: () => import("@/views/HeritageVolumesView.vue"), meta: { title: "传统服饰非遗技艺 · 六卷" } },
  // 旧「AI 生成」页保留但不再占 /heritage，移到 /heritage/generate
  { path: "/heritage/generate", name: "heritage-generate", component: () => import("@/views/HeritageGenerate.vue"), meta: { title: "文化传承 · 图像生成" } },
  // 面料频道：由独立静态站（public/fabric-site）迁入主工程，源码在 src/sites/fabric，图片在 public/fab-assets
  { path: "/fabric", name: "fabric", component: () => import("@/views/FabricSiteView.vue"), meta: { title: "面料 · 中国传统丝织品知识库" } },
  { path: "/pattern", name: "pattern-library", component: () => import("@/views/PatternLibrary.vue"), meta: { title: "纹样资料库" } },
  { path: "/pattern/:id", name: "pattern-detail", component: () => import("@/views/PatternLibrary.vue"), meta: { title: "纹样详情" } },
  // 数字馆（主入口）：新交付的第一人称漫游馆（资源在 public/mus3d，React+three.js），iframe 承载
  { path: "/museum", name: "museum", component: () => import("@/views/MuseumHallView.vue"), meta: { title: "数字馆 · 华夏服饰漫游" } },
  // 同一座馆的第二入口（保留旧书签与历史链接）
  { path: "/museum3d", name: "museum3d", component: () => import("@/views/MuseumHallView.vue"), meta: { title: "数字馆 · 华夏服饰漫游" } },
  // 图录式旧馆（原独立 three.js 子站，资源在 public/mus-app）：不再进导航，保留可访问
  { path: "/museum-app", name: "museum-app", component: () => import("@/views/MuseumAppView.vue"), meta: { title: "数字博物馆（旧版图录）" } },
  // 虚拟试穿（新版）：AI 换装 + 三维建模，React 应用部署为 dist/fitview，由 FitViewView iframe 承载
  { path: "/fitview", name: "fitview", component: () => import("@/views/FitViewView.vue"), meta: { title: "换装 · 三维试穿" } },
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
