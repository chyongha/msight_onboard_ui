<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import AlertIcon from './AlertIcon.vue'
import { categoryMeta } from '../../utils/alertVisuals.js'

const props = defineProps({
  type: { type: String, default: null },       // ICA or RSA
  category: { type: String, default: null },    // vehicle or pedestrian or weather or road hazard or other 
  timestamp: { type: Number, default: null },   // epoch seconds from the backend
})

const meta = computed(() => categoryMeta(props.category))

// which one-shot entrance animation the icon badge plays - falls back to
// the generic fade for anything not in this known set, same "never render
// nothing/nothing recognizable" spirit as categoryMeta()'s own fallback
const KNOWN_ANIM_CATEGORIES = ['vehicle', 'pedestrian', 'weather', 'road_hazard']
const iconAnimClass = computed(() => `icon-arrive-${KNOWN_ANIM_CATEGORIES.includes(props.category) ? props.category : 'other'}`)

// ticking clock so "x s ago" stays live while the card is on screen
const now = ref(Date.now())
let clockTimer = null
onMounted(() => {
  clockTimer = setInterval(() => { now.value = Date.now() }, 1000)
})
onBeforeUnmount(() => {
  if (clockTimer) clearInterval(clockTimer)
})

const relativeTime = computed(() => {
  if (!props.timestamp) return null
  const deltaS = Math.max(0, Math.round(now.value / 1000 - props.timestamp))
  if (deltaS < 1) return 'just now'
  if (deltaS < 60) return `${deltaS}s ago`
  return `${Math.round(deltaS / 60)}m ago`
})
</script>

<template>
  <div class="alert-header">
    <!-- keyed on timestamp: a re-broadcast of the same alert (useSocket.js
         bumps it to top + refreshes this value) remounts the badge, so the
         entrance animation replays instead of only playing once ever -->
    <div :key="timestamp" class="icon-badge" :class="iconAnimClass" :style="{ color: `var(${meta.colorVar})`, background: `var(${meta.bgVar})` }">
      <AlertIcon :category="category" :size="24" />
    </div>
    <div class="titles">
      <span class="category">{{ meta.label }}</span>
      <span v-if="type" class="type-tag">{{ type }}</span>
    </div>
    <span v-if="relativeTime" class="time">{{ relativeTime }}</span>
  </div>
</template>

<style scoped>
.alert-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.icon-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  animation-duration: 0.45s;
  animation-timing-function: ease-out;
  animation-fill-mode: both;
}
/* one-shot entrance per category, all the same restrained ~0.45s family -
   varies only the direction/motion to hint at the category, not the whole
   effect, so five categories still read as one coherent idea */
.icon-arrive-vehicle { animation-name: icon-arrive-up; }
.icon-arrive-pedestrian { animation-name: icon-arrive-step; }
.icon-arrive-weather { animation-name: icon-arrive-down; }
.icon-arrive-road_hazard { animation-name: icon-arrive-wobble; }
.icon-arrive-other { animation-name: icon-arrive-fade; }

@keyframes icon-arrive-up {
  0% { opacity: 0; transform: translateY(8px) scale(0.85); }
  70% { opacity: 1; transform: translateY(-2px) scale(1.05); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes icon-arrive-step {
  0% { opacity: 0; transform: translateX(-8px) scale(0.85); }
  70% { opacity: 1; transform: translateX(2px) scale(1.05); }
  100% { opacity: 1; transform: translateX(0) scale(1); }
}
@keyframes icon-arrive-down {
  0% { opacity: 0; transform: translateY(-8px) scale(0.9); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes icon-arrive-wobble {
  0% { opacity: 0; transform: rotate(0deg) scale(0.85); }
  30% { opacity: 1; transform: rotate(-8deg) scale(1); }
  60% { transform: rotate(8deg) scale(1); }
  100% { transform: rotate(0deg) scale(1); }
}
@keyframes icon-arrive-fade {
  0% { opacity: 0; transform: scale(0.85); }
  100% { opacity: 1; transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .icon-badge { animation: none; }
}

.titles {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  min-width: 0;
}
.category {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.type-tag {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-surface-2);
  color: var(--color-text-faint);
  border: 1px solid var(--color-border);
}
.time {
  font-size: 0.78rem;
  color: var(--color-text-faint);
  flex-shrink: 0;
}
</style>
