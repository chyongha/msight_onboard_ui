<script setup>
// two independent layers - alert / tracking pin 
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import EgoCoordinatesBox from './EgoCoordinatesBox.vue'
import MapLegend from './MapLegend.vue'
import SdsmInfoBox from './SdsmInfoBox.vue'
import { bearingBetween, roughMetersBetween } from '../utils/geo.js'

const props = defineProps({
  isWarning: Boolean, // is there an active alert
  lat: { type: Number, default: null }, // alert latitude
  lon: { type: Number, default: null }, // alert longitude
  warningText: { type: String, default: '' }, // shown in the alert pin's tooltip
  frame: { type: Object, default: null }, // live tracking
  egoPosition: { type: Object, default: null }, // this vehicle's own live GPS fix - { lat, lon, timestamp } or null
  showGpsBox: { type: Boolean, default: true }, // independent of whether the map itself is showing
  sdsmFrame: { type: Object, default: null }, // latest SDSM sensor frame - { source_id, equipment_type, lat, lon, objects[] } or null
  showSdsm: { type: Boolean, default: false }, // SDSM is a data layer, not chrome - off until asked for, unlike showGpsBox
})


const DEFAULT_CENTER = [
  Number(import.meta.env.VITE_DEFAULT_LAT) || 42.2975,
  Number(import.meta.env.VITE_DEFAULT_LON) || -83.7042,
]

const CATEGORY_COLOR = { vehicle: '#3388ff', vru: '#22aa44' } // blue for vehicles, green for pedestrians
const ALERT_STROKE_COLOR = '#cc0000'
const ALERT_FILL_COLOR = '#f52323'
const EGO_COLOR = '#7c5cf0' // weather-purple (--color-cat-weather) - distinct from the alert pin (red) and tracked-object markers (blue/green), since this one means "you"
// SDSM is real detected-object data from a roadside sensor, kept visually
// distinct from the (still mocked) tracking overlay's blue/green - also has
// two categories tracking doesn't (obstacle/animal)
const SDSM_CATEGORY_COLOR = { vehicle: '#ff9f1c', vru: '#00b4d8', obstacle: '#6c757d', animal: '#8ac926' }
// the reporting station (refPos) itself - a muted grey rather than a bold
// color like the categories above, since it's just a fixed reference point
// (where the sensor is), not something that needs to grab attention the
// way a detected object does
const SDSM_STATION_COLOR = '#9aa0a6'

// two separate legend boxes rather than one combined list (see MapView's
// template) - the base one (alert/tracking/ego) always shows, the SDSM one
// only appears, stacked above it, while that layer is toggled on
const baseLegendItems = [
  { color: ALERT_FILL_COLOR, label: 'Alert location' },
  { color: CATEGORY_COLOR.vehicle, label: 'Tracked vehicle' },
  { color: CATEGORY_COLOR.vru, label: 'Tracked pedestrian' },
  { color: EGO_COLOR, label: 'You (GPS)' },
]
const sdsmLegendItems = [
  { color: SDSM_STATION_COLOR, label: 'Reporting station' },
  { color: SDSM_CATEGORY_COLOR.vehicle, label: 'Vehicle' },
  { color: SDSM_CATEGORY_COLOR.vru, label: 'Pedestrian' },
  { color: SDSM_CATEGORY_COLOR.obstacle, label: 'Obstacle' },
  { color: SDSM_CATEGORY_COLOR.animal, label: 'Animal' },
]

const mapContainer = ref(null) // this is how Leaflet gets a real DOM element to attach to
let map = null // leaflet map instance
let alertMarker = null // single red circle marking the most recent alert's location
let hasCenteredOnAlert = false // true after the map has auto-centered on an alert once — prevents re-centering (and fighting your manual panning) on every later alert
const objectMarkers = {} // live tracking object marker
const sdsmObjectMarkers = {} // SDSM detected-object markers - separate layer/store so it can be toggled independently of tracking
let sdsmStationMarker = null // the SDSM reporting station itself (refPos) - a fixed sensor location, not a detected object
let egoMarker = null // this vehicle's own position
let hasCenteredOnEgo = false // same one-time-only pattern as hasCenteredOnAlert - without this, a GPS location far from DEFAULT_CENTER (e.g. testing at a different site, or a mock/default mismatch) would move the marker somewhere off-screen with nothing to make it visible
let egoHeadingDeg = null // last known direction of travel, null until computed from two real fixes - never fabricated from a single point
let lastHeadingRefLatLon = null // the position egoHeadingDeg was last computed FROM

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
      color: ALERT_STROKE_COLOR,
      fillColor: ALERT_FILL_COLOR,
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

