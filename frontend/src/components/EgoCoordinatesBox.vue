<script setup>
import { computed } from 'vue'
import { formatEventTime } from '../utils/alertVisuals.js'

const props = defineProps({
  egoPosition: { type: Object, default: null }, // { lat, lon, timestamp } or null before the first fix arrives
})

const hasFix = computed(() => typeof props.egoPosition?.lat === 'number' && typeof props.egoPosition?.lon === 'number')

const timeText = computed(() => formatEventTime(props.egoPosition?.timestamp) ?? '---')
// fixed precision so the box doesn't jitter in width as digits change length
const lonText = computed(() => (hasFix.value ? props.egoPosition.lon.toFixed(6) : '---'))
const latText = computed(() => (hasFix.value ? props.egoPosition.lat.toFixed(6) : '---'))
</script>

<template>
  <div class="ego-box">
    <span class="title">GPS position</span>
    <div v-if="hasFix" class="rows">
      <div class="row"><span class="row-label">time</span><span class="row-value">{{ timeText }}</span></div>
      <div class="row"><span class="row-label">long</span><span class="row-value">{{ lonText }}</span></div>
      <div class="row"><span class="row-label">lat</span><span class="row-value">{{ latText }}</span></div>
    </div>
    <span v-else class="muted">No GPS signal yet</span>
  </div>
</template>

<style scoped>
.ego-box {
  position: absolute;
  top: var(--space-3);
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
  pointer-events: none; /* purely informational - never blocks map interaction underneath */
}
.title {
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-faint);
}
.rows {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.row-label {
  width: 34px;
  flex-shrink: 0;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-text-faint);
}
.row-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}
.muted {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-faint);
}
</style>
