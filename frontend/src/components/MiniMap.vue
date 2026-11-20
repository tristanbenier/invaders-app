<script setup lang="ts">
import L from '@/lib/leaflet'
import '@maplibre/maplibre-gl-leaflet'
import 'maplibre-gl/dist/maplibre-gl.css'

import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'

import { basemapStyle } from '@/lib/basemap'
import { useAuthStore } from '@/stores/auth'

/** Small fixed map centred on one point (no dragging or zooming: "Voir sur la carte" opens the real one). */
const props = defineProps<{ lat: number; lng: number; label: string }>()

const ZOOM = 18
const auth = useAuthStore()
const element = ref<HTMLElement>()
const map = shallowRef<L.Map>()
let marker: L.Marker | undefined

onMounted(() => {
  const instance = L.map(element.value!, {
    center: [props.lat, props.lng],
    zoom: ZOOM,
    zoomControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
    touchZoom: false,
  })
  L.maplibreGL({ style: basemapStyle(auth.me?.map_theme ?? 'light'), interactive: false }).addTo(instance)
  marker = L.marker([props.lat, props.lng], {
    interactive: false,
    keyboard: false,
    icon: L.divIcon({ className: 'mini-map__pin', iconSize: [18, 18], iconAnchor: [9, 9] }),
  }).addTo(instance)
  map.value = instance
})

watch(
  () => [props.lat, props.lng] as const,
  ([lat, lng]) => {
    marker?.setLatLng([lat, lng])
    map.value?.setView([lat, lng], ZOOM)
  },
)

onBeforeUnmount(() => map.value?.remove())
</script>

<template>
  <div ref="element" class="mini-map" role="img" :aria-label="`Carte : position de ${label}`" />
</template>

<style scoped>
.mini-map {
  /* Square, as wide as the photo above it. */
  width: min(100%, 320px);
  aspect-ratio: 1;
  align-self: center;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  /* Below the modal's own layers: Leaflet panes use z-index up to 1000. */
  isolation: isolate;
}
</style>

<style>
/* Leaflet markers live outside the component scope. */
.mini-map__pin {
  border: 3px solid var(--surface);
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.5);
}
</style>
