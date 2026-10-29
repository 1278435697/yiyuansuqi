<template>
  <div class="acc-sec-head">
    <span class="acc-sec-no">{{ no }}</span>
    <div class="acc-sec-title-wrap">
      <h3 class="acc-sec-title">{{ title }}</h3>
      <span v-if="sub" class="acc-sec-sub">{{ sub }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ no: string; title: string; sub?: string }>();
</script>
