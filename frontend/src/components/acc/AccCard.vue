<template>
  <component
    :is="to ? 'router-link' : 'div'"
    class="acc-card"
    :to="to"
    :role="to ? undefined : 'link'"
    :tabindex="to ? undefined : 0"
    :style="{ '--i': index ?? 0 }"
    @click="onActivate"
    @keydown.enter="onActivate"
  >
    <div class="acc-visual" :style="{ '--tone': tone }">
      <span v-if="no" class="acc-no">{{ no }}</span>
      <span v-if="volume" class="acc-volume">{{ volume }}</span>
      <img
        v-if="image && !broken"
        class="acc-photo"
        :src="image"
        :alt="alt || title"
        loading="lazy"
        @error="broken = true"
      />
      <span v-else class="acc-seal">{{ title.slice(0, 1) }}</span>
      <span v-if="badge" class="acc-badge">{{ badge }}</span>
    </div>

    <div class="acc-body">
      <div class="acc-title-row">
        <h3 class="acc-title" :class="{ 'is-long': title.length > 4 }">{{ title }}</h3>
        <span v-if="code" class="acc-code">{{ code }}</span>
        <slot name="actions" />
      </div>

      <div v-if="meta" class="acc-meta">{{ meta }}</div>
      <p v-if="summary" class="acc-summary">{{ summary }}</p>

      <div v-if="shownTags.length || rest" class="acc-tags">
        <span v-for="t in shownTags" :key="t" class="acc-tag">{{ t }}</span>
        <span v-if="rest" class="acc-tag is-more">+{{ rest }}</span>
      </div>

      <div class="acc-link">
        <span>{{ linkText }}</span>
        <i>→</i>
      </div>
    </div>
  </component>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    to?: string;
    title: string;
    image?: string | null;
    alt?: string;
    meta?: string;
    summary?: string;
    tags?: string[];
    no?: string;
    volume?: string;
    code?: string;
    badge?: string;
    tone?: string;
    index?: number;
    linkText?: string;
    maxTags?: number;
  }>(),
  { image: null, tags: () => [], tone: "#a8672f", linkText: "阅档案", maxTags: 3 }
);

/* 不给 to 时卡片由父级接管点击（面料页要先播分裂动画） */
const emit = defineEmits<{ (e: "open"): void }>();
function onActivate() {
  if (!props.to) emit("open");
}

const broken = ref(false);
watch(() => props.image, () => (broken.value = false));

const shownTags = computed(() => props.tags.slice(0, props.maxTags));
const rest = computed(() => Math.max(0, props.tags.length - props.maxTags));
</script>
