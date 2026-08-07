<script setup>
import { toRef } from 'vue'
import { useVoiceAlarm } from '../composables/useVoiceAlarm.js'

// props: data passed IN from a parent component (App.vue, in this case).
// This component doesn't know or care where the data comes from — it
// just displays whatever it's given.
const props = defineProps({
  isWarning: Boolean,      // is there an active alert right now?
  warningText: String,     // text to display for the current alert
  connected: Boolean,      // is the Socket.IO connection to the backend up?
  showMap: Boolean,        // is the map currently visible (normal mode) or hidden (field-test mode)?
})
defineEmits(['toggle-map']) // declares that this component can emit 'toggle-map' — App.vue listens for it via @toggle-map

// The alarm needs to react to isWarning turning on/off, so it's owned
// here rather than in App.vue — this is the only component that already
// has that signal. toRef(props, 'isWarning') wraps just that one prop in
// its own ref, so useVoiceAlarm can watch it reactively without needing
// the whole props object.
const { soundEnabled, soundBlockedMessage, toggleSound } = useVoiceAlarm(toRef(props, 'isWarning'))
</script>

<template>
  <!-- :class="{ 'full-screen': !showMap }" adds the "full-screen" CSS
       class only when showMap is false — this single binding is what
       switches between the thin top strip (map visible) and the
       full-viewport takeover (map hidden). -->
  <div class="overlay" :class="{ 'full-screen': !showMap }">
    <!-- v-if / v-else-if chain: exactly one of these three ever renders -->
    <div v-if="!connected" class="status">Connecting to backend...</div>
    <div v-else-if="isWarning" class="banner">
      <span class="icon">⚠</span>
      <span class="message">{{ warningText }}</span>
    </div>
    <!-- Only needed in full-screen (map-hidden) mode — with the map
         visible, an empty transparent overlay correctly just shows the
         map through it; without the map, leaving this blank would look
         like a frozen/broken screen instead of "no warning right now". -->
    <div v-else-if="!showMap" class="banner idle">No warning</div>
  </div>

  <div class="controls">
    <!-- clicking this emits 'toggle-map' up to App.vue, which actually flips its showMap ref -->
    <button type="button" @click="$emit('toggle-map')">
      {{ showMap ? 'Hide map (field test)' : 'Show map' }}
    </button>
    <!-- toggleSound comes from useVoiceAlarm() above; calling it flips soundEnabled and starts/stops the alarm -->
    <button type="button" @click="toggleSound">
      {{ soundEnabled ? 'Disable voice alarm' : 'Enable voice alarm' }}
    </button>
    <!-- only shown if the browser actually blocked the audio — see useVoiceAlarm.js -->
    <div v-if="soundBlockedMessage" class="sound-blocked">{{ soundBlockedMessage }}</div>
  </div>
</template>

<style scoped>
/* Normally sits on top of MapView.vue's full-screen map (see App.vue)
   rather than covering it — same "strip across the top, map visible
   underneath" layout as msight_original_script/realtime_plot.py's
   #alert-overlay. In full-screen mode (map hidden) it expands to cover
   the whole viewport instead, since there's nothing left to show through it. */
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;           /* sits above MapView.vue's map, which uses z-index: 0 */
  font-family: sans-serif;
  pointer-events: none;    /* lets clicks/drags pass through to the map underneath wherever this overlay has no visible content */
}
.overlay.full-screen {
  bottom: 0;   /* adding bottom:0 to the top/left/right already set above makes this div fill the whole viewport instead of just a strip */
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
/* Only takes effect when BOTH classes are present on the parent div —
   i.e. only in field-test (map hidden) mode. */
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
  animation: pulse 0.8s ease-in-out infinite;  /* the red pulsing effect */
}
.overlay.full-screen .banner {
  height: 100%;       /* fill the whole screen instead of being a thin strip */
  font-size: 2.5rem;  /* bigger text since there's much more room to use */
}
.banner.idle {
  /* Overrides .banner's red background/animation for the "No warning"
     state — works because .banner.idle (two classes) is more specific
     than .banner alone, so these rules win without needing !important. */
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

/* Positioned bottom-left: clear of Leaflet's default top-left zoom
   control and its bottom-right attribution text. Grouped together so
   both toggles live in one place. */
.controls {
  position: fixed;   /* fixed to the viewport, unaffected by .overlay's own positioning */
  bottom: 10px;
  left: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;  /* stack the two buttons vertically */
  align-items: flex-start;
  gap: 6px;
  font-family: sans-serif;
  /* no pointer-events:none here (unlike .overlay above) — these buttons need to stay clickable */
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
