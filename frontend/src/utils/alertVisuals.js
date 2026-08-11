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

// epoch seconds -> "when this happened", replacing the old live "Xs ago"
// clock - the countdown bar already says how much longer the card has, so
// this shows a fixed point in time instead of a second relative-time
// readout. Includes the date when occurredAt isn't today - a minute-of-
// year-derived backend value (see alert_formatter.py's _event_epoch) can
// easily land on a different day than "now", and a bare time with no date
// would misleadingly read as today.
export function formatEventTime(occurredAtSeconds) {
  if (typeof occurredAtSeconds !== 'number' || Number.isNaN(occurredAtSeconds)) return null
  const when = new Date(occurredAtSeconds * 1000)
  const time = when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  const isToday = when.toDateString() === new Date().toDateString()
  if (isToday) return time
  return `${when.toLocaleDateString([], { month: 'short', day: 'numeric' })}, ${time}`
}

const GEAR_LABELS = {
  forwardGears: 'Forward gear',
  reverseGears: 'Reverse',
  park: 'Parked',
  neutral: 'Neutral',
}

// raw ICAEncoder transmission string -> display label, null if unrecognized/missing
export function gearLabel(gear) {
  return GEAR_LABELS[gear] || null
}

// Descriptive (non-causal) chip text for AlertSubject.vue's "Vehicle"/
// "Pedestrian"/"Extent" section - speed/heading are deliberately excluded,
// DirectionIndicator.vue's arrow already says those. A single source of
// truth so AlertCardFull.vue can decide whether the section has anything to
// show at all without duplicating these thresholds/formatting itself.
export function subjectDetailChips(subject, extent) {
  const chips = []
  if (extent) chips.push(extent)

  const gear = gearLabel(subject?.gear)
  if (gear) chips.push(gear)

  if (typeof subject?.length_m === 'number') chips.push(`${subject.length_m}m long`)

  const steeringDeg = subject?.steering_deg
  // deadbanded - a few degrees of steering noise during ordinary
  // straight-line driving isn't worth a chip, only a deliberate turn is
  if (typeof steeringDeg === 'number' && Math.abs(steeringDeg) > 3) {
    const direction = steeringDeg > 0 ? 'right' : 'left'
    chips.push(`Steering ${direction} ${Math.round(Math.abs(steeringDeg))}°`)
  }

  const accelMps2 = subject?.accel_mps2
  // same idea - steady-state cruising accel is noise, only a real accel/brake event is worth a chip
  if (typeof accelMps2 === 'number' && Math.abs(accelMps2) > 1) {
    const verb = accelMps2 > 0 ? 'Accelerating' : 'Braking'
    chips.push(`${verb} ${Math.abs(accelMps2).toFixed(1)} m/s²`)
  }

  return chips
}
