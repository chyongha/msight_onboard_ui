<script setup>
// Small "which way, how fast" indicator: a single arrow rotated to the
// responsible vehicle/pedestrian's real reported heading, plus the compass
// label + mph as text. Deliberately NOT a spatial replay panel any more -
// that version (rotating breadcrumbs into a schematic, not-to-scale,
// vehicle-relative frame, paced to real timing) tried to answer "where/which
// way/how fast" all at once in a tiny space and read as confusing rather
// than informative. One clear fact, one clear arrow.
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
    <template v-if="compass">
      <!-- keyed on timestamp: a re-broadcast of the same alert refreshes
           this value (useSocket.js), so remounting here replays the
           entrance animation instead of it only ever playing once -->
      <div :key="timestamp" class="arrow-wrap" :style="{ '--dot-color': `var(${accentVar})` }">
        <!-- points north (up) at 0deg, so rotating by the real compass
             heading (0=N, 90=E, clockwise) lands correctly - the previous
             glyph pointed east at 0deg, which was quietly 90deg off from
             what the adjacent compass label said -->
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
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
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
