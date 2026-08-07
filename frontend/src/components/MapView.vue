<script setup>
// two independent layers - alert / tracking pin 
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'            
import 'leaflet/dist/leaflet.css'  

const props = defineProps({
  isWarning: Boolean, // is there an active alert 
  lat: { type: Number, default: null }, // alert latitude 
  lon: { type: Number, default: null }, // alert longitude
  warningText: { type: String, default: '' }, // shown in the alert pin's tooltip
  frame: { type: Object, default: null }, // live tracking 
})


const DEFAULT_CENTER = [
  Number(import.meta.env.VITE_DEFAULT_LAT) || 42.2808,
  Number(import.meta.env.VITE_DEFAULT_LON) || -83.7430,
]

const CATEGORY_COLOR = { vehicle: '#3388ff', vru: '#22aa44' } // blue for vehicles, green for pedestrians

const mapContainer = ref(null) // this is how Leaflet gets a real DOM element to attach to
let map = null // leaflet map instance
let alertMarker = null // single red circle marking the most recent alert's location
let hasCenteredOnAlert = false // true after the map has auto-centered on an alert once — prevents re-centering (and fighting your manual panning) on every later alert
const objectMarkers = {} // live tracking object marker 

function updateAlertMarker() {
  if (!map) return  

  if (!props.isWarning || props.lat === null || props.lon === null) {
    // no active alert — remove the marker if one currently exists
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
      color: '#cc0000',     
      fillColor: '#f52323', 
      fillOpacity: 0.9,
      weight: 2,             
    })
      .bindTooltip(props.warningText || 'Warning', { permanent: false }) // permanent: false = only shows on hover, not always visible
      .addTo(map)
  }

  // center the first ever alert location 
  if (!hasCenteredOnAlert) {
    map.setView(latlng, 18)  /// 18 - zoom level 
    hasCenteredOnAlert = true
  }
}

function updateObjectMarkers() {
  if (!map || !props.frame) return  // map isn't built yet, or no tracking data has ever arrived

  const objects = props.frame.objects || []
  const seen = new Set()  // tracks which object ids are present in THIS frame, so stale markers can be removed below

  objects.forEach((obj) => {
    seen.add(obj.id)
    const color = CATEGORY_COLOR[obj.category] || '#888888'  // grey fallback for any unrecognized category
    const tip = `ID ${obj.id} &bull; ${obj.category}<br>` +
      `speed ${obj.speed.toFixed(1)} m/s<br>` +
      `heading ${obj.heading_deg.toFixed(1)}&deg;`
    
    const isVehicleBox = obj.shape === 'vehicle_box' && Array.isArray(obj.corners) && obj.corners.length >= 4

    const existing = objectMarkers[obj.id]
    if (existing) {
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
      // Shape changed - drop and recreate 
      map.removeLayer(existing)
      delete objectMarkers[obj.id]
    }

    // no existing marker - create a new one 
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

  // anything not in the frame gets removed 
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
