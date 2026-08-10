<script setup>
// Small inline-SVG icon set keyed by backend `category`, no external icon
// library needed. Falls back to a generic warning triangle for anything
// unrecognized so the header never renders blank.
defineProps({
  category: { type: String, default: null },
  size: { type: Number, default: 22 },
})
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <!-- vehicle: body + two wheels -->
    <g v-if="category === 'vehicle'" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">
      <path d="M3.5 15.5l1.4-4.8A2 2 0 0 1 6.8 9.3h10.4a2 2 0 0 1 1.9 1.4l1.4 4.8" fill="none" />
      <rect x="2.5" y="15.5" width="19" height="3.4" rx="1.2" fill="none" />
      <circle cx="7" cy="19.3" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="17" cy="19.3" r="1.5" fill="currentColor" stroke="none" />
    </g>

    <!-- pedestrian: head + body -->
    <g v-else-if="category === 'pedestrian'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <circle cx="12" cy="5.5" r="2.1" fill="currentColor" stroke="none" />
      <path d="M12 8.4v5.6M12 14l-3 6M12 14l3 6M8.7 11.3L12 9.6l3.3 1.7" />
    </g>

    <!-- weather: cloud + rain -->
    <g v-else-if="category === 'weather'" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M6.5 14.5a3.5 3.5 0 0 1 .4-6.98A4.5 4.5 0 0 1 15.3 9.5a3.2 3.2 0 0 1-.8 6.3H7a3 3 0 0 1-.5-1.3z" />
      <path d="M9 18l-1 2M13 18l-1 2M17 17l-1 2" />
    </g>

    <!-- road hazard: cone-ish triangle with a band -->
    <g v-else-if="category === 'road_hazard'" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" fill="none">
      <path d="M12 3.5l6 16.5H6l6-16.5z" />
      <path d="M8.6 15h6.8" />
    </g>

    <!-- default / 'other': classic warning triangle with exclamation -->
    <g v-else stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" fill="none">
      <path d="M12 3.2l9.5 17.1H2.5L12 3.2z" />
      <path d="M12 9.6v4.2" />
      <circle cx="12" cy="16.9" r="0.15" fill="currentColor" stroke="currentColor" stroke-width="1.4" />
    </g>
  </svg>
</template>
