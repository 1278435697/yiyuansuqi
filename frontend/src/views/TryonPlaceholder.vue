<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import data from '../data/exhibits.json';

const route = useRoute();
const router = useRouter();

const garment = computed(() => String(route.query.garment || ''));
const matched = computed(() => data.exhibits.find((e) => e.tryonId === garment.value) || null);
</script>

<template>
  <div class="tryon">
    <div class="panel">
      <div class="tag">虚拟试穿模块 · 占位页</div>
      <h1>虚拟试穿</h1>

      <div v-if="matched" class="info">
        <img :src="matched.images[0].src" :alt="matched.name" />
        <div class="meta">
          <div class="d">{{ matched.dynasty }}</div>
          <div class="n">{{ matched.name }}</div>
          <p>
            已从博物馆展厅跳转而来，携带展品参数
            <code>garment={{ garment }}</code>。
            正式接入 2D/3D 试穿模块后，此处将渲染该服饰的上身效果。
          </p>
        </div>
      </div>

      <div v-else class="empty">
        <p>未携带展品参数。请从<a @click="router.push('/museum')">博物馆展厅</a>点击展品后选择「试穿此服饰」。</p>
      </div>

      <div class="actions">
        <button @click="router.push('/museum')">返回博物馆展厅</button>
      </div>

      <div class="note">
        说明：本项目博物馆模块与虚拟试穿模块相互独立，此处为联动链路演示占位，不影响既有 RAG 与试穿代码。
      </div>
    </div>
  </div>
</template>

<style scoped>
.tryon {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(circle at 50% 40%, #221913, #0c0a09 70%);
}

.panel {
  width: min(680px, 94vw);
  padding: 28px 30px;
  background: linear-gradient(180deg, #241a14, #1b120e);
  border: 1px solid rgba(var(--silk-gold-rgb), 0.4);
  border-radius: 8px;
}

.tag {
  display: inline-block;
  padding: 3px 10px;
  margin-bottom: 12px;
  font-size: 12px;
  letter-spacing: 1px;
  color: #f7edd9;
  background: var(--ink-red);
  border-radius: 3px;
}

h1 {
  margin: 0 0 18px;
  font-size: 24px;
  letter-spacing: 4px;
  color: var(--silk-gold-soft);
}

.info {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.info img {
  width: 180px;
  height: 200px;
  object-fit: contain;
  background: #0f0c0a;
  border: 1px solid rgba(var(--silk-gold-rgb), 0.28);
  border-radius: 6px;
}

.d {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  color: #f7edd9;
  background: var(--ink-red);
  border-radius: 3px;
}

.n {
  margin: 8px 0 10px;
  font-size: 20px;
  letter-spacing: 2px;
  color: var(--silk-gold-soft);
}

.info p,
.empty p {
  margin: 0;
  font-size: 13px;
  line-height: 1.9;
  color: #c3b79f;
  text-align: justify;
}

code {
  padding: 1px 6px;
  font-size: 12px;
  color: var(--silk-gold-soft);
  background: rgba(var(--silk-gold-rgb), 0.12);
  border-radius: 3px;
}

.actions {
  margin-top: 22px;
}

.actions button {
  padding: 10px 20px;
  font-size: 13px;
  letter-spacing: 1px;
  color: #1a1310;
  background: linear-gradient(180deg, var(--silk-gold-soft), var(--silk-gold));
  border: 1px solid var(--silk-gold);
  border-radius: 4px;
}

.note {
  margin-top: 18px;
  padding-top: 14px;
  font-size: 11.5px;
  line-height: 1.8;
  color: #857a68;
  border-top: 1px dashed rgba(var(--silk-gold-rgb), 0.22);
}
</style>
