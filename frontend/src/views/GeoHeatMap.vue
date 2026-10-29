<template>
  <div class="geomap-page">
    <div class="map-layout anim-stagger">
      <div class="map-wrap">
        <div class="map-card ys-card">
          <div class="map-head">
            <el-select v-model="dynasty" placeholder="全部朝代" clearable size="small" style="width: 130px" @change="loadRelics">
              <el-option v-for="d in dynastyOptions" :key="d" :label="d" :value="d" />
            </el-select>
            <el-radio-group v-model="heatMode" size="small" @change="renderMap">
              <el-radio-button label="marker">标注</el-radio-button>
              <el-radio-button label="heat">热力</el-radio-button>
            </el-radio-group>
            <el-button size="small" :type="ancient ? 'danger' : 'default'" plain @click="toggleAncient">古代舆图</el-button>
          </div>
          <div ref="mapEl" class="map-canvas"></div>
          <p class="map-note">点击标注点查看出土文物与关联服饰档案</p>
        </div>

        <!-- 选中文物：置于地图正下方，点几件列几件 -->
        <div class="ys-card relic-below">
          <h3 class="ys-title">选中文物<template v-if="selectedItems.length"><span class="cnt">（{{ selectedItems.length }} 件）</span></template></h3>
          <div v-if="selectedItems.length" class="rel-list">
            <div v-for="r in selectedItems" :key="(r._isCostume ? 'c' : 'r') + r.id" class="rel-row">
              <div class="rel-img-box" v-if="r.image_url">
                <img :src="r.image_url" :alt="r.name" class="rel-img" />
              </div>
              <div v-else class="rel-img-box rel-img-empty">暂无实物照片</div>
              <div class="rel-info">
                <h4>{{ r.name }}</h4>
                <p>{{ r.dynasty }} · {{ r.location }}</p>
                <p class="museum">{{ r.museum }}</p>
                <p class="desc">{{ r.description }}</p>
                <div class="rel-costumes">
                  <el-tag v-for="c in r.costumes" :key="c.id" size="small"
                          class="c-tag" @click="$router.push(`/archive/${c.id}`)">{{ c.name }}</el-tag>
                </div>
                <el-button v-if="r.costumes && r.costumes.length" link type="primary" size="small" class="go-archive"
                           @click="$router.push(`/archive/${r.costumes[0].id}`)">查看档案详情 ›</el-button>
              </div>
            </div>
          </div>
          <div v-else class="ys-empty">点击地图标注点查看文物详情</div>
        </div>
      </div>

      <aside class="map-side">
        <div class="ys-card">
          <h3 class="ys-title">按朝代分布</h3>
          <div ref="dynastyChart" style="height: 220px"></div>
        </div>
        <div class="ys-card">
          <h3 class="ys-title">出土热点地区</h3>
          <div ref="locChart" style="height: 260px"></div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import * as echarts from "echarts";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchRelics, fetchGeoStats, fetchMapConfig } from "@/api/modules";
import request from "@/api/request";
import PageHero from "@/components/PageHero.vue";

const dynasty = ref("");
const heatMode = ref("marker");
const ancient = ref(false);
const router = useRouter();
const route = useRoute();
const dynastyOptions = ["上古", "先秦", "秦汉", "魏晋", "隋唐", "宋", "元", "明", "清"];
const relics = ref<any[]>([]);
const selectedItems = ref<any[]>([]);
const mapEl = ref<HTMLDivElement>();
const dynastyChart = ref<HTMLDivElement>();
const locChart = ref<HTMLDivElement>();
let map: any = null;
let tileLayer: any = null;
let ancientLayer: any = null;
let customLayers: any[] = [];
let charts: echarts.ECharts[] = [];

async function loadRelics() {
  const data: any = await fetchRelics({ dynasty: dynasty.value });
  relics.value = data.items;
  renderMap();
}

