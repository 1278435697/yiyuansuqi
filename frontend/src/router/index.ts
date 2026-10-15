import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/store/user";

const routes = [
  { path: "/", name: "home", component: () => import("@/views/HomeIndex.vue"), meta: { title: "文博资讯首页" } },
  { path: "/news/:id", name: "news-detail", component: () => import("@/views/NewsDetail.vue"), meta: { title: "资讯详情" } },
  { path: "/archive", name: "archive", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "衣溯AI档案" } },
  { path: "/archive/:id", name: "archive-detail", component: () => import("@/views/CostumeArchive.vue"), meta: { title: "档案详情" } },
  { path: "/timeline", name: "timeline", component: () => import("@/views/TimeLine.vue"), meta: { title: "千年衣脉时间轴" } },
  { path: "/geomap", name: "geomap", component: () => import("@/views/GeoHeatMap.vue"), meta: { title: "服饰出土地图" } },
  { path: "/aiqa", name: "aiqa", component: () => import("@/views/AiQaPage.vue"), meta: { title: "AI溯源问答" } },
  { path: "/community", name: "community", component: () => import("@/views/CommunityIndex.vue"), meta: { title: "国风社区" } },
  { path: "/community/:id", name: "post-detail", component: () => import("@/views/CommunityIndex.vue"), meta: { title: "帖子详情" } },
  { path: "/user", name: "user", component: () => import("@/views/UserCenter.vue"), meta: { title: "用户中心" } },
  { path: "/heritage", name: "heritage", component: () => import("@/views/HeritageGenerate.vue"), meta: { title: "文化传承" } },
  { path: "/fabric", name: "fabric", component: () => import("@/views/FabricArchive.vue"), meta: { title: "服装面料" } },
  { path: "/fabric/:id", name: "fabric-detail", component: () => import("@/views/FabricArchive.vue"), meta: { title: "面料详情" } },
  { path: "/museum", name: "museum", component: () => import("@/views/MuseumView.vue"), meta: { title: "数字博物馆", bareLayout: true } },
  { path: "/museum/tryon", name: "tryon", component: () => import("@/views/TryonPlaceholder.vue"), meta: { title: "虚拟试穿", bareLayout: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  document.title = `${String(to.meta.title ?? "衣溯AI")} · 衣溯AI`;
  const userStore = useUserStore();
  // 未登录访问受保护页 → 跳用户中心（登录+个人中心二合一页）；登录页自身不触发守卫循环
  if (to.meta.requiresAuth && !userStore.token && to.path !== "/user") {
    return { path: "/user", query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;
