<template>
  <div class="timegeo-page">
    <PageHero title="千年衣脉 · 时空双维图谱" kicker="TIMELINE & GEO · 时空溯源"
              sub="纵向沿时间轴纵览衣制千年演变，横向在地图上遍览全国服饰文物出土分布" seal="脉" />

    <div class="tg-tabs anim-stagger">
      <button class="tg-tab" :class="{ on: tab === 'time' }" @click="tab = 'time'">
        <b>千年衣脉时间轴</b><i>纵向 · 朝代演变</i>
      </button>
      <button class="tg-tab" :class="{ on: tab === 'geo' }" @click="tab = 'geo'">
        <b>服饰出土地图</b><i>横向 · 全国分布</i>
      </button>
    </div>

    <TimeLine v-if="tab === 'time'" />
    <GeoHeatMap v-if="tab === 'geo'" />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import PageHero from "@/components/PageHero.vue";
import TimeLine from "@/views/TimeLine.vue";
import GeoHeatMap from "@/views/GeoHeatMap.vue";

const route = useRoute();
const tab = ref(route.query.tab === "geo" ? "geo" : "time");
onMounted(() => {
  if (route.query.tab === "geo") tab.value = "geo";
});
</script>

<style scoped>
.timegeo-page { min-height: 100vh; }
.tg-tabs {
  display: flex; gap: 12px; padding: 0 6vw 18px; flex-wrap: wrap;
}
.tg-tab {
  flex: 1; min-width: 220px; max-width: 360px;
  display: flex; flex-direction: column; gap: 4px; align-items: flex-start;
  padding: 14px 18px; border-radius: 12px; cursor: pointer; text-align: left;
  background: #fffdf8; border: 1px solid var(--ys-line, #e5d9c3);
  transition: all .2s ease;
}
.tg-tab b { font-size: 15px; color: #5a2a20; letter-spacing: 1px; }
.tg-tab i { font-size: 12px; color: #9a8a72; font-style: normal; }
.tg-tab.on {
  background: linear-gradient(135deg, #7a221c, #8f3a2a);
  border-color: #7a221c;
  box-shadow: 0 6px 18px rgba(122,34,28,.25);
}
.tg-tab.on b { color: #f6e6c8; }
.tg-tab.on i { color: #d8b98a; }
</style>
