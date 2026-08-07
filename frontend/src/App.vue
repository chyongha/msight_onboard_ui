<script setup>
import { ref } from 'vue'                                    
import { useMsightSocket } from './composables/useSocket.js' // owns the Socket.IO connection 
import WarningBanner from './components/WarningBanner.vue'   // alert banner + control buttons
import MapView from './components/MapView.vue'               // leaflet map

// This is where the composable actually gets called. Everything it returns is reactive — when the socket receives new data, these update
// automatically, and anything using them in the template re-renders.
const {
  isWarning,    // true while an ICA/RSA alert is currently active
  warningText,  // human-readable text for the current alert (empty string when none)
  connected,    // whether the Socket.IO connection to the backend is currently open
  lat, lon,     // location of the most recent alert — both null until the first one ever arrives
  frame,        // latest live-tracking payload {objects: [...], timestamp} — mocked backend for now, see useSocket.js
} = useMsightSocket()

// Field-test option, per supervisor: the map isn't the important part for
// testing warning delivery — this lets it be hidden so only the banner
// shows, full-screen. Owned here (not inside WarningBanner.vue) because
// it also controls whether <MapView> renders at all; WarningBanner just
// requests the toggle via an event, same pattern as
// msight_old_structure's Hud.vue emitting 'toggle-sound'/'toggle-range'
// up to its parent. v-if (not v-show) so hiding it actually tears the
// Leaflet map down rather than leaving it running invisibly — also
// sidesteps Leaflet's known "container was hidden, tiles render wrong
// until you interact with it" issue that v-show + display:none causes.
const showMap = ref(true) // true = map visible (default); false = field-test mode, banner only
</script>

<template>
  <div class="app">
    <!-- v-if means this component (and the whole Leaflet map instance
         inside it) only exists in the DOM while showMap is true —
         toggling off destroys it, toggling back on builds a fresh one. -->
    <MapView
      v-if="showMap"
      :is-warning="isWarning"
      :lat="lat"
      :lon="lon"
      :warning-text="warningText"
      :frame="frame"
    />
    <!-- Always rendered, regardless of showMap — it's the one that
         decides (via the show-map prop) whether to draw itself as a top
         strip or a full-screen takeover, and it owns the toggle buttons. -->
    <WarningBanner
      :is-warning="isWarning"
      :warning-text="warningText"
      :connected="connected"
      :show-map="showMap"
      @toggle-map="showMap = !showMap"
    />
  </div>
</template>

<style scoped>
.app {
  position: relative;   /* lets the children position themselves with position:absolute relative to this div, not the whole page */
  width: 100vw;
  height: 100vh;         /* fills the browser viewport exactly, no page scrolling */
  overflow: hidden;
  background: #1a1a1a;  /* visible whenever the map is hidden (field-test mode) */
}
</style>
