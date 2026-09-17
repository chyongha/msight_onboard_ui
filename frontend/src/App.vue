<script setup>
import { ref } from 'vue'
import { useMsightSocket } from './composables/useSocket.js' // owns the Socket.IO connection
import AlertStack from './components/alert/AlertStack.vue' // stacked alert cards + control buttons
import MapView from './components/MapView.vue' // leaflet map

const {
  alerts,      // active alerts, newest/top of stack first
  isWarning,   // true while at least one ICA/RSA alert is active
  warningText, // human-readable text for the newest alert (empty string when none)
  connected,   // whether the socketio connection to the backend is open
  lat, lon,    // location of the newest alert (both null initially)
  frame,       // latest live tracking event
  egoPosition, // this vehicle's own latest GPS fix
  sdsmFrame,   // latest SDSM sensor frame (real detected objects, not an alert)
} = useMsightSocket()

// 'both' (default, today's behavior) | 'map' | 'alerts' - alert cards used
// to always overlay the map whenever any were active, blocking it; this
// lets the map be viewed alone, or the alerts alone, not just both-or-banner
const viewMode = ref('both')
// independent of viewMode - shown by default (matches the box's prior
// always-on behavior), but toggleable on its own now
const showGpsBox = ref(true)
// SDSM is a data layer (real detected objects), not chrome like the GPS
// box - off by default until asked for, so it doesn't clutter the map
// before anyone's opted into it
const showSdsm = ref(false)
</script>

<template>
  <div class="app">
    <MapView
      v-if="viewMode !== 'alerts'"
      :is-warning="isWarning"
      :lat="lat"
      :lon="lon"
      :warning-text="warningText"
      :frame="frame"
      :ego-position="egoPosition"
      :show-gps-box="showGpsBox"
      :sdsm-frame="sdsmFrame"
      :show-sdsm="showSdsm"
    />
    <!-- Always rendered regardless -->
    <AlertStack
      :alerts="alerts"
      :connected="connected"
      :view-mode="viewMode"
      :show-gps-box="showGpsBox"
      :show-sdsm="showSdsm"
      @set-view-mode="viewMode = $event"
      @toggle-gps-box="showGpsBox = !showGpsBox"
      @toggle-sdsm="showSdsm = !showSdsm"
    />
  </div>
</template>

<style scoped>
.app {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
}
</style>
