<script setup lang="ts">
// Minimal stroke icon set (24x24 grid), so no icon library is needed.
const PATHS = {
  map: 'M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Zm0 0v14m6-12v14',
  team: 'M16 19v-1a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v1M9 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm13 9v-1a4 4 0 0 0-3-3.9M16 4.1a3 3 0 0 1 0 5.8',
  locate: 'M12 2v3m0 14v3M2 12h3m14 0h3m-10 6a6 6 0 1 0 0-12 6 6 0 0 0 0 12Zm0-4a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z',
  search: 'm21 21-4.3-4.3M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z',
  filter: 'M3 5h18l-7 8v6l-4 2v-8L3 5Z',
  plus: 'M12 5v14M5 12h14',
  close: 'M18 6 6 18M6 6l12 12',
  check: 'M20 6 9 17l-5-5',
  edit: 'M4 20h4L19 9l-4-4L4 16v4Zm9-13 4 4',
  move: 'M12 2v20M2 12h20M12 2l-3 3m3-3 3 3m-3 17-3-3m3 3 3-3M2 12l3-3m-3 3 3 3m17-3-3-3m3 3-3 3',
  route: 'M3 11 21 3l-8 18-2-8-8-2Z',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9',
  copy: 'M9 9h11v11H9V9Zm-4 6H4V4h11v1',
  trash: 'M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6',
  back: 'M15 18 9 12l6-6',
  forward: 'm9 18 6-6-6-6',
  camera: 'M3 8h4l2-3h6l2 3h4v11H3V8Zm9 9a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
  pin: 'M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11Zm0-8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  key: 'M15 7a2 2 0 1 0 0 .01M21 8a5 5 0 0 1-6.8 4.7L12 15h-2v2H8v2H4v-3.5l7.3-7.3A5 5 0 1 1 21 8Z',
  image: 'M4 5h16v14H4V5Zm0 10 4-4 5 5m-2-2 3-3 6 6M15 9h.01',
  grid: 'M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z',
  chart: 'M4 20V10m6 10V4m6 16v-7m4 7H2',
  rotate: 'M21 12a9 9 0 1 1-3-6.7L21 8m0-5v5h-5',
  sun: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0-14v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
  cluster: 'M7 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm10 0a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm-5 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  flag: 'M5 21V4m0 0h11l-2 4 2 4H5',
  up: 'm6 15 6-6 6 6',
  down: 'm6 9 6 6 6-6',
  moon: 'M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z',
} as const

defineProps<{ name: keyof typeof PATHS; size?: number }>()
</script>

<template>
  <svg
    :width="size ?? 22"
    :height="size ?? 22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="PATHS[name]" />
  </svg>
</template>
