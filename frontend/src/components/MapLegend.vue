<script setup>
// No hardcoded colors here - takes whatever MapView.vue is actually
// drawing, so the legend can't silently drift out of sync with the map.
defineProps({
  items: { type: Array, default: () => [] }, // [{ color, label }]
})
</script>

<template>
  <div class="legend">
    <div v-for="item in items" :key="item.label" class="row">
      <span class="swatch" :style="{ background: item.color }"></span>
      <span class="label">{{ item.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.legend {
  position: absolute;
  bottom: var(--space-3);
  right: var(--space-3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  font-family: var(--font-sans);
  pointer-events: none;
}
.row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.15);
}
.label {
  font-size: 0.76rem;
  font-weight: 500;
  color: var(--color-text-muted);
}
</style>