async function renderMap() {
  if (!mapEl.value) return;
  if (!map) {
    const cfg: any = await fetchMapConfig();
    map = L.map(mapEl.value, { center: cfg.default_center, zoom: cfg.default_zoom, scrollWheelZoom: true, minZoom: cfg.min_zoom || 3 });
    tileLayer = L.tileLayer(cfg.tile_url, { attribution: cfg.attribution, subdomains: cfg.subdomains || "abc", maxZoom: cfg.max_zoom || 10 });
    tileLayer.addTo(map);
    if (ancient.value) {
      ancientLayer = L.imageOverlay(buildAncientImage(), [[15, 70], [55, 140]], { opacity: 0.95, interactive: false });
      ancientLayer.addTo(map);
      tileLayer.setOpacity(0.18);
    }
  }
  // 移除旧的自定义图层
  customLayers.forEach((layer) => map.removeLayer(layer));
  customLayers = [];

  // 弹窗：多件通用（标注模式单件数组，热力模式同组数组）
  const popupFor = (items: any[]) => {
    const rows = items
      .map((it) => {
        const cos = (it.costumes || [])
          .map(
            (c: any) =>
              `<div class="heat-item" data-cid="${c.id}" data-cname="${c.name}">` +
              `<span class="hi-name">${c.name}</span>` +
              `<a class="heat-go">档案详情 ›</a></div>`
          )
          .join("");
        return `<div class="heat-row"><b>${it.name}</b><br><span class="hp-sub">${it.dynasty} · ${it.location} · ${it.museum || ""}</span>${cos}</div>`;
      })
      .join("");
    return `<div class="heat-pop">${rows}</div>`;
  };
/* 档案权威图映射（与档案详情页 COSTUME_DETAILS 一致）：名称 → 实物/图像 */
const COSTUME_IMG: Record<string, string> = {
  深衣: "/images/relics/relic_xianqin_shenyi.jpg",
  素纱单衣: "/images/relics/relic_han_susha.jpg",
  曲裾深衣: "/images/relics/relic_han_quju_v2.jpg",
  宽衫大袖: "/images/relics/relic_weijin_kuanshan.jpg",
  大袖襦裙: "/images/relics/relic_tang_ruqun.jpg",
  圆领袍: "/images/relics/relic_tang_yuanling.jpg",
  褙子: "/images/relics/relic_song_beizi.jpg",
  质孙服: "/images/relics/relic_yuan_zhisun.jpg",
  马面裙: "/images/relics/relic_ming_maqun.jpg",
  旗装: "/images/relics/relic_qing_qizhuang.jpg",
  冕服: "/images/relics/relic_xianqin_mianfu.jpg",
  凤鸟纹绣绢䋺衣: "/images/relics/relic_xianqin_fengniaoxiu.jpg",
  信期绣绵袍: "/images/relics/relic_han_xinqixiu.jpg",
  印花敷彩丝绵袍: "/images/relics/relic_han_yinhuafucai.jpg",
  魏晋襦裙: "/images/relics/relic_weijin_ruqun.jpg",
  裲裆: "/images/relics/relic_weijin_liangdang.jpg",
  半臂: "/images/relics/relic_tang_banbi.jpg",
  "胡服·缺胯袍": "/images/relics/relic_tang_hufu.jpg",
  幞头: "/images/relics/relic_tang_futou.jpg",
  "大袖·礼衣": "/images/relics/relic_song_daxiu.jpg",
  朱子深衣: "/images/relics/relic_song_zhuzishenyi.jpg",
  辫线袄: "/images/relics/relic_yuan_bianxianao.jpg",
  姑姑冠: "/images/relics/relic_yuan_guguguan.jpg",
  道袍: "/images/relics/relic_ming_daopao.jpg",
  "补服·官服": "/images/relics/relic_ming_bufu.jpg",
  袄裙: "/images/relics/relic_ming_aoqun.jpg",
  马褂: "/images/relics/relic_qing_magua.jpg",
  氅衣: "/images/relics/relic_qing_changyi.jpg",
  坎肩: "/images/relics/relic_qing_kanjian.jpg",
  定陵织金妆花缎: "/images/relics/relic_geo_dingling_zhuanghua.jpg",
  敦煌供养人像壁画: "/images/relics/relic_geo_dunhuang_tang.jpg",
  集宁路织金锦: "/images/relics/relic_geo_jininglu_zhijin.jpg",
  马山一号楚墓丝袍: "/images/relics/relic_geo_mashan_jinpao.jpg",
  孔府桃红纱大袖衫: "/images/relics/relic_geo_kongfu_daxiushan.jpg",
};

  /* 最长公共子串长度：用于判定高度相似的"同名文物"（如 孔府旧藏桃红纱大袖衫 vs 孔府桃红纱大袖衫） */
  const lcsLen = (a: string, b: string): number => {
    const m = a.length, n = b.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
    let best = 0;
    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (a[i - 1] === b[j - 1]) {
          dp[i][j] = dp[i - 1][j - 1] + 1;
          if (dp[i][j] > best) best = dp[i][j];
        } else dp[i][j] = 0;
      }
    }
    return best;
  };

  /* 选中文物统一计算：遗址本体 + 该遗址其余不同文物档案逐件列出。
     去重规则：同名档案、名称互相包含的档案、高度相似档案、仅关联 1 条档案的遗址（该档案即遗址本身）、以及列表中已有的同名项，都不再单列 */
  const buildSelectedItems = (items: any[]): any[] => {
    const list: any[] = [];
    for (const it of items) {
      list.push(it);
      const cos = it.costumes || [];
      for (const c of cos) {
        const same =
          c.name === it.name ||
          (it.name.includes(c.name) && it.name.length > c.name.length) ||
          (c.name.includes(it.name) && c.name.length > it.name.length) ||
          lcsLen(it.name, c.name) / Math.max(it.name.length, c.name.length) >= 0.55;
        if (cos.length === 1 || same) continue;
        if (list.some((x: any) => x.name === c.name)) continue;
        list.push({
          ...c,
          _isCostume: true,
          costumes: [c],
          dynasty: it.dynasty,
          location: it.location,
          museum: it.museum,
          image_url: c.image_url || COSTUME_IMG[c.name] || it.image_url || "",
        });
      }
    }
    return list;
  };

  const bindPopupEvents = (layer: any, items: any[]) => {
    layer.on("popupopen", () => {
      const pop = layer.getPopup()?.getElement();
      if (!pop) return;
      pop.querySelectorAll(".heat-item").forEach((el: any) => {
        const cid = Number(el.dataset.cid);
        el.addEventListener("click", (e: Event) => {
          e.stopPropagation();
          router.push(`/archive/${cid}`);
        });
      });
    });
    layer.on("click", () => {
      // 直接弹 popup，用户在 popup 里点具体件进详情；不在下方列卡片
    });
  };

  if (heatMode.value === "heat") {
    // 热力模式：同地点合并为一个圈，半径/浓度随件数，中心显示件数
    const hgroup = new Map<string, { lat: number; lng: number; items: any[] }>();
    for (const r of relics.value) {
      const key = `${Math.round(r.geo_lat * 10) / 10},${Math.round(r.geo_lng * 10) / 10}`;
      if (!hgroup.has(key)) hgroup.set(key, { lat: r.geo_lat, lng: r.geo_lng, items: [] });
      hgroup.get(key)!.items.push(r);
    }
    hgroup.forEach((g) => {
      const count = buildSelectedItems(g.items).length;
      const circle = L.circle([g.lat, g.lng], {
        radius: 20000 + count * 16000,
        color: "#a93226", fillColor: "#a93226", fillOpacity: 0.22 + Math.min(0.5, count * 0.09),
      });
      const numIcon = L.divIcon({
        className: "heat-num",
        html: `<span>${count}</span>`,
        iconSize: [24, 24], iconAnchor: [12, 12],
      });
      const numMarker = L.marker([g.lat, g.lng], { icon: numIcon, interactive: false });
      customLayers.push(circle, numMarker);
      circle.bindPopup(popupFor(g.items), { maxWidth: 360 });
      bindPopupEvents(circle, g.items);
      circle.addTo(map);
      numMarker.addTo(map);
    });
    return;
  }

  // 标注模式：同地点合并为一个点，多件带件数角标，弹窗列出该处全部文物
  const mgroup = new Map<string, { lat: number; lng: number; items: any[] }>();
  for (const r of relics.value) {
    const key = `${Math.round(r.geo_lat * 10) / 10},${Math.round(r.geo_lng * 10) / 10}`;
    if (!mgroup.has(key)) mgroup.set(key, { lat: r.geo_lat, lng: r.geo_lng, items: [] });
    mgroup.get(key)!.items.push(r);
  }
  mgroup.forEach((g) => {
    const count = buildSelectedItems(g.items).length;
    const icon = L.divIcon({
      html: `<span class="relic-dot">${count > 1 ? `<em class="dot-cnt">${count}</em>` : ""}</span>`,
      className: "relic-marker",
      iconSize: [26, 26], iconAnchor: [13, 13],
    });
    const marker = L.marker([g.lat, g.lng], { icon });
    customLayers.push(marker);
    marker.bindTooltip(
      `<b>${count > 1 ? `${g.items[0].location} · ${count} 件` : g.items[0].name}</b><br>${g.items[0].dynasty} · ${g.items[0].location}`,
      { direction: "top", offset: [0, -12], opacity: 1 }
    );
    marker.bindPopup(popupFor(g.items), { maxWidth: 360 });
    bindPopupEvents(marker, g.items);
    marker.addTo(map);
  });
}

