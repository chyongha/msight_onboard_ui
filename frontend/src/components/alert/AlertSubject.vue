<script setup>
import { computed } from 'vue'
import { subjectDetailChips } from '../../utils/alertVisuals.js'

// show whater isn't said 
const props = defineProps({
  subject: { type: Object, default: null }, // { kind, source_id, flags[], gear, steering_deg, accel_mps2, length_m, width_m, ... } 
  extent: { type: String, default: null },  // RSA only - how far past the hazard this stays relevant
  accentVar: { type: String, default: '--color-cat-vehicle' }, 
})

const detailChips = computed(() => subjectDetailChips(props.subject, props.extent))
const flags = computed(() => props.subject?.flags || [])
</script>

<template>
  <div v-if="detailChips.length || flags.length" class="alert-subject" :style="{ '--accent': `var(${accentVar})` }">
    <span v-for="chip in detailChips" :key="chip" class="chip">{{ chip }}</span>
    <!-- flags are why this vehicle triggered the alert (ABS/traction/
         stability engaged, spinning, sliding, etc.) - accented to stand out
         from the plain descriptive chips above -->
    <span v-for="flag in flags" :key="flag" class="chip chip-flag">{{ flag }}</span>
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
