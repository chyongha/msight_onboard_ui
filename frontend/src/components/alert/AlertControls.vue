<script setup>
defineProps({
  viewMode: String, // 'both' | 'map' | 'alerts'
  showGpsBox: Boolean,
  soundEnabled: Boolean,
  soundBlockedMessage: String,
})
defineEmits(['set-view-mode', 'toggle-gps-box', 'toggle-sound'])
</script>

<template>
  <div class="controls">
    <!-- segmented, not a single cycling button - jump straight to the
         mode you want instead of clicking through the other two first.
         Also the only control for SDSM's visibility (no separate toggle):
         Map/Both show it, Alerts-only doesn't render the map at all. -->
    <div class="segmented">
      <button type="button" class="control-btn segment" :class="{ active: viewMode === 'both' }" @click="$emit('set-view-mode', 'both')">Both</button>
      <button type="button" class="control-btn segment" :class="{ active: viewMode === 'map' }" @click="$emit('set-view-mode', 'map')">Map</button>
      <button type="button" class="control-btn segment" :class="{ active: viewMode === 'alerts' }" @click="$emit('set-view-mode', 'alerts')">Alerts</button>
    </div>
    <button type="button" class="control-btn" :class="{ active: showGpsBox }" @click="$emit('toggle-gps-box')">
      {{ showGpsBox ? 'Hide GPS box' : 'Show GPS box' }}
    </button>
    <button type="button" class="control-btn" :class="{ active: soundEnabled }" @click="$emit('toggle-sound')">
      {{ soundEnabled ? 'Disable voice alarm' : 'Enable voice alarm' }}
    </button>
    <div v-if="soundBlockedMessage" class="sound-blocked">{{ soundBlockedMessage }}</div>
  </div>
</template>

<style scoped>
.controls {
  position: fixed;
  bottom: var(--space-3);
  left: var(--space-3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-2);
  font-family: var(--font-sans);
}
.segmented {
  display: flex;
  gap: 4px;
}
.control-btn {
  padding: 7px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  background: var(--color-surface);
  color: var(--color-text-muted);
  transition: border-color 0.15s ease, color 0.15s ease;
}
.control-btn:hover {
  color: var(--color-text);
  border-color: var(--color-text-faint);
}
.control-btn.active {
  color: var(--color-info);
  border-color: var(--color-info);
}
.sound-blocked {
  padding: 4px 10px;
  background: var(--color-surface);
  border: 1px solid var(--color-critical);
  color: var(--color-critical);
  border-radius: var(--radius-sm);
  font-size: 11px;
}
</style>
