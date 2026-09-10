<script setup>
import { computed, ref, toRef, watch } from 'vue'
import { useVoiceAlarm } from '../../composables/useVoiceAlarm.js'
import AlertCardFull from './AlertCardFull.vue'
import AlertControls from './AlertControls.vue'

const props = defineProps({
  alerts: { type: Array, default: () => [] }, // newest/top of stack first
  connected: Boolean,
  viewMode: { type: String, default: 'both' }, // 'both' | 'map' | 'alerts'
  showGpsBox: Boolean,
})
defineEmits(['set-view-mode', 'toggle-gps-box'])

const hasActiveAlerts = computed(() => props.alerts.length > 0)
const { soundEnabled, soundBlockedMessage, toggleSound } = useVoiceAlarm(toRef(hasActiveAlerts))

// every alert renders in full (see AlertCardFull.vue) so a burst of
// simultaneous alerts can outgrow the viewport - .stack scrolls internally
// in that case (see CSS below); when a new one arrives, snap back to the
// top so it's never missed by someone scrolled down reading an older card
const stackEl = ref(null)
watch(
  () => props.alerts.length,
  (next, prev) => {
    if (next <= prev) return
    // TransitionGroup forwards `ref` to its component instance (`.$el`) in
    // some Vue builds and straight to the rendered DOM node in others -
    // covering both rather than assuming one
    const el = stackEl.value?.$el ?? stackEl.value
    el?.scrollTo?.({ top: 0, behavior: 'smooth' })
  }
)
</script>

<template>
  <!-- always top-anchored, whether or not the map is showing - multiple
       alerts stack downward from here, newest on top, all shown in full.
       Hidden entirely in 'map' mode - not even the connecting-status text,
       since that's alert-system chrome too. -->
  <div v-if="viewMode !== 'map'" class="overlay">
    <div v-if="!connected" class="status">Connecting to backend...</div>

    <TransitionGroup v-else ref="stackEl" tag="div" name="stack" class="stack">
      <AlertCardFull v-for="alert in alerts" :key="alert.id" :alert="alert" />
    </TransitionGroup>

    <div v-if="connected && !hasActiveAlerts && viewMode === 'alerts'" class="idle">No warning</div>
  </div>

  <!-- AlertControls always renders regardless of viewMode - it's the
       switcher, so it can never itself be mode-hidden or there'd be no way back -->
  <AlertControls
    :view-mode="viewMode"
    :show-gps-box="showGpsBox"
    :sound-enabled="soundEnabled"
    :sound-blocked-message="soundBlockedMessage"
    @set-view-mode="$emit('set-view-mode', $event)"
    @toggle-gps-box="$emit('toggle-gps-box')"
    @toggle-sound="toggleSound"
  />
</template>

<style scoped>
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  font-family: var(--font-sans);
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-4);
}

.status {
  margin-top: var(--space-2);
  padding: 6px 14px;
  background: var(--color-surface);
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  border: 1px solid var(--color-border);
}

.idle {
  margin-top: var(--space-2);
  padding: 6px 14px;
  color: var(--color-text-faint);
  font-size: 0.9rem;
}

.stack {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  pointer-events: auto; 
  max-height: calc(100vh - var(--space-4) * 2 - 100px);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}

/* existing cards slide smoothly into the gap a removed/expired one leaves */
.stack-move {
  transition: transform 0.3s ease;
}
.stack-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
  animation: card-arrive 0.45s ease-out;
}
.stack-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
  position: absolute; /* drop out of flow while fading so siblings can animate into its spot via .stack-move */
}
.stack-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.stack-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

@keyframes card-arrive {
  0% {
    box-shadow: var(--shadow-card), 0 0 0 0 color-mix(in srgb, var(--accent) 45%, transparent);
  }
  100% {
    box-shadow: var(--shadow-card), 0 0 0 10px transparent;
  }
}

@media (prefers-reduced-motion: reduce) {
  /* keep the slide/fade transition (it's a brief list-reorder cue, not a
     bounce/pulse effect) - only drop the decorative accent-ring pulse */
  .stack-enter-active { animation: none; }
}
</style>
