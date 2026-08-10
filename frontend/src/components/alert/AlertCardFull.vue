<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import AlertHeader from './AlertHeader.vue'
import AlertSubject from './AlertSubject.vue'
import DirectionIndicator from './DirectionIndicator.vue'
import { categoryMeta } from '../../utils/alertVisuals.js'
import { CLEAR_AFTER_MS } from '../../composables/useSocket.js'

// Every active alert renders through this one component
const props = defineProps({
  alert: { type: Object, required: true }, 
})

const meta = computed(() => categoryMeta(props.alert.category))

// vehicle / pedestrian 
const subjectLabel = computed(() => (props.alert.category === 'pedestrian' ? 'Pedestrian' : 'Vehicle'))

// same value the useSocket.js clear timer uses
const clearAfterMs = `${CLEAR_AFTER_MS}ms`

// Long condition lists get capped/scrolled (see .events CSS) rather than
// stretching the card - but a scrollbar alone is an easy-to-miss signal
// that content is hidden, especially on touch/kiosk displays where
// scrollbars often don't show until touched. Measure actual overflow so a
// fade + label can flag it explicitly instead.
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
    <!-- keyed on timestamp so a re-broadcast of the same alert (which
         restarts the clear timer in useSocket.js) restarts this too,
         instead of it silently jumping back to full without visual notice -->
    <div class="countdown-track"><div class="countdown-bar" :key="alert.timestamp" /></div>

    <AlertHeader :type="alert.type" :category="alert.category" :timestamp="alert.timestamp" />

    <div v-if="alert.headline || alert.events?.length" class="section">
      <span class="section-label">Event</span>
      <!-- one list for both message types: ICA's flag conditions ARE the
           primary info here, no headline. RSA's typeEvent (headline) leads
           as the emphasized first item, description codes follow as normal
           items - both are ITIS codes describing the same event, just at
           different levels of specificity, so they read as one list rather
           than two visually separate blocks -->
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

    <div v-if="alert.subject" class="section">
      <span class="section-label">{{ subjectLabel }}</span>
      <AlertSubject :subject="alert.subject" :accent-var="meta.colorVar" />
    </div>

    <DirectionIndicator
      v-if="alert.subject"
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
  /* cap so an alert with an unusually long condition list (ICA can have
     several flag bits set at once) scrolls internally instead of
     stretching the card - paired with .events-fade below since a
     scrollbar alone is easy to miss, especially on touch/kiosk displays */
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
/* RSA's typeEvent - the primary event, vs. the description items below it
   which merely elaborate on it (see AlertCardFull's template comment) */
.headline-item {
  font-weight: 700;
  font-size: 1.05rem;
}
</style>
