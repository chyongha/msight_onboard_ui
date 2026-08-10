<script setup>
import { computed } from 'vue'
import { compassLabel, metersPerSecondToMph } from '../../utils/alertVisuals.js'

const props = defineProps({
  subject: { type: Object, default: null }, // { kind, source_id, speed_mps, heading_deg, flags[] }
  accentVar: { type: String, default: '--color-cat-vehicle' }, // CSS var name - flag chips (the "why" of the alert) use this to stand out from the neutral speed/heading chips
})

const mph = computed(() => metersPerSecondToMph(props.subject?.speed_mps))
const heading = computed(() => compassLabel(props.subject?.heading_deg))
</script>

<template>
  <div v-if="subject" class="alert-subject" :style="{ '--accent': `var(${accentVar})` }">
    <span v-if="mph !== null" class="chip">{{ mph }} mph</span>
    <span v-if="heading" class="chip">heading {{ heading }}</span>
    <!-- flags are *why* this vehicle triggered the alert (ABS/traction/
         stability engaged, etc.) - accented to stand out from the plain
         descriptive speed/heading chips above -->
    <span v-for="flag in subject.flags" :key="flag" class="chip chip-flag">{{ flag }}</span>
  </div>
</template>

<style scoped>
.alert-subject {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.chip {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
.chip-flag {
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, var(--color-surface-2));
  border-color: var(--accent);
  font-weight: 700;
}
</style>
