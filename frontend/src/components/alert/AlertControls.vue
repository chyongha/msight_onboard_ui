<script setup>
defineProps({
  showMap: Boolean,
  soundEnabled: Boolean,
  soundBlockedMessage: String,
})
defineEmits(['toggle-map', 'toggle-sound'])
</script>

<template>
  <div class="controls">
    <button type="button" class="control-btn" @click="$emit('toggle-map')">
      {{ showMap ? 'Hide map (field test)' : 'Show map' }}
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
