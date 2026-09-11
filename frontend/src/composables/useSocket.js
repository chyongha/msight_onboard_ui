// SOcket.io connection
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

// how long an alert stays on screen after its most recent broadcast
export const CLEAR_AFTER_MS = 7000
// cap on simultaneously stacked alerts
const MAX_ALERTS = 4
// UDP has no "disconnected" signal - the only way to notice the GPS feed
// went quiet is the absence of a new fix for a while. 2s is fast enough to
// notice a real dropout quickly, while staying safely above the expected
// fix interval (the mock sends every 0.5s; real RTK/INS hardware typically
// updates at 1-10Hz) so one slightly-delayed packet doesn't flicker it
export const EGO_STALE_AFTER_MS = 2000

// Falls back to local dev if no .env file available
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000'

// identity to tell rsu is re-broadcasting the same ongoing hazard instead of new alert
// ica - offending vehicle's source ide
// rsa - identical description 
function alertKey(data) {
  return `${data.type}:${data.subject?.source_id ?? data.text}`
}

function alertFields(data) {
  return {
    key: alertKey(data),
    type: data.type,
    category: data.category ?? null,
    severity: data.severity ?? null, // computed on the backend, not currently displayed
    text: data.text,
    headline: data.headline ?? null, // RSA's primary event
    events: Array.isArray(data.events) && data.events.length ? data.events : [data.text],
    subject: data.subject ?? null,
    extent: data.extent ?? null, // RSA only - see alert_formatter.py
    directionSlices: data.direction_slices ?? null, // RSA only - see alert_formatter.py
    trajectory: data.trajectory ?? null,
    timestamp: data.timestamp ?? Date.now() / 1000,
    occurredAt: data.occurred_at ?? data.timestamp ?? Date.now() / 1000, // "when it happened" - see alert_formatter.py's _event_epoch
    lat: data.lat ?? null,
    lon: data.lon ?? null,
  }
}

// single socketio connection controls both warning nad tracking
export function useMsightSocket() {
  const alerts = ref([])  // newest/top of stack first
  const connected = ref(false)
  // latest live tracking frame
  const frame = ref(null)
  // this vehicle's own latest GPS fix - { lat, lon, timestamp } or null before the first one arrives
  const egoPosition = ref(null)

  let socket = null
  let nextId = 1
  const clearTimers = new Map() // alert id -> timeout handle
  let egoStaleTimer = null // single timer - there's only ever one ego position, unlike the per-alert Map above

  function scheduleEgoStale() {
    if (egoStaleTimer) clearTimeout(egoStaleTimer)
    egoStaleTimer = setTimeout(() => { egoPosition.value = null }, EGO_STALE_AFTER_MS)
  }

  function stopTimer(id) {
    const timer = clearTimers.get(id)
    if (timer) {
      clearTimeout(timer)
      clearTimers.delete(id)
    }
  }

  function removeAlert(id) {
    stopTimer(id)
    alerts.value = alerts.value.filter((a) => a.id !== id)
  }

  function startTimer(id) {
    clearTimers.set(id, setTimeout(() => removeAlert(id), CLEAR_AFTER_MS))
  }

  function upsertAlert(data) {
    const key = alertKey(data)
    const existing = alerts.value.find((a) => a.key === key)

    if (existing) {
      // same ongoing situation re-broadcasting - refresh its content/timer
      // and bump it back to the top rather than stacking a duplicate
      stopTimer(existing.id)
      const updated = { id: existing.id, ...alertFields(data) }
      alerts.value = [updated, ...alerts.value.filter((a) => a.id !== existing.id)]
      startTimer(existing.id)
      return
    }

    const id = nextId++
    const next = [{ id, ...alertFields(data) }, ...alerts.value]
    if (next.length > MAX_ALERTS) {
      next.splice(MAX_ALERTS).forEach((evicted) => stopTimer(evicted.id))
    }
    alerts.value = next
    startTimer(id)
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
      if (data.warning) upsertAlert(data)
    })

    // tracking - new frame replaces the most recent frame
    socket.on('frame', (data) => {
      frame.value = data
    })

    // this vehicle's own GPS - new fix replaces the previous one, and
    // restarts the staleness timer so it doesn't just freeze if the feed
    // goes quiet (see EGO_STALE_AFTER_MS above)
    socket.on('ego', (data) => {
      egoPosition.value = data
      scheduleEgoStale()
    })
  })

  // cleanup
  onUnmounted(() => {
    clearTimers.forEach((timer) => clearTimeout(timer))
    clearTimers.clear()
    if (egoStaleTimer) clearTimeout(egoStaleTimer)
    if (socket) socket.disconnect()
  })

  // MapView only shows one alert pin (map isn't the focus right now) - use
  // the newest/top-of-stack alert for that, same as before the stack existed
  const isWarning = computed(() => alerts.value.length > 0)
  const topAlert = computed(() => alerts.value[0] ?? null)
  const warningText = computed(() => topAlert.value?.text ?? '')
  const lat = computed(() => topAlert.value?.lat ?? null)
  const lon = computed(() => topAlert.value?.lon ?? null)

  return { alerts, isWarning, warningText, lat, lon, connected, frame, egoPosition }
}