// shared by both the (mocked) tracking overlay and the SDSM overlay - both
// produce objects in this exact shape ({id, lat, lon, category, speed,
// heading_deg}, SDSM adds optional `size_m`/`detail`), just from different
// sources/ports, kept on separate marker stores so either layer can be
// toggled independently. Objects render with the same fixed-size icon as
// the ego marker (see buildMarkerIcon()) rather than a true-to-scale
// shape - heading is always known directly here (unlike ego, which has to
// derive it from consecutive fixes), so the arrow is shown immediately.
function syncObjectMarkers(objects, markerStore, colorMap) {
  const seen = new Set()  // tracks which object ids are present in THIS frame, so stale markers can be removed below

  objects.forEach((obj) => {
    seen.add(obj.id)
    const color = colorMap[obj.category] || '#888888'  // grey fallback for any unrecognized category
    const tip = `ID ${obj.id} &bull; ${obj.category}<br>` +
      `speed ${obj.speed.toFixed(1)} m/s<br>` +
      `heading ${obj.heading_deg.toFixed(1)}&deg;` +
      (obj.size_m ? `<br>size ${obj.size_m}` : '') +
      (obj.detail ? `<br>${obj.detail}` : '')
    const latlng = [obj.lat, obj.lon]

    let marker = markerStore[obj.id]
    if (marker) {
      marker.setLatLng(latlng)
      marker.setTooltipContent(tip)
    } else {
      marker = L.marker(latlng, { icon: buildMarkerIcon(color) })
        .bindTooltip(tip, { permanent: false })
        .addTo(map)
      markerStore[obj.id] = marker
    }

    setMarkerHeading(marker, obj.heading_deg)
  })

  // anything not in this frame gets removed
  Object.keys(markerStore).forEach((id) => {
    if (!seen.has(Number(id))) {
      map.removeLayer(markerStore[id])
      delete markerStore[id]
    }
  })
}

function updateObjectMarkers() {
  if (!map || !props.frame) return  // map isn't built yet, or no tracking data has ever arrived
  syncObjectMarkers(props.frame.objects || [], objectMarkers, CATEGORY_COLOR)
}

// a small diamond (rotated square), deliberately NOT the circle+arrow
// shape every detected-object/ego marker uses - this is a fixed sensor
// location, not a moving tracked entity, so it needs to read as a
// different kind of thing at a glance. Muted/low-opacity on purpose - it's
// a reference point, not something that should compete for attention with
// the (moving, actively-detected) object markers
function buildStationIcon() {
  return L.divIcon({
    className: '',
    html: `
      <svg width="22" height="22" viewBox="0 0 22 22" style="opacity: 0.6;">
        <rect x="5" y="5" width="12" height="12" fill="${SDSM_STATION_COLOR}" stroke="#ffffff" stroke-width="1.5" transform="rotate(45 11 11)" />
      </svg>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  })
}

function updateSdsmStationMarker() {
  const hasFix = props.showSdsm && props.sdsmFrame
    && typeof props.sdsmFrame.lat === 'number' && typeof props.sdsmFrame.lon === 'number'

  if (!hasFix) {
    if (sdsmStationMarker) {
      map.removeLayer(sdsmStationMarker)
      sdsmStationMarker = null
    }
    return
  }

  const latlng = [props.sdsmFrame.lat, props.sdsmFrame.lon]
  const tip = `SDSM reporting station<br>${props.sdsmFrame.source_id ?? 'unknown source'} (${props.sdsmFrame.equipment_type ?? 'unknown type'})`

  if (sdsmStationMarker) {
    sdsmStationMarker.setLatLng(latlng)
    sdsmStationMarker.setTooltipContent(tip)
  } else {
    sdsmStationMarker = L.marker(latlng, { icon: buildStationIcon() })
      .bindTooltip(tip, { permanent: false })
      .addTo(map)
  }
}

function updateSdsmMarkers() {
  if (!map) return

  if (!props.showSdsm || !props.sdsmFrame) {
    // layer toggled off, or no frame (yet, or gone stale) - clear
    // everything rather than leaving stale markers on screen, same fix as
    // the ego marker's staleness handling
    Object.keys(sdsmObjectMarkers).forEach((id) => {
      map.removeLayer(sdsmObjectMarkers[id])
      delete sdsmObjectMarkers[id]
    })
    updateSdsmStationMarker()
    return
  }

  syncObjectMarkers(props.sdsmFrame.objects || [], sdsmObjectMarkers, SDSM_CATEGORY_COLOR)
  updateSdsmStationMarker()
}

// circle (always) + a small triangular arrow (hidden via opacity until a
// real heading is known) - one icon shape/size for EVERY marker on this map
// (ego, tracked objects, SDSM objects), just a different fill color per
// category/purpose, so they read as one consistent visual language instead
// of ego being a crisp icon while tracked/SDSM objects were tiny
// real-world-scaled dots/boxes at typical zoom. The arrow is toggled/
// rotated in place rather than swapping icons, see setMarkerHeading().
function buildMarkerIcon(color) {
  // bigger than the first version (26->36px), and the arrow redrawn to sit
  // mostly ABOVE the circle (tip near the very top of the icon, base just
  // touching the circle's edge) instead of deep inside it - the previous
  // arrow's base (y=11.5) sat well past the circle's own edge (y=5) in a
  // 16px-diameter circle, so the two blended into one blob. Anchoring stays
  // on the circle's center (the real lat/lon point), unaffected by the
  // arrow extending upward past it.
  return L.divIcon({
    className: '', // overrides Leaflet's default 'leaflet-div-icon' class (a white box + border) - the SVG below is the whole visual
    html: `
      <div class="marker-icon-rotate" style="transform: rotate(0deg);">
        <svg width="36" height="36" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="9" fill="${color}" stroke="#ffffff" stroke-width="2.5" />
          <path class="marker-icon-arrow" d="M18 2 L24 12 L18 9 L12 12 Z" fill="${color}" stroke="#ffffff" stroke-width="1.5" style="opacity: 0; transition: opacity 0.25s ease;" />
        </svg>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  })
}

