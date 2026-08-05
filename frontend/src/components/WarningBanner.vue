<script setup>
import { toRef } from 'vue'
import { useVoiceAlarm } from '../composables/useVoiceAlarm.js'

// props: data passed IN from a parent component (App.vue, in this case).
// This component doesn't know or care where the data comes from — it
// just displays whatever it's given.
const props = defineProps({
  isWarning: Boolean,
  warningText: String,
  connected: Boolean,
})

// The alarm needs to react to isWarning turning on/off, so it's owned
// here rather than in App.vue — this is the only component that already
// has that signal.
const { soundEnabled, soundBlockedMessage, toggleSound } = useVoiceAlarm(toRef(props, 'isWarning'))
</script>

<template>
  <div class="overlay">
    <div v-if="!connected" class="status">Connecting to backend...</div>
    <div v-else-if="isWarning" class="banner">
      <span class="icon">⚠</span>
      <span class="message">{{ warningText }}</span>
    </div>
  </div>

  <div class="sound-control">
    <button type="button" @click="toggleSound">
      {{ soundEnabled ? 'Disable voice alarm' : 'Enable voice alarm' }}
    </button>
    <div v-if="soundBlockedMessage" class="sound-blocked">{{ soundBlockedMessage }}</div>
  </div>
</template>

<style scoped>
/* Sits on top of MapView.vue's full-screen map (see App.vue) rather than
   covering it — same "strip across the top, map visible underneath"
   layout as msight_original_script/realtime_plot.py's #alert-overlay. */
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  font-family: sans-serif;
  pointer-events: none;
}
.status {
  margin: 10px;
  padding: 6px 12px;
  display: inline-block;
  background: rgba(0, 0, 0, 0.75);
  color: #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
}
.banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  background: rgba(190, 0, 0, 0.92);
  color: #fff;
  font-weight: 700;
  font-size: 1.3rem;
  text-align: center;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
  animation: pulse 0.8s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { background: rgba(190, 0, 0, 0.92); }
  50% { background: rgba(245, 35, 35, 0.95); }
}
.icon {
  font-size: 1.6rem;
}

/* Positioned bottom-left: clear of Leaflet's default top-left zoom
   control and its bottom-right attribution text. */
.sound-control {
  position: fixed;
  bottom: 10px;
  left: 10px;
  z-index: 1000;
  font-family: sans-serif;
}
.sound-control button {
  padding: 6px 10px;
  border: 1px solid #666;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.9);
}
.sound-blocked {
  margin-top: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.75);
  color: #ff8080;
  border-radius: 4px;
  font-size: 11px;
}
</style>
