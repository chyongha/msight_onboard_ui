// SOcket.io connection 
import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

// clean the banner after 3 sec
const CLEAR_AFTER_MS = 3000  

// Falls back to local dev if no .env file available 
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000'

// single socketio connection controls both warning nad tracking 
export function useMsightSocket() {
  const isWarning = ref(false)
  const warningText = ref('')
  const connected = ref(false)
  // last known alert location 
  const lat = ref(null)
  const lon = ref(null)
  // latest live tracking frame 
  const frame = ref(null)

  let socket = null       // the actual socket.io-client connection object
  let clearTimer = null   // clear the banner timeout 

  function cancelClear() {
    if (clearTimer !== null) {
      clearTimeout(clearTimer)
      clearTimer = null
    }
  }

  // reset the countdown every new alerts 
  function scheduleClear() {
    cancelClear()  // always clear any existing timer first, so repeated alerts restart the full countdown instead of stacking timers
    clearTimer = setTimeout(() => {
      isWarning.value = false
      warningText.value = ''
      clearTimer = null
    }, CLEAR_AFTER_MS)
  }

  // where the network connection actually opens 
  onMounted(() => {
    socket = io(BACKEND_URL)

    socket.on('connect', () => {
      connected.value = true
    })

    socket.on('disconnect', () => {
      connected.value = false
    })

    socket.on('warning', (data) => {
      isWarning.value = data.warning
      warningText.value = data.text
      if (data.lat != null) lat.value = data.lat
      if (data.lon != null) lon.value = data.lon
      if (data.warning) {
        scheduleClear()
      } else {
        cancelClear()
      }
    })

    // tracking - new frame replaces the most recent frame 
    socket.on('frame', (data) => {
      frame.value = data
    })
  })

  // cleanup
  onUnmounted(() => {
    cancelClear()
    if (socket) socket.disconnect()
  })

  return { isWarning, warningText, connected, lat, lon, frame }
}
