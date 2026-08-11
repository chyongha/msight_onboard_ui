<script setup>
// "Which compass directions does this alert apply to" - a ring of 16
// wedges (one per ~22.5deg HeadingSlice), colored where the RSU flagged a
// slice, neutral elsewhere. Deliberately a DIFFERENT visual language than
// DirectionIndicator's single rotating arrow (a ring of possibly-several
// lit wedges, vs. one arrow pointing one way) so the two don't blur into
// looking like the same fact - this is "applies to traffic heading these
// ways", not "this vehicle is heading this way".
import { computed } from 'vue'

const props = defineProps({
  slices: { type: Array, default: null }, // [{index, label}, ...] - see alert_formatter.py's _rsa_heading_slices
  accentVar: { type: String, default: '--color-cat-vehicle' },
  timestamp: { type: Number, default: null }, // re-keys the ring so it replays on a refreshed alert, matching DirectionIndicator's pattern
})

const CENTER = 50
const OUTER_R = 42
const INNER_R = 27
const GAP_DEG = 2 // thin gap between wedges so they read as separate segments, not one solid ring

const activeIndexes = computed(() => new Set((props.slices || []).map((s) => s.index)))
// full sentence, not a bare list of compass letters - reads clearly even
// if someone only glances at this line and skips the title above it
const activeLabels = computed(() => `Vehicles heading ${(props.slices || []).map((s) => s.label).join(', ')}`)

// compass degrees (0=up/N, clockwise) -> SVG x/y at the given radius
function point(deg, radius) {
  const rad = (deg * Math.PI) / 180
  return [CENTER + radius * Math.sin(rad), CENTER - radius * Math.cos(rad)]
}

// one wedge's <path> d string - an annulus segment between innerR/outerR, from startDeg to endDeg
function wedgePath(startDeg, endDeg) {
  const [ox0, oy0] = point(startDeg, OUTER_R)
  const [ox1, oy1] = point(endDeg, OUTER_R)
  const [ix1, iy1] = point(endDeg, INNER_R)
  const [ix0, iy0] = point(startDeg, INNER_R)
  return `M ${ox0} ${oy0} A ${OUTER_R} ${OUTER_R} 0 0 1 ${ox1} ${oy1} L ${ix1} ${iy1} A ${INNER_R} ${INNER_R} 0 0 0 ${ix0} ${iy0} Z`
}

const wedges = computed(() => {
  const out = []
  for (let i = 0; i < 16; i++) {
    const start = i * 22.5 + GAP_DEG / 2
    const end = (i + 1) * 22.5 - GAP_DEG / 2
    out.push({ index: i, d: wedgePath(start, end), active: activeIndexes.value.has(i) })
  }
  return out
})
</script>

<template>
  <div v-if="slices && slices.length" class="ring-panel">
    <!-- short, plain-language explainer - this is a different fact than
         the direction arrow next to it (which way a vehicle is heading),
         so it needs its own framing to not read as the same thing -->
    <span class="panel-title">Applies to</span>

    <div :key="timestamp" class="ring-wrap" :style="{ '--dot-color': `var(${accentVar})` }">
      <svg width="72" height="72" viewBox="0 0 100 100" aria-hidden="true">
        <path
          v-for="wedge in wedges"
          :key="wedge.index"
          :d="wedge.d"
          :fill="wedge.active ? 'var(--dot-color, var(--color-cat-vehicle))' : 'var(--color-border)'"
        />
      </svg>
    </div>
    <span class="label">{{ activeLabels }}</span>
  </div>
</template>

<style scoped>
.ring-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* see DirectionIndicator.vue's matching comment - same fix, same reason:
     this panel sits next to it in a stretched flex row, so without this
     the ring ends up pinned to the top instead of centered */
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
.ring-wrap {
  display: flex;
  animation: ring-arrive 0.45s ease-out;
}
@keyframes ring-arrive {
  0% { opacity: 0; transform: scale(0.7) rotate(-20deg); }
  100% { opacity: 1; transform: scale(1) rotate(0deg); }
}
@media (prefers-reduced-motion: reduce) {
  .ring-wrap { animation: none; }
}
.label {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-align: center;
}
</style>
