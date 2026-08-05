// A "composable" is just a plain JS function that uses Vue's ref() and
// returns reactive state — a reusable piece of logic any component can
// call. This one owns the Socket.IO connection so App.vue doesn't have
// to know about socket.io-client directly at all.
import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

// ICA/RSA are alert-only message types (see backend/alert_formatter.py) —
// there's no "all clear" message, the RSU just stops sending. So instead
// of waiting for an explicit warning:false, we clear the banner after
// this much silence since the last alert.
const CLEAR_AFTER_MS = 3000

// Deployment-configurable, not hardcoded — this same built frontend needs
// to run against whatever host the backend is actually on (a dev laptop
// today, some other box on the roadside network tomorrow), not just
// 127.0.0.1. Vite only exposes env vars prefixed VITE_ to browser code;
// see frontend/.env.example. Falls back to the local-dev default when no
// .env is present, so nothing changes for local development.
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000'

// Renamed from useWarningSocket now that this owns the whole backend
// connection, not just alerts — one Socket.IO connection multiplexes
// both the 'warning' (ICA/RSA) and 'frame' (live tracking) events;
// opening a second io() connection just for 'frame' would be wasteful
// and isn't how Socket.IO is meant to be used.
export function useMsightSocket() {
  const isWarning = ref(false)
  const warningText = ref('')
  const connected = ref(false)
  // Last known alert location. Not reset by the clear timer below — MapView
  // only renders a marker while isWarning is true, so a stale lat/lon
  // sitting here unused after a warning clears is harmless.
  const lat = ref(null)
  const lon = ref(null)
  // Latest live-tracking payload: {objects: [...], timestamp}. Mocked
  // for now — see backend/tracking_formatter.py's docstring.
  const frame = ref(null)

  let socket = null
  let clearTimer = null

  function cancelClear() {
    if (clearTimer !== null) {
      clearTimeout(clearTimer)
      clearTimer = null
    }
  }

  // Resets the countdown on every new alert, rather than letting the
  // first alert's timer fire out from under a still-active warning.
  function scheduleClear() {
    cancelClear()
    clearTimer = setTimeout(() => {
      isWarning.value = false
      warningText.value = ''
      clearTimer = null
    }, CLEAR_AFTER_MS)
  }

  onMounted(() => {
    socket = io(BACKEND_URL)

    socket.on('connect', () => {
      connected.value = true
    })

    socket.on('disconnect', () => {
      connected.value = false
    })

    // This is the same emit('warning', ...) / on('warning', ...) pattern
    // you already know from the map script's 'frame' event — just a
    // different event name and payload shape.
    socket.on('warning', (data) => {
      isWarning.value = data.warning
      warningText.value = data.text
      if (data.lat != null) lat.value = data.lat
      if (data.lon != null) lon.value = data.lon

      // If a message ever does carry an explicit warning:false, trust it
      // immediately instead of waiting out the silence timer.
      if (data.warning) {
        scheduleClear()
      } else {
        cancelClear()
      }
    })

    socket.on('frame', (data) => {
      frame.value = data
    })
  })

  onUnmounted(() => {
    cancelClear()
    if (socket) socket.disconnect()
  })

  return { isWarning, warningText, connected, lat, lon, frame }
}