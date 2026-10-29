<template>
  <div class="acc-section-head">
    <div v-if="no || kicker" class="acc-section-kicker">
      <b v-if="no">{{ no }}</b>
      <span>{{ kicker }}</span>
    </div>
    <h2 class="acc-section-title" :class="{ 'is-sm': size === 'sm' }">
      {{ title }}
      <em v-if="sub">{{ sub }}</em>
    </h2>
    <p v-if="desc" class="acc-section-sub">{{ desc }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  kicker?: string;
  no?: string;
  sub?: string;
  desc?: string;
  size?: "sm" | "md";
}>();
</script>
