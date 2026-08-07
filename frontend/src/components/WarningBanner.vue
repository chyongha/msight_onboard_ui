<script setup>
import { toRef } from 'vue'
import { useVoiceAlarm } from '../composables/useVoiceAlarm.js'

const props = defineProps({
  isWarning: Boolean, // true - active alert present / false - no active alert 
  warningText: String, // text to display for the current alert
  connected: Boolean,  // true - socketio connection is on / false - its off 
  showMap: Boolean, // true - map is visible / false - its off 
})
defineEmits(['toggle-map']) // declares that this component can emit toggle-map — App.vue listens for it via @toggle-map

const { soundEnabled, soundBlockedMessage, toggleSound } = useVoiceAlarm(toRef(props, 'isWarning'))
</script>

<template>
  <!-- full-screen when showMap is false -->
  <div class="overlay" :class="{ 'full-screen': !showMap }">
    <div v-if="!connected" class="status">Connecting to backend...</div>
    <div v-else-if="isWarning" class="banner">
      <span class="icon">⚠</span>
      <span class="message">{{ warningText }}</span>
    </div>
    <!-- only when full-screen is on and no warning is sent -->
    <div v-else-if="!showMap" class="banner idle">No warning</div>
  </div>

  <div class="controls">
    <!-- clicking this emits toggle-map up to App.vue, which actually flips its showMap ref -->
    <button type="button" @click="$emit('toggle-map')">
      {{ showMap ? 'Hide map (field test)' : 'Show map' }}
    </button>
    <!-- toggleSound comes from useVoiceAlarm() above - calling it flips soundEnabled and starts/stops the alarm -->
    <button type="button" @click="toggleSound">
      {{ soundEnabled ? 'Disable voice alarm' : 'Enable voice alarm' }}
    </button>
    <!-- only shown if the browser actually blocked the audio -->
    <div v-if="soundBlockedMessage" class="sound-blocked">{{ soundBlockedMessage }}</div>
  </div>
</template>

<style scoped>
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;        
  font-family: sans-serif;
  pointer-events: none;  
}
.overlay.full-screen {
  bottom: 0;   
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

.overlay.full-screen .status {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  margin: 0;
  border-radius: 0;
  font-size: 1.5rem;
  background: #1a1a1a;
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
.overlay.full-screen .banner {
  height: 100%;       
  font-size: 2.5rem; 
}
.banner.idle {
  background: #1a1a1a;
  color: #888;
  animation: none;
  box-shadow: none;
}
@keyframes pulse {
  0%, 100% { background: rgba(190, 0, 0, 0.92); }
  50% { background: rgba(245, 35, 35, 0.95); }
}
.icon {
  font-size: 1.6rem;
}

.controls {
  position: fixed;   
  bottom: 10px;
  left: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column; 
  align-items: flex-start;
  gap: 6px;
  font-family: sans-serif;
}
.controls button {
  padding: 6px 10px;
  border: 1px solid #666;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.9);
}
.sound-blocked {
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.75);
  color: #ff8080;
  border-radius: 4px;
  font-size: 11px;
}
</style>
