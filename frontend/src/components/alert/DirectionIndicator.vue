<script setup>
// which way + how fast indicator 
import { computed } from 'vue'
import { compassLabel, metersPerSecondToMph } from '../../utils/alertVisuals.js'

const props = defineProps({
  subject: { type: Object, default: null },     // { speed_mps, heading_deg, ... } or null
  accentVar: { type: String, default: '--color-cat-vehicle' }, // CSS var name for the arrow's color
  timestamp: { type: Number, default: null },    // re-keys the arrow so it replays on a refreshed alert, not just first arrival
})

const compass = computed(() => compassLabel(props.subject?.heading_deg))
const mph = computed(() => metersPerSecondToMph(props.subject?.speed_mps))
</script>

<template>
  <div class="direction-panel">
    <!-- short, plain-language explainer so this reads clearly the first
         time someone sees it, not just an arrow + jargon -->
    <span class="panel-title">Direction &amp; speed</span>

    <template v-if="compass">
      <div :key="timestamp" class="arrow-wrap" :style="{ '--dot-color': `var(${accentVar})` }">
        <svg width="28" height="28" viewBox="0 0 24 24" class="arrow" :style="{ transform: `rotate(${subject.heading_deg}deg)` }" aria-hidden="true">
          <path d="M12 2.5 L19 19 L12 15 L5 19 Z" fill="var(--dot-color, var(--color-cat-vehicle))" />
        </svg>
      </div>
      <span class="label">Traveling {{ compass }}<template v-if="mph !== null"> &bull; {{ mph }} mph</template></span>
    </template>

    <template v-else>
      <div class="label muted">No direction reported for this event</div>
    </template>
  </div>
</template>

<style scoped>
.direction-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* the arrow+label block was sitting flush against the top instead of
     centered whenever this panel got stretched taller than its own content
     - happens whenever it sits next to HeadingSlicesRing in AlertCardFull's
     side-by-side row (align-items: stretch there matches both panels to the
     taller one's height). justify-content here centers the content in
     whatever extra height the stretch adds, instead of leaving it pinned
     to flex-start (the default). */
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.panel-title {
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-faint);
}
.arrow-wrap {
  display: flex;
  animation: arrow-arrive 0.45s ease-out;
}
@keyframes arrow-arrive {
  0% { opacity: 0; transform: scale(0.6); }
  70% { opacity: 1; transform: scale(1.12); }
  100% { opacity: 1; transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .arrow-wrap { animation: none; }
}
.label {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  text-align: center;
}
.label.muted {
  color: var(--color-text-faint);
  font-size: 0.8rem;
}
</style>
