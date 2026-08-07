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
import L from 'leaflet'                 // the Leaflet mapping library itself
import 'leaflet/dist/leaflet.css'       // Leaflet's own CSS — without this the map renders broken/unstyled

const props = defineProps({
  isWarning: Boolean,                              // is there an active alert right now?
  lat: { type: Number, default: null },            // alert latitude (null = no alert yet)
  lon: { type: Number, default: null },            // alert longitude
  warningText: { type: String, default: '' },      // shown in the alert pin's tooltip
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
  // Number(undefined) is NaN, and `NaN || x` falls through to x — so an
  // unset env var correctly falls back to the literal default here.
  Number(import.meta.env.VITE_DEFAULT_LAT) || 42.2808,
  Number(import.meta.env.VITE_DEFAULT_LON) || -83.7430,
]

const CATEGORY_COLOR = { vehicle: '#3388ff', vru: '#22aa44' } // blue for vehicles, green for pedestrians/VRUs, on the live-tracking layer

const mapContainer = ref(null)     // bound to the <div ref="mapContainer"> below — this is how Leaflet gets a real DOM element to attach to
let map = null                     // the Leaflet map instance; a plain variable, not a ref — Leaflet manages its own internal state, Vue doesn't need to track it
let alertMarker = null             // the single red circle marking the most recent alert's location, or null if none is showing
let hasCenteredOnAlert = false     // true after the map has auto-centered on an alert once — prevents re-centering (and fighting your manual panning) on every later alert
// Live object markers, keyed by object id — mutated in place rather than
// re-rendered on every frame (avoids flicker), same reasoning as
// LiveMap.vue's imperative Leaflet state.
const objectMarkers = {}

function updateAlertMarker() {
  if (!map) return  // guard: this can fire (via the watch() below) before onMounted() has created the map — nothing to do yet

  if (!props.isWarning || props.lat === null || props.lon === null) {
    // no active alert (or no location for it) — remove the marker if one currently exists
    if (alertMarker) {
      map.removeLayer(alertMarker)
      alertMarker = null
    }
    return
  }

  const latlng = [props.lat, props.lon]

  if (alertMarker) {
    // marker already exists — move it and refresh its tooltip text rather than destroying/recreating it
    alertMarker.setLatLng(latlng)
    alertMarker.setTooltipContent(props.warningText || 'Warning')
  } else {
    // first time seeing an alert (or the marker was just removed above) — create it fresh
    alertMarker = L.circleMarker(latlng, {
      radius: 10,
      color: '#cc0000',       // outline color
      fillColor: '#f52323',   // fill color
      fillOpacity: 0.9,
      weight: 2,               // outline thickness
    })
      .bindTooltip(props.warningText || 'Warning', { permanent: false }) // permanent: false = only shows on hover, not always visible
      .addTo(map)
  }

  // Center on the first alert location we ever see, then leave the user
  // free to pan/zoom by hand afterward — same pattern as the original
  // script's `centered` flag.
  if (!hasCenteredOnAlert) {
    map.setView(latlng, 18)  // 18 = zoom level (higher number = more zoomed in)
    hasCenteredOnAlert = true
  }
}

function updateObjectMarkers() {
  if (!map || !props.frame) return  // guard: map isn't built yet, or no tracking data has ever arrived

  const objects = props.frame.objects || []
  const seen = new Set()  // tracks which object ids are present in THIS frame, so stale markers can be removed below

  objects.forEach((obj) => {
    seen.add(obj.id)
    const color = CATEGORY_COLOR[obj.category] || '#888888'  // grey fallback for any unrecognized category
    const tip = `ID ${obj.id} &bull; ${obj.category}<br>` +
      `speed ${obj.speed.toFixed(1)} m/s<br>` +
      `heading ${obj.heading_deg.toFixed(1)}&deg;`
    // vehicles are drawn as rotated rectangles (corners already computed
    // backend-side in geometry.py); anything else (pedestrians) is a plain circle
    const isVehicleBox = obj.shape === 'vehicle_box' && Array.isArray(obj.corners) && obj.corners.length >= 4

    const existing = objectMarkers[obj.id]
    if (existing) {
      // Leaflet polygons expose getLatLngs() (plural — multiple points);
      // circles expose getLatLng() (singular — one center point). This is
      // how we tell which kind of marker we already have for this id,
      // without needing a separate flag stored alongside it.
      const existingIsPolygon = typeof existing.getLatLngs === 'function' && typeof existing.getLatLng !== 'function'

      if (isVehicleBox && existingIsPolygon) {
        // still a vehicle box — update its corner positions/color/tooltip in place
        existing.setLatLngs(obj.corners)
        existing.setStyle({ color, fillColor: color })
        existing.setTooltipContent(tip)
        return  // done with this object — skip the "create new marker" code below
      }
      if (!isVehicleBox && !existingIsPolygon) {
        // still a circle — same idea, update in place
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

    // No existing marker for this id (brand new, or just deleted above
    // because its shape changed) — create the right marker type from scratch.
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
    // Object.keys() always returns strings, even for numeric keys —
    // Number(id) converts back so it can be compared against the
    // numeric ids stored in `seen`.
    if (!seen.has(Number(id))) {
      map.removeLayer(objectMarkers[id])
      delete objectMarkers[id]
    }
  })
}

onMounted(() => {
  // mapContainer.value is the real <div> element by this point (the
  // template has already rendered) — this is the one time Leaflet needs
  // an actual DOM node to attach itself to.
  map = L.map(mapContainer.value).setView(DEFAULT_CENTER, 18)

  L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 21, attribution: 'Tiles &copy; Esri' }
  ).addTo(map)

  // In case props already had alert/tracking data by the time this
  // component mounted (e.g. the socket connected and data arrived before
  // the map even existed) — draw it immediately rather than waiting for
  // the next change to trigger the watch()es below.
  updateAlertMarker()
  updateObjectMarkers()
})

onBeforeUnmount(() => {
  // Clean up the Leaflet instance whenever this component is removed
  // (e.g. the field-test map toggle in App.vue sets v-if="false") —
  // otherwise it'd leak memory/event listeners every time the map is
  // hidden and shown again.
  if (map) {
    map.remove()
    map = null
  }
})

// Vue's watch() re-runs its callback whenever the watched value changes.
// Watching an array literal like this fires if ANY of the listed values change.
watch(() => [props.isWarning, props.lat, props.lon, props.warningText], updateAlertMarker)
watch(() => props.frame, updateObjectMarkers)
</script>

<template>
  <!-- ref="mapContainer" here is exactly what mapContainer.value points to in the script above -->
  <div ref="mapContainer" class="map"></div>
</template>

<style scoped>
.map {
  position: absolute;
  inset: 0;       /* shorthand for top:0; right:0; bottom:0; left:0 — fills its parent completely */
  z-index: 0;     /* sits behind WarningBanner.vue's overlay, which uses z-index: 1000 */
}
</style>
