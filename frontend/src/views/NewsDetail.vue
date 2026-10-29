<template>
  <div class="news-detail">
    <el-button text class="back-btn" @click="$router.back()">
      ← 返回
    </el-button>

    <div v-if="news" class="detail-card ys-card">
      <img v-if="news.cover_image" class="detail-cover" :src="news.cover_image" :alt="news.title" @error="hideImg($event)" />
      <div class="detail-body">
        <div class="detail-meta">
          <span class="ai-badge">AI摘要</span>
          <span>{{ news.source }}</span>
          <span class="date">{{ news.publish_time?.slice(0, 10) }}</span>
          <span v-if="news.code" class="date">编号 {{ news.code }}</span>
          <a v-if="news.source_url" class="src-link" :href="news.source_url" target="_blank" rel="noopener">查看原文 ↗</a>
        </div>
        <h1 class="detail-title">{{ news.title }}</h1>
        <div class="detail-tags">
          <span class="ys-tag" v-for="t in news.dynasty_tags" :key="t" @click="jumpArchive(t)">{{ t }}</span>
          <span class="ys-tag" v-for="t in news.entity_tags" :key="t" @click="jumpArchive(t)">{{ t }}</span>
        </div>

        <section class="detail-section">
          <h2 class="sec-title">AI 摘要</h2>
          <p class="ai-note">本摘要由 AI 自动生成，仅供参考，事实以原文与史料为准。</p>
          <p class="summary-text">{{ news.summary }}</p>
        </section>

        <section class="detail-section">
          <h2 class="sec-title">正文</h2>
          <div class="content-text">{{ news.content || news.summary }}</div>
        </section>

        <section class="detail-section" v-if="news.ai_questions?.length">
          <h2 class="sec-title">AI 推荐提问</h2>
          <div class="qa-list">
            <span v-for="q in news.ai_questions" :key="q" class="qa-item" @click="askAI(q)">{{ q }}</span>
          </div>
        </section>
      </div>
    </div>

    <div v-else-if="loaded" class="ys-empty">资讯不存在或已下线</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchNewsDetail } from "@/api/modules";

const route = useRoute();
const router = useRouter();
const news = ref<any>(null);
const loaded = ref(false);

async function load() {
  const data: any = await fetchNewsDetail(Number(route.params.id));
  loaded.value = true;
  if (data && !data.error) news.value = data;
}

function jumpArchive(tag: string) {
  router.push(`/archive?keyword=${encodeURIComponent(tag)}`);
}

function askAI(q: string) {
  ElMessage.info(`推荐提问：${q}`);
  router.push("/aiqa");
}

function hideImg(e: Event) {
  (e.target as HTMLImageElement).style.display = "none";
}

onMounted(load);
</script>

<style scoped>
.news-detail { max-width: 860px; margin: 0 auto; }
.back-btn { margin-bottom: 12px; color: var(--ys-red-deep); }
.detail-card { overflow: hidden; }
.detail-cover { width: 100%; max-height: 420px; object-fit: cover; display: block; }
.detail-body { padding: 20px 26px 28px; }
.detail-meta { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--ys-ink-3); }
.src-link { color: var(--ys-red-deep); text-decoration: none; font-size: 13px; white-space: nowrap; }
.src-link:hover { text-decoration: underline; }
.ai-badge { background: var(--ys-red); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.detail-title { margin: 12px 0 10px; font-size: 26px; line-height: 1.4; }
.detail-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.detail-section { margin-top: 22px; }
.sec-title { font-size: 17px; margin: 0 0 8px; padding-left: 10px; border-left: 3px solid var(--ys-red); }
.ai-note { font-size: 12px; color: var(--ys-ink-3); margin: 0 0 6px; }
.summary-text { font-size: 15px; color: var(--ys-ink-2); line-height: 1.9; margin: 0; }
.content-text { font-size: 15px; line-height: 2; color: var(--ys-ink-1); white-space: pre-line; }
.qa-list { display: flex; flex-direction: column; gap: 8px; }
.qa-item { color: var(--ys-red-deep); cursor: pointer; font-size: 14px; text-decoration: underline dotted; }
</style>