/* 古代舆图：真实宋代石刻《禹迹图》拓本高清图（计里画方、覆盖全境，公共领域文物图），叠加到 Leaflet */
const ANCIENT_MAP_URL = "/images/map/yuji_map.jpg";
function buildAncientImage() {
  return ANCIENT_MAP_URL;
}

function toggleAncient() {
  ancient.value = !ancient.value;
  if (!map || !tileLayer) return;
  if (ancient.value) {
    if (!ancientLayer) {
      ancientLayer = L.imageOverlay(buildAncientImage(), [[15, 70], [55, 140]], { opacity: 0.95, interactive: false });
    }
    ancientLayer.addTo(map);
    tileLayer.setOpacity(0.18);
  } else {
    if (ancientLayer) map.removeLayer(ancientLayer);
    tileLayer.setOpacity(1);
  }
}

async function loadStats() {
  const stats: any = await fetchGeoStats();
  await nextTick();
  if (dynastyChart.value && locChart.value) {
    charts.forEach((c) => c.dispose());
    charts = [];
    const c1 = echarts.init(dynastyChart.value);
    charts.push(c1);
    c1.setOption({
      grid: { left: 34, right: 12, top: 8, bottom: 24 },
      xAxis: { type: "category", data: stats.by_dynasty.map((x: any) => x.name), axisLabel: { fontSize: 11 } },
      yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: "#eee5d2" } } },
      series: [{ type: "bar", data: stats.by_dynasty.map((x: any) => x.value),
        itemStyle: { color: "#7e2418", borderRadius: [4, 4, 0, 0] } }],
      tooltip: { trigger: "axis" },
    });
    const c2 = echarts.init(locChart.value);
    charts.push(c2);
    c2.setOption({
      grid: { left: 44, right: 16, top: 8, bottom: 24 },
      yAxis: { type: "category", inverse: true, data: stats.by_location.map((x: any) => x.name).slice(0, 10), axisLabel: { fontSize: 11 } },
      xAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: "#eee5d2" } } },
      series: [{ type: "bar", data: stats.by_location.map((x: any) => x.value).slice(0, 10),
        itemStyle: { color: "#b98a2f", borderRadius: [0, 4, 4, 0] } }],
      tooltip: { trigger: "axis" },
    });
  }
}

