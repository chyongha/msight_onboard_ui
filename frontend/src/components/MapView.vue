<script setup>
// Ports the map bits of msight_original_script/realtime_plot.py into a
// Vue component: same Esri World_Imagery tile source, same "circle marker,
// not a default Leaflet icon" choice (avoids the classic bundler pitfall
// where Leaflet's default marker images 404 under Vite/webpack).
//
// Two independent layers on the same Leaflet map instance:
//   - the alert pin: lat/lon already embedded in the decoded ICA/RSA
//     alert, visible only while isWarning is true.
//   - live object markers: ported from msight_old_structure's
//     LiveMap.vue, trimmed of conflict/ego-vehicle highlighting — this
//     project doesn't recompute conflicts itself (the RSU already
//     decides that via ICA/RSA), so there's no "conflict" or "ego"
//     concept here, just plain vehicle/VRU markers.
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  isWarning: Boolean,
  lat: { type: Number, default: null },
  lon: { type: Number, default: null },
  warningText: { type: String, default: '' },
  // Live-tracking payload from backend/tracking_formatter.py (mocked for
  // now — see its docstring): {objects: [...], timestamp}.
  frame: { type: Object, default: null },
})

// Fallback center for before the first alert ever arrives. Deployment-
// configurable (see frontend/.env.example) rather than hardcoded — same
// reasoning as VITE_BACKEND_URL: this bundle needs to work at whatever
// intersection it's actually deployed to, not just this test one. Falls
// back to mock_sender.py's test coordinates when unset.
const DEFAULT_CENTER = [
  Number(import.meta.env.VITE_DEFAULT_LAT) || 42.2808,
  Number(import.meta.env.VITE_DEFAULT_LON) || -83.7430,
]

const CATEGORY_COLOR = { vehicle: '#3388ff', vru: '#22aa44' }

const mapContainer = ref(null)
let map = null
let alertMarker = null
let hasCenteredOnAlert = false
// Live object markers, keyed by object id — mutated in place rather than
// re-rendered on every frame (avoids flicker), same reasoning as
// LiveMap.vue's imperative Leaflet state.
const objectMarkers = {}

function updateAlertMarker() {
  if (!map) return

  if (!props.isWarning || props.lat === null || props.lon === null) {
    if (alertMarker) {
      map.removeLayer(alertMarker)
      alertMarker = null
    }
    return
  }

  const latlng = [props.lat, props.lon]

  if (alertMarker) {
    alertMarker.setLatLng(latlng)
    alertMarker.setTooltipContent(props.warningText || 'Warning')
  } else {
    alertMarker = L.circleMarker(latlng, {
      radius: 10,
      color: '#cc0000',
      fillColor: '#f52323',
      fillOpacity: 0.9,
      weight: 2,
    })
      .bindTooltip(props.warningText || 'Warning', { permanent: false })
      .addTo(map)
  }

  // Center on the first alert location we ever see, then leave the user
  // free to pan/zoom by hand afterward — same pattern as the original
  // script's `centered` flag.
  if (!hasCenteredOnAlert) {
    map.setView(latlng, 18)
    hasCenteredOnAlert = true
  }
}

function updateObjectMarkers() {
  if (!map || !props.frame) return

  const objects = props.frame.objects || []
  const seen = new Set()

  objects.forEach((obj) => {
    seen.add(obj.id)
    const color = CATEGORY_COLOR[obj.category] || '#888888'
    const tip = `ID ${obj.id} &bull; ${obj.category}<br>` +
      `speed ${obj.speed.toFixed(1)} m/s<br>` +
      `heading ${obj.heading_deg.toFixed(1)}&deg;`
    const isVehicleBox = obj.shape === 'vehicle_box' && Array.isArray(obj.corners) && obj.corners.length >= 4

    const existing = objectMarkers[obj.id]
    if (existing) {
      const existingIsPolygon = typeof existing.getLatLngs === 'function' && typeof existing.getLatLng !== 'function'

      if (isVehicleBox && existingIsPolygon) {
        existing.setLatLngs(obj.corners)
        existing.setStyle({ color, fillColor: color })
        existing.setTooltipContent(tip)
        return
      }
      if (!isVehicleBox && !existingIsPolygon) {
        existing.setLatLng([obj.lat, obj.lon])
        existing.setStyle({ color, fillColor: color, radius: obj.radius_m })
        existing.setTooltipContent(tip)
        return
      }
      // Shape changed (e.g. a re-categorized object) — drop and recreate
      // below rather than trying to morph a circle into a polygon.
      map.removeLayer(existing)
      delete objectMarkers[obj.id]
    }

    if (isVehicleBox) {
      objectMarkers[obj.id] = L.polygon(obj.corners, {
        color, fillColor: color, fillOpacity: 0.35, weight: 2,
      }).bindTooltip(tip, { permanent: false }).addTo(map)
    } else {
      objectMarkers[obj.id] = L.circle([obj.lat, obj.lon], {
        radius: obj.radius_m || 1.0, color, fillColor: color, fillOpacity: 0.75, weight: 2,
      }).bindTooltip(tip, { permanent: false }).addTo(map)
    }
  })

  // Anything not in this frame anymore (left the detection range) gets removed.
  Object.keys(objectMarkers).forEach((id) => {
    if (!seen.has(Number(id))) {
      map.removeLayer(objectMarkers[id])
      delete objectMarkers[id]
    }
  })
}

onMounted(() => {
  map = L.map(mapContainer.value).setView(DEFAULT_CENTER, 18)

  L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 21, attribution: 'Tiles &copy; Esri' }
  ).addTo(map)

  updateAlertMarker()
  updateObjectMarkers()
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})

watch(() => [props.isWarning, props.lat, props.lon, props.warningText], updateAlertMarker)
watch(() => props.frame, updateObjectMarkers)
</script>

<template>
  <div ref="mapContainer" class="map"></div>
</template>

<style scoped>
.map {
  position: absolute;
  inset: 0;
  z-index: 0;
}
</style>
