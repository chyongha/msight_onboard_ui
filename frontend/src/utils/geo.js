// Raw lat/lon geometry helpers, reusable by any map code - kept separate
// from alertVisuals.js, which is specifically alert-card display formatting.

function toRad(deg) {
  return (deg * Math.PI) / 180
}
function toDeg(rad) {
  return (rad * 180) / Math.PI
}

// standard initial-bearing (great-circle) formula between two points ->
// compass degrees, 0-360, clockwise from north
export function bearingBetween(lat1, lon1, lat2, lon2) {
  const phi1 = toRad(lat1)
  const phi2 = toRad(lat2)
  const deltaLon = toRad(lon2 - lon1)

  const y = Math.sin(deltaLon) * Math.cos(phi2)
  const x = Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLon)

  return (toDeg(Math.atan2(y, x)) + 360) % 360
}

// flat-earth approximation, meters - fine at intersection/local scale (same
// reasoning backend/geometry.py already uses server-side). Only used here
// as a movement-detection threshold, not for precision distance.
export function roughMetersBetween(lat1, lon1, lat2, lon2) {
  const METERS_PER_DEG_LAT = 111320
  const dLat = (lat2 - lat1) * METERS_PER_DEG_LAT
  const dLon = (lon2 - lon1) * METERS_PER_DEG_LAT * Math.cos(toRad(lat1))
  return Math.hypot(dLat, dLon)
}
