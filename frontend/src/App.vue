<script setup>
import { ref } from 'vue'                                    
import { useMsightSocket } from './composables/useSocket.js' // owns the Socket.IO connection 
import WarningBanner from './components/WarningBanner.vue' // alert banner + control buttons
import MapView from './components/MapView.vue' // leaflet map

const {
  isWarning, // true while an ICA/RSA alert is currently active
  warningText, // human-readable text for the current alert (empty string when none)
  connected, // whether the socketio connection to the backend is open 
  lat, lon,  // location of the most recent alert (both null initially)
  frame,  // latest live tracking event 
} = useMsightSocket()

const showMap = ref(true) // true = map visible / false = only banner visible 
</script>

<template>
  <div class="app">
    <MapView
      v-if="showMap"
      :is-warning="isWarning"
      :lat="lat"
      :lon="lon"
      :warning-text="warningText"
      :frame="frame"
    />
    <!-- Always rendered regardless -->
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
  position: relative;  
  width: 100vw;
  height: 100vh;    
  overflow: hidden;
  background: #1a1a1a; 
}
</style>
