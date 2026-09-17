<script setup>
import { computed } from 'vue'
import { formatEventTime } from '../utils/alertVisuals.js'

const props = defineProps({
  sdsmFrame: { type: Object, default: null }, // { source_id, equipment_type, lat, lon, timestamp, objects[] } or null
  categoryColor: { type: Object, default: () => ({}) }, // same palette MapView.vue draws the object markers with, so the dots below match
})

// capped so this box stays small and out of the way of the map's icon
// locations no matter how many objects a frame carries - a static "+N more"
// tail rather than a scrollable list, so it never needs pointer-events and
// can never grow to cover the map like an alert card would
const MAX_OBJECTS_SHOWN = 5

const hasFrame = computed(() => props.sdsmFrame !== null)
const timeText = computed(() => formatEventTime(props.sdsmFrame?.timestamp) ?? '---')
const sourceText = computed(() => props.sdsmFrame?.source_id || '---')
const equipmentText = computed(() => props.sdsmFrame?.equipment_type || '---')
const hasStationFix = computed(() => typeof props.sdsmFrame?.lat === 'number' && typeof props.sdsmFrame?.lon === 'number')
const latText = computed(() => (hasStationFix.value ? props.sdsmFrame.lat.toFixed(6) : '---'))
const lonText = computed(() => (hasStationFix.value ? props.sdsmFrame.lon.toFixed(6) : '---'))

const allObjects = computed(() => props.sdsmFrame?.objects || [])
const shownObjects = computed(() => allObjects.value.slice(0, MAX_OBJECTS_SHOWN))
const hiddenCount = computed(() => Math.max(allObjects.value.length - MAX_OBJECTS_SHOWN, 0))

function dotColor(category) {
  return props.categoryColor[category] || '#888888'
}
</script>

<template>
  <div class="sdsm-box">
    <span class="title">SDSM sensor</span>
    <div v-if="hasFrame" class="rows">
      <div class="row"><span class="row-label">time</span><span class="row-value">{{ timeText }}</span></div>
      <div class="row"><span class="row-label">source</span><span class="row-value">{{ sourceText }}</span></div>
      <div class="row"><span class="row-label">type</span><span class="row-value">{{ equipmentText }}</span></div>
      <div class="row"><span class="row-label">lat</span><span class="row-value">{{ latText }}</span></div>
      <div class="row"><span class="row-label">long</span><span class="row-value">{{ lonText }}</span></div>

      <div v-if="allObjects.length" class="objects">
        <div v-for="obj in shownObjects" :key="obj.id" class="object-row">
          <div class="object-row-main">
            <span class="dot" :style="{ background: dotColor(obj.category) }"></span>
            <span class="object-label">{{ obj.category }} #{{ obj.id }}</span>
          </div>
          <div class="object-row-sub">
            <span v-if="obj.size_m">{{ obj.size_m }} &bull; </span>{{ obj.speed.toFixed(1) }} m/s
          </div>
        </div>
        <div v-if="hiddenCount > 0" class="more">+{{ hiddenCount }} more</div>
      </div>
      <div v-else class="row"><span class="row-label">objects</span><span class="row-value">0</span></div>
    </div>
    <span v-else class="muted">No SDSM data yet</span>
  </div>
</template>

<style scoped>
.sdsm-box {
  position: absolute;
  top: var(--space-3);
  left: var(--space-3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 190px; /* fixed, narrow - stays small regardless of object count so it never blocks the map's icon locations */
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
  width: 46px;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.objects {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid var(--color-border);
}
.object-row {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.object-row-main {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.object-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text);
  font-weight: 600;
}
.object-row-sub {
  padding-left: 13px; /* aligns under object-label, past the dot */
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.66rem;
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.more {
  font-size: 0.68rem;
  color: var(--color-text-faint);
  font-style: italic;
}
.muted {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-faint);
}
</style>