// rotates a marker built by buildMarkerIcon() to headingDeg and reveals its
// arrow (opacity 0 -> 1) - shared by the ego marker (heading derived from
// consecutive fixes, so this is only called once one's known) and tracked/
// SDSM object markers (heading arrives directly in every frame, so this is
// called immediately on every update)
function setMarkerHeading(marker, headingDeg) {
  const el = marker.getElement()
  const rotateEl = el?.querySelector('.marker-icon-rotate')
  const arrowEl = el?.querySelector('.marker-icon-arrow')
  if (rotateEl) rotateEl.style.transform = `rotate(${headingDeg}deg)`
  if (arrowEl) arrowEl.style.opacity = '1'
}

function updateEgoMarker() {
  if (!map) return

  if (!props.egoPosition || typeof props.egoPosition.lat !== 'number' || typeof props.egoPosition.lon !== 'number') {
    if (egoMarker) {
      map.removeLayer(egoMarker)
      egoMarker = null
    }
    egoHeadingDeg = null
    lastHeadingRefLatLon = null
    return
  }

  const { lat, lon } = props.egoPosition
  const latlng = [lat, lon]

  // only recompute heading (and only rotate) once the vehicle has actually
  // moved a meaningful distance since the last computed heading - guards
  // against the arrow jittering/spinning on GPS noise while stationary
  if (lastHeadingRefLatLon) {
    const movedMeters = roughMetersBetween(lastHeadingRefLatLon.lat, lastHeadingRefLatLon.lon, lat, lon)
    if (movedMeters > 1.0) {
      egoHeadingDeg = bearingBetween(lastHeadingRefLatLon.lat, lastHeadingRefLatLon.lon, lat, lon)
      lastHeadingRefLatLon = { lat, lon }
    }
  } else {
    lastHeadingRefLatLon = { lat, lon } // first-ever fix - nothing to compute a bearing from yet
  }

  if (egoMarker) {
    egoMarker.setLatLng(latlng)
  } else {
    egoMarker = L.marker(latlng, { icon: buildMarkerIcon(EGO_COLOR) })
      .bindTooltip('You (GPS)', { permanent: false })
      .addTo(map)
  }

  if (egoHeadingDeg !== null) {
    setMarkerHeading(egoMarker, egoHeadingDeg)
  }

  // center on the FIRST ego fix only, same one-time pattern as the alert
  // pin's hasCenteredOnAlert - every fix after that just moves the marker,
  // no continuous recentering (that would fight manual panning in a way a
  // single one-time center doesn't). Without even the one-time center, a
  // real GPS location far from DEFAULT_CENTER - a different test site, or
  // any future mismatch between the two - would move the marker somewhere
  // off-screen with nothing to make it visible.
  if (!hasCenteredOnEgo) {
    map.setView(latlng, 18)
    hasCenteredOnEgo = true
  }
}

onMounted(() => {
  map = L.map(mapContainer.value).setView(DEFAULT_CENTER, 18)

  L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 21, attribution: 'Tiles &copy; Esri' }
  ).addTo(map)

  updateAlertMarker()
  updateObjectMarkers()
  updateEgoMarker()
  updateSdsmMarkers()
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})

watch(() => [props.isWarning, props.lat, props.lon, props.warningText], updateAlertMarker)
watch(() => props.frame, updateObjectMarkers)
watch(() => props.egoPosition, updateEgoMarker)
watch(() => [props.sdsmFrame, props.showSdsm], updateSdsmMarkers)
</script>

<template>
  <div ref="mapContainer" class="map"></div>
  <EgoCoordinatesBox v-if="showGpsBox" :ego-position="egoPosition" />
  <SdsmInfoBox v-if="showSdsm" :sdsm-frame="sdsmFrame" :category-color="SDSM_CATEGORY_COLOR" />
  <div class="legend-stack">
    <MapLegend v-if="showSdsm" title="SDSM" :items="sdsmLegendItems" />
    <MapLegend :items="baseLegendItems" />
  </div>
</template>

<style scoped>
.map {
  position: absolute;
  inset: 0;
  z-index: 0;
}
/* anchored at the bottom-right corner, growing upward as boxes are added -
   the SDSM legend (first in DOM) ends up stacked above the always-present
   base legend (last in DOM) without either needing to know the other's
   height */
.legend-stack {
  position: absolute;
  bottom: var(--space-3);
  right: var(--space-3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-2);
}
</style>
