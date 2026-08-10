// Shared lookups the alert components use to turn backend category strings
// into display labels/colors, kept in one place so they stay consistent.
// cards are colored by category 

const CATEGORY_META = {
  vehicle: { label: 'Vehicle', colorVar: '--color-cat-vehicle', bgVar: '--color-cat-vehicle-bg' },
  pedestrian: { label: 'Pedestrian', colorVar: '--color-cat-pedestrian', bgVar: '--color-cat-pedestrian-bg' },
  road_hazard: { label: 'Road hazard', colorVar: '--color-cat-hazard', bgVar: '--color-cat-hazard-bg' },
  weather: { label: 'Weather', colorVar: '--color-cat-weather', bgVar: '--color-cat-weather-bg' },
  other: { label: 'Event', colorVar: '--color-cat-other', bgVar: '--color-cat-other-bg' },
}

const COMPASS_DIRECTIONS = [
  'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
]

// falls back to 'other' for unrecognized/missing category - never silently render nothing
export function categoryMeta(category) {
  return CATEGORY_META[category] || CATEGORY_META.other
}

// heading in compass degrees (16 points)
export function compassLabel(headingDeg) {
  if (typeof headingDeg !== 'number' || Number.isNaN(headingDeg)) return null
  const normalized = ((headingDeg % 360) + 360) % 360
  return COMPASS_DIRECTIONS[Math.round(normalized / 22.5) % 16]
}

// m/s -> mph
export function metersPerSecondToMph(speedMps) {
  if (typeof speedMps !== 'number' || Number.isNaN(speedMps)) return null
  return Math.round(speedMps * 2.23694)
}