onMounted(async () => {
  await loadRelics();
  loadStats();
  // 支持 /geomap?relic=ID：从时间轴/其他页面跳入时自动定位并选中该文物
  const rid = Number(route.query.relic);
  if (rid && map) {
    const found = relics.value.find((r) => Number(r.id) === rid);
    if (found) {
      selectedItems.value = [found];
      map.flyTo([found.geo_lat, found.geo_lng], Math.max(map.getZoom(), 6), { duration: 0.8 });
    }
  }
});
onBeforeUnmount(() => {
  map?.remove();
  charts.forEach((c) => c.dispose());
});
</script>

<style scoped>
.page-sub { color: var(--ys-ink-3); margin: -6px 0 18px; }
.map-layout { display: grid; grid-template-columns: 1fr 320px; gap: 16px; align-items: start; }
.map-wrap { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.map-card { min-height: 500px; }
.map-head { display: flex; justify-content: space-between; margin-bottom: 10px; }
.map-canvas { height: 440px; border-radius: 8px; background: #eef2e9; z-index: 0; }
.map-note { font-size: 12px; color: var(--ys-ink-3); margin: 8px 0 0; }
.map-side { display: flex; flex-direction: column; gap: 14px; }
.relic-below .cnt { font-size: 12px; color: var(--ys-red-deep); margin-left: 6px; }
.relic-below .rel-list { display: flex; flex-direction: column; }
.relic-below .rel-list .rel-row + .rel-row { border-top: 1px dashed var(--ys-line); padding-top: 12px; margin-top: 12px; }
.relic-below .rel-row { display: flex; gap: 14px; }
.relic-below h4 { margin: 0 0 4px; font-size: 15px; }
.relic-below p { margin: 2px 0; color: var(--ys-ink-2); font-size: 13px; }
.relic-below .museum { color: var(--ys-red-deep); }
.rel-img-box { border-radius: 8px; overflow: hidden; border: 1px solid var(--ys-line); flex-shrink: 0; width: 200px; }
.rel-img { width: 200px; height: 140px; object-fit: cover; display: block; }
.rel-img-empty { display: flex; align-items: center; justify-content: center; width: 200px; height: 90px; color: #8a7a60; font-size: 13px; background: #f6efe4; }
.rel-info { flex: 1; min-width: 0; }
.relic-below .desc { color: var(--ys-ink-3); font-size: 12px; line-height: 1.6; }
.rel-costumes { margin-top: 8px; }
.c-tag { cursor: pointer; margin-right: 6px; }
.go-archive { margin-top: 6px; padding: 0; }
@media (max-width: 900px) {
  .map-layout { grid-template-columns: 1fr; }
}
</style>

<style>
/* Leaflet 动态标注点（非 scoped，作用于 map 生成的 DOM） */
.heat-pop .heat-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; cursor: pointer; padding: 3px 4px; border-radius: 4px; color: #7e2418; font-size: 13px; }
.heat-pop .heat-item:hover { background: #f4ead6; }
.heat-pop .heat-go { color: var(--ys-red-deep, #a93226); text-decoration: none; font-size: 12px; white-space: nowrap; }
.heat-pop .heat-go:hover { text-decoration: underline; }
.heat-num { background: transparent; border: none; }
.heat-num span {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: #a93226; color: #fff; font-size: 12px; font-weight: 600;
  border: 2px solid #fff; box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4);
}
.relic-marker { background: transparent; border: none; cursor: pointer; }
.relic-dot {
  display: inline-block; width: 22px; height: 22px; border-radius: 50%;
  background: #a93226; border: 2px solid #fff;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.35);
  transition: transform 0.15s ease;
}
.relic-dot .dot-cnt {
  position: absolute; top: -6px; right: -8px;
  min-width: 16px; height: 16px; line-height: 16px; border-radius: 8px;
  background: #7e2418; color: #fff; font-size: 10px; font-weight: 600;
  font-style: normal; text-align: center; padding: 0 3px;
  border: 1.5px solid #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}
.relic-dot { position: relative; }
.relic-marker:hover .relic-dot { transform: scale(1.45); box-shadow: 0 0 0 6px rgba(169, 50, 38, 0.18); }
.relic-dot .dot-seq {
  position: absolute; top: -7px; right: -9px;
  min-width: 16px; height: 16px; line-height: 16px; border-radius: 8px;
  background: #b98a2f; color: #fff; font-size: 10px; font-weight: 600;
  font-style: normal; text-align: center; padding: 0 3px;
  border: 1.5px solid #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}
.heat-pop .hp-sub { color: var(--ys-ink-2, #5a544a); font-size: 12px; }
.heat-pop b { font-size: 14px; color: #4a2c17; }
.heat-pop .hi-name { flex: 1; }
.heat-pop .heat-row + .heat-row { border-top: 1px dashed var(--ys-line, #e8e0d5); margin-top: 6px; padding-top: 6px; }
.leaflet-tooltip.relic-tip { font-size: 13px; }
</style>
