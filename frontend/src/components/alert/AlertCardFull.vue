<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import AlertHeader from './AlertHeader.vue'
import AlertSubject from './AlertSubject.vue'
import DirectionIndicator from './DirectionIndicator.vue'
import HeadingSlicesRing from './HeadingSlicesRing.vue'
import { categoryMeta, subjectDetailChips } from '../../utils/alertVisuals.js'
import { CLEAR_AFTER_MS } from '../../composables/useSocket.js'

// Every active alert renders through this one component
const props = defineProps({
  alert: { type: Object, required: true },
})

const meta = computed(() => categoryMeta(props.alert.category))

// ICA alert subject - pedestrian or vehicle 
// RSA alert subject - extent (other info got moved)
const subjectLabel = computed(() => {
  if (props.alert.type === 'RSA') return 'Extent'
  return props.alert.category === 'pedestrian' ? 'Pedestrian' : 'Vehicle'
})

// Can end up showing nothing 
const hasSubjectDetails = computed(() => {
  const chips = subjectDetailChips(props.alert.subject, props.alert.extent)
  return chips.length > 0 || (props.alert.subject?.flags?.length ?? 0) > 0
})

// same value the useSocket.js clear timer uses
const clearAfterMs = `${CLEAR_AFTER_MS}ms`

// Measure actual overflow so a fade + label can flag it explicitly instead.
const eventsListEl = ref(null)
const hasMoreEvents = ref(false)
function checkEventsOverflow() {
  const el = eventsListEl.value
  hasMoreEvents.value = !!el && el.scrollHeight > el.clientHeight + 1
}
watch(
  () => [props.alert.headline, props.alert.events],
  async () => {
    await nextTick()
    checkEventsOverflow()
  },
  { immediate: true, deep: true }
)
</script>

<template>
  <div class="card" :style="{ '--accent': `var(${meta.colorVar})` }">
    <div class="countdown-track"><div class="countdown-bar" :key="alert.timestamp" /></div>

    <AlertHeader :type="alert.type" :category="alert.category" :timestamp="alert.timestamp" :occurred-at="alert.occurredAt" />

    <div v-if="alert.headline || alert.events?.length" class="section">
      <span class="section-label">Event</span>
      <div class="events-wrap">
        <ul ref="eventsListEl" class="events">
          <li v-if="alert.headline" class="headline-item">{{ alert.headline }}</li>
          <li v-for="(event, i) in alert.events" :key="i">{{ event }}</li>
        </ul>
        <!-- only shown when the list is actually scroll-capped (see
             checkEventsOverflow) - a scrollbar alone is too easy to miss -->
        <div v-if="hasMoreEvents" class="events-fade">
          <span class="more-hint">more below</span>
        </div>
      </div>
    </div>

    <div v-if="hasSubjectDetails" class="section">
      <span class="section-label">{{ subjectLabel }}</span>
      <AlertSubject :subject="alert.subject" :extent="alert.extent" :accent-var="meta.colorVar" />
    </div>

    <!-- RSA with a HeadingSlice bitmask gets both panels side by side -
         kept as two visually/textually distinct facts (arrow = one
         object's motion, ring = which directions this alert applies to)
         rather than merged, so they don't blur into looking like the same
         thing. Everything else (ICA, or RSA without this field) keeps the
         single full-width arrow panel as before. -->
    <div v-if="alert.subject && alert.directionSlices?.length" class="direction-row">
      <DirectionIndicator :subject="alert.subject" :accent-var="meta.colorVar" :timestamp="alert.timestamp" />
      <HeadingSlicesRing :slices="alert.directionSlices" :accent-var="meta.colorVar" :timestamp="alert.timestamp" />
    </div>
    <DirectionIndicator
      v-else-if="alert.subject"
      :subject="alert.subject"
      :accent-var="meta.colorVar"
      :timestamp="alert.timestamp"
    />
  </div>
</template>

<style scoped>
.card {
  width: min(420px, 100%);
  pointer-events: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--accent);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  box-shadow: var(--shadow-card);
}

/* thin bar counting down the ~5s an alert has left on screen, so it
   disappears as an expected event instead of an abrupt cut */
.countdown-track {
  height: 3px;
  border-radius: 2px;
  background: var(--color-surface-2);
  overflow: hidden;
}
.countdown-bar {
  height: 100%;
  width: 100%;
  background: var(--accent);
  transform-origin: left;
  animation: countdown-shrink v-bind(clearAfterMs) linear forwards;
}
@keyframes countdown-shrink {
  from { transform: scaleX(1); }
  to { transform: scaleX(0); }
}

.section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.section-label {
  color: var(--color-text-faint);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.events-wrap {
  position: relative;
}
.events {
  margin: 0;
  padding-left: 1.1em;
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: var(--color-text);
  font-size: 1rem;
  font-weight: 500;
  line-height: 1.35;
  max-height: 7.4em;
  overflow-y: auto;
}
.events li::marker {
  color: var(--accent);
}
.events-fade {
  position: absolute;
  left: 0;
  right: 8px; /* clear the scrollbar gutter */
  bottom: 0;
  height: 26px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 2px;
  background: linear-gradient(to bottom, transparent, var(--color-surface) 75%);
  pointer-events: none;
}
.more-hint {
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-faint);
}
.headline-item {
  font-weight: 700;
  font-size: 1.05rem;
}

.direction-row {
  display: flex;
  gap: var(--space-2);
  align-items: stretch;
}
.direction-row > :deep(*) {
  flex: 1 1 0;
  min-width: 0;
}
</style>
