<script setup>
import { useMsightSocket } from './composables/useSocket.js'
import WarningBanner from './components/WarningBanner.vue'
import MapView from './components/MapView.vue'

// This is where the composable actually gets called. Everything it
// returns (isWarning, warningText, connected, lat, lon, frame) is
// reactive — when the socket receives new data, these update
// automatically, and anything using them in the template re-renders.
const { isWarning, warningText, connected, lat, lon, frame } = useMsightSocket()
</script>

<template>
  <div class="app">
    <MapView :is-warning="isWarning" :lat="lat" :lon="lon" :warning-text="warningText" :frame="frame" />
    <WarningBanner
      :is-warning="isWarning"
      :warning-text="warningText"
      :connected="connected"
    />
  </div>
</template>

<style scoped>
.app {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>
