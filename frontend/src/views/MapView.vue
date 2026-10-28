<script setup lang="ts">
import L from '@/lib/leaflet'
import 'leaflet.markercluster'

import { computed, onBeforeUnmount, onMounted, provide, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { PlaceResult } from '@/api/endpoints'
import type { Invader } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import BottomSheet from '@/components/BottomSheet.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import SearchBox from '@/components/SearchBox.vue'
import { type LatLng, MAP_CONTEXT } from '@/composables/mapContext'
import { useGeolocation } from '@/composables/useGeolocation'
import { isIssInvader, useIssPosition } from '@/composables/useIssPosition'
import { useAuthStore } from '@/stores/auth'
import { useFiltersStore } from '@/stores/filters'
import { useInvadersStore } from '@/stores/invaders'
import { usePlacesStore } from '@/stores/places'
import { useTeamStore } from '@/stores/team'

// OSM tiles relayed (and cached) by Django: browsers like Brave strip the Referer OSM requires.
const TILE_URL = import.meta.env.VITE_MAP_TILE_URL || '/tiles/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION =
  import.meta.env.VITE_MAP_TILE_ATTRIBUTION ||
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
const DEFAULT_VIEW = { center: [48.8566, 2.3522] as L.LatLngTuple, zoom: 13 }
// Last map view, restored on reload (per browser, nothing to sync).
const VIEW_STORAGE_KEY = 'invaders.mapView'

function savedView(): { center: L.LatLngTuple; zoom: number } | null {
  try {
    const view = JSON.parse(localStorage.getItem(VIEW_STORAGE_KEY) ?? 'null')
    if (view && [view.lat, view.lng, view.zoom].every(Number.isFinite)) return { center: [view.lat, view.lng], zoom: view.zoom }
  } catch {
    // Storage blocked or corrupted value: use the default view.
  }
  return null
}

function saveView(instance: L.Map) {
  const { lat, lng } = instance.getCenter()
  try {
    localStorage.setItem(VIEW_STORAGE_KEY, JSON.stringify({ lat, lng, zoom: instance.getZoom() }))
  } catch {
    // Storage unavailable (private mode): the view is simply not remembered.
  }
}

const route = useRoute()
const router = useRouter()
const invaders = useInvadersStore()
const filters = useFiltersStore()
const places = usePlacesStore()
const team = useTeamStore()
const geo = useGeolocation()
const auth = useAuthStore()

const mapElement = ref<HTMLElement>()
const map = shallowRef<L.Map>()
const showFilters = ref(false)
const toast = ref<string | null>(null)
const picking = ref<{ message: string; resolve: (point: LatLng | null) => void; marker: L.Marker } | null>(null)

let clusters: L.MarkerClusterGroup
let userMarker: L.CircleMarker | undefined
let accuracyCircle: L.Circle | undefined
let centeredOnUser = false
let toastTimer: ReturnType<typeof setTimeout> | undefined
let placeMarker: L.Marker | undefined
// SPACE2ISS follows the ISS: kept out of the clusters, which cannot move a marker.
let issMarker: L.Marker | undefined
const issInvader = computed(() => invaders.items.find(isIssInvader))
const iss = useIssPosition(computed(() => issInvader.value !== undefined))

const sheetOpen = computed(() => route.name !== 'map')
const mapTheme = computed(() => auth.me?.map_theme ?? 'light')

async function setMapTheme(theme: 'light' | 'dark') {
  try {
    await auth.setMapTheme(theme)
  } catch (error) {
    showToast(error instanceof Error ? error.message : String(error))
  }
}

function showToast(message: string) {
  toast.value = message
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = null), 4000)
}

function markerState(invader: Invader) {
  if (invader.status === 'destroyed') return 'destroyed'
  return invader.my_flashed_at ? 'flashed' : 'not-flashed'
}

function invaderIcon(invader: Invader, extraClass = '') {
  return L.divIcon({
    className: `pin pin--${markerState(invader)} ${extraClass}`.trim(),
    html: '<span class="pin__invader"></span>',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  })
}

function renderMarkers() {
  clusters.clearLayers()
  clusters.addLayers(
    invaders.items
      .filter((invader) => !isIssInvader(invader))
      .map((invader) =>
        L.marker([invader.lat, invader.lng], { icon: invaderIcon(invader), title: invader.name, keyboard: true }).on(
          'click',
          () => router.push({ name: 'invader', params: { id: invader.id } }),
        ),
      ),
  )
  renderIss()
}

/** SPACE2ISS at the live ISS position (its stored position until the first answer). */
function renderIss() {
  issMarker?.remove()
  issMarker = undefined
  const invader = issInvader.value
  if (!map.value || !invader) return
  const point = iss.position.value ?? invader
  issMarker = L.marker([point.lat, point.lng], {
    icon: invaderIcon(invader, 'pin--iss'),
    title: `${invader.name} — Station spatiale internationale`,
    keyboard: true,
    zIndexOffset: 1000,
  })
    .on('click', () => router.push({ name: 'invader', params: { id: invader.id } }))
    .addTo(map.value)
}

function renderUserPosition() {
  const position = geo.position.value
  if (!map.value || !position) return
  const latLng: L.LatLngTuple = [position.lat, position.lng]
  if (!userMarker) {
    accuracyCircle = L.circle(latLng, { radius: position.accuracy, className: 'user-accuracy', interactive: false })
    userMarker = L.circleMarker(latLng, { radius: 8, className: 'user-position', interactive: false })
    accuracyCircle.addTo(map.value)
    userMarker.addTo(map.value)
  } else {
    userMarker.setLatLng(latLng)
    accuracyCircle?.setLatLng(latLng).setRadius(position.accuracy)
  }
  // Center on the user once, unless they opened an invader directly.
  if (!centeredOnUser && !sheetOpen.value) {
    centeredOnUser = true
    map.value.setView(latLng, 16)
  }
}

function locate() {
  geo.start()
  if (geo.error.value) return showToast(geo.error.value)
  const position = geo.position.value
  if (position) map.value?.flyTo([position.lat, position.lng], Math.max(map.value.getZoom(), 16))
  else showToast('Recherche de votre position…')
}

function addHere() {
  const position = geo.position.value ?? map.value?.getCenter()
  if (!position) return
  router.push({ name: 'invader-new', query: { lat: position.lat.toFixed(6), lng: position.lng.toFixed(6) } })
}

function mapCenter() {
  const center = map.value?.getCenter()
  return center ? { lat: center.lat, lng: center.lng } : { lat: DEFAULT_VIEW.center[0], lng: DEFAULT_VIEW.center[1] }
}

/** Address picked in the search box: center on it and drop a temporary pin. */
function showPlace(place: PlaceResult) {
  if (!map.value) return
  placeMarker?.remove()
  const content = document.createElement('div')
  content.className = 'place-popup'
  const label = document.createElement('p')
  label.textContent = place.label
  const add = document.createElement('button')
  add.type = 'button'
  add.className = 'btn btn--primary'
  add.textContent = 'Ajouter un invader ici'
  add.addEventListener('click', () => {
    placeMarker?.remove()
    router.push({ name: 'invader-new', query: { lat: place.lat.toFixed(6), lng: place.lng.toFixed(6) } })
  })
  content.append(label, add)

  placeMarker = L.marker([place.lat, place.lng], {
    icon: L.divIcon({ className: 'place-pin', iconSize: [18, 18], iconAnchor: [9, 9] }),
    keyboard: false,
  })
    .bindPopup(content, { closeButton: true, offset: [0, -6] })
    .on('popupclose', () => placeMarker?.remove())
    .addTo(map.value)
  if (route.name !== 'map') router.push({ name: 'map' })
  map.value.flyTo([place.lat, place.lng], 18, { duration: 0.6 })
  map.value.once('moveend', () => placeMarker?.openPopup())
}

function openInvader(invader: Invader) {
  router.push({ name: 'invader', params: { id: invader.id } })
}

function confirmPicking(confirmed: boolean) {
  if (!picking.value) return
  const { resolve, marker } = picking.value
  const point = marker.getLatLng()
  marker.remove()
  picking.value = null
  resolve(confirmed ? { lat: point.lat, lng: point.lng } : null)
}

provide(MAP_CONTEXT, {
  focus(point, zoom) {
    const instance = map.value
    if (!instance) return
    const targetZoom = zoom ?? Math.max(instance.getZoom(), 17)
    // Keep the point visible next to the sheet: above it on mobile, right of the side panel otherwise.
    const isMobile = window.innerWidth < 768
    const offset = L.point(isMobile ? 0 : -190, isMobile ? instance.getSize().y * 0.3 : 0)
    const center = instance.unproject(instance.project([point.lat, point.lng], targetZoom).add(offset), targetZoom)
    instance.flyTo(center, targetZoom, { duration: 0.6 })
  },
  pickLocation(initial, message) {
    if (picking.value) confirmPicking(false)
    return new Promise((resolve) => {
      const marker = L.marker([initial.lat, initial.lng], {
        draggable: true,
        autoPan: true,
        icon: L.divIcon({ className: 'pin pin--picking', html: '<span class="pin__invader"></span>', iconSize: [36, 36], iconAnchor: [18, 18] }),
      })
      marker.addTo(map.value!)
      map.value?.panTo([initial.lat, initial.lng])
      picking.value = { message, resolve, marker }
    })
  },
  userPosition: computed(() => geo.position.value),
  center: mapCenter,
})

onMounted(() => {
  const restored = savedView()
  // A remembered view wins over the first geolocation fix (the locate button still recenters).
  centeredOnUser = restored !== null
  const instance = L.map(mapElement.value!, { zoomControl: false, maxZoom: 19, ...(restored ?? DEFAULT_VIEW) })
  instance.on('moveend', () => saveView(instance))
  L.tileLayer(TILE_URL, {
    attribution: TILE_ATTRIBUTION,
    maxZoom: 19,
    className: 'map-tiles',
  }).addTo(instance)
  clusters = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
    maxClusterRadius: 50,
    disableClusteringAtZoom: 17,
    iconCreateFunction: (cluster) =>
      L.divIcon({ className: 'cluster', html: `<span>${cluster.getChildCount()}</span>`, iconSize: [40, 40] }),
  }).addTo(instance)
  // Long press on touch screens, right click with a mouse.
  instance.on('contextmenu', (event: L.LeafletMouseEvent) => {
    if (picking.value) return
    router.push({ name: 'invader-new', query: { lat: event.latlng.lat.toFixed(6), lng: event.latlng.lng.toFixed(6) } })
  })
  map.value = instance

  renderMarkers()
  geo.start()
  invaders.load()
  places.load()
  team.load()
})

onBeforeUnmount(() => {
  if (picking.value) confirmPicking(false)
  issMarker?.remove()
  map.value?.remove()
  clearTimeout(toastTimer)
})

watch(() => invaders.items, renderMarkers)
watch(iss.position, (point) => point && issMarker?.setLatLng([point.lat, point.lng]))
watch(geo.position, renderUserPosition)
watch(
  () => invaders.error,
  (error) => error && showToast(error),
)
</script>

<template>
  <div class="map-view" :class="[`map-view--${mapTheme}`, { 'map-view--picking': picking }]">
    <div ref="mapElement" class="map-view__map" />

    <div class="map-view__top">
      <SearchBox :near="mapCenter" @select="openInvader" @select-place="showPlace" />
      <button
        type="button"
        class="btn btn--icon map-view__control"
        :class="{ 'map-view__control--active': filters.activeCount }"
        aria-label="Filtres"
        @click="showFilters = !showFilters"
      >
        <AppIcon name="filter" />
        <span v-if="filters.activeCount" class="badge">{{ filters.activeCount }}</span>
      </button>
    </div>

    <div v-if="!sheetOpen && !picking" class="map-view__actions">
      <div class="theme-switch" role="group" aria-label="Thème de la carte">
        <button
          type="button"
          class="theme-switch__option"
          :aria-pressed="mapTheme === 'light'"
          aria-label="Carte claire"
          title="Carte claire"
          @click="setMapTheme('light')"
        >
          <AppIcon name="sun" :size="20" />
        </button>
        <button
          type="button"
          class="theme-switch__option"
          :aria-pressed="mapTheme === 'dark'"
          aria-label="Carte sombre"
          title="Carte sombre"
          @click="setMapTheme('dark')"
        >
          <AppIcon name="moon" :size="20" />
        </button>
      </div>
      <button type="button" class="btn btn--icon map-view__control" aria-label="Me localiser" @click="locate">
        <AppIcon name="locate" />
      </button>
      <button type="button" class="btn btn--primary map-view__add" @click="addHere">
        <AppIcon name="plus" />
        Ajouter
      </button>
    </div>

    <div v-if="picking" class="map-view__picking card">
      <p>{{ picking.message }}</p>
      <div class="map-view__picking-actions">
        <button type="button" class="btn" @click="confirmPicking(false)">Annuler</button>
        <button type="button" class="btn btn--primary" @click="confirmPicking(true)">Valider</button>
      </div>
    </div>

    <p v-if="invaders.loading" class="map-view__status">Chargement…</p>
    <p v-if="toast" class="map-view__toast" role="status">{{ toast }}</p>

    <BottomSheet v-if="showFilters && !picking" title="Filtres" @close="showFilters = false">
      <FilterPanel />
    </BottomSheet>

    <!-- Child routes (invader sheet, form) stay mounted while picking a location, only hidden. -->
    <div v-show="!picking && !showFilters">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.map-view {
  position: absolute;
  inset: 0;
}

.map-view__map {
  position: absolute;
  inset: 0;
}

.map-view__top {
  position: absolute;
  top: calc(12px + env(safe-area-inset-top));
  left: 12px;
  right: 12px;
  display: flex;
  gap: 8px;
  z-index: 1001;
}

.map-view__control {
  position: relative;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.map-view__control--active {
  color: var(--accent);
}

.map-view__actions {
  position: absolute;
  right: 12px;
  bottom: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  z-index: 1000;
}

.theme-switch {
  display: flex;
  flex-direction: column;
  padding: 3px;
  gap: 3px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.theme-switch__option {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}

.theme-switch__option[aria-pressed='true'] {
  background: var(--surface-2);
  color: var(--accent);
}

.map-view__add {
  box-shadow: var(--shadow);
  border-radius: 999px;
  padding: 12px 20px;
}

.map-view__picking {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 16px;
  z-index: 1001;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow);
}

.map-view__picking p {
  margin: 0;
}

.map-view__picking-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.map-view__status,
.map-view__toast {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  margin: 0;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--surface-2);
  box-shadow: var(--shadow);
  font-size: 0.85rem;
  z-index: 1002;
  white-space: nowrap;
}

.map-view__status {
  top: calc(68px + env(safe-area-inset-top));
}

.map-view__toast {
  bottom: 90px;
  max-width: calc(100% - 24px);
  white-space: normal;
  text-align: center;
}

@media (min-width: 768px) {
  .map-view__top {
    left: auto;
    width: 420px;
  }

  .map-view__picking {
    left: auto;
    width: 380px;
  }
}
</style>

<style>
/* Standard OSM tiles, toned down (light) or inverted (dark). */
.map-view--light .map-tiles {
  filter: grayscale(0.85) brightness(1.04) contrast(0.92);
}

.map-view--dark .map-tiles {
  filter: invert(1) hue-rotate(180deg) brightness(0.9) contrast(0.9) saturate(0.6);
}

.map-view--light .leaflet-container {
  background: #f2f2f0;
}

/* Leaflet markers live outside the component scope. */
.pin {
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--surface);
  border: 2px solid currentColor;
  box-shadow: 0 2px 6px rgb(0 0 0 / 0.5);
}

.pin__invader {
  width: 60%;
  height: 60%;
  background: currentColor;
  mask: url('@/assets/invader.svg') center / contain no-repeat;
}

.pin--flashed {
  color: var(--flashed);
}

.pin--not-flashed {
  color: var(--not-flashed);
}

.pin--destroyed {
  color: var(--destroyed);
  opacity: 0.7;
}

.pin--picking {
  color: var(--warning);
  animation: pin-pulse 1.2s ease-in-out infinite;
}

@keyframes pin-pulse {
  50% {
    box-shadow: 0 0 0 8px rgb(255 199 95 / 0.25);
  }
}

/* SPACE2ISS, moving with the ISS: a halo tells it apart from fixed invaders. */
.pin--iss {
  animation: pin-orbit 2.5s ease-in-out infinite;
}

@keyframes pin-orbit {
  50% {
    box-shadow: 0 0 0 8px rgb(90 170 255 / 0.35);
  }
}

.cluster {
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgb(31 28 46 / 0.9);
  border: 2px solid var(--accent);
  color: var(--text);
  font-weight: 700;
  font-size: 0.85rem;
}

.user-position {
  fill: #4c8dff;
  fill-opacity: 1;
  stroke: #fff;
  stroke-width: 3;
}

.place-pin {
  border-radius: 50%;
  background: var(--warning);
  border: 3px solid #fff;
  box-shadow: 0 2px 6px rgb(0 0 0 / 0.5);
}

.place-popup {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 180px;
}

.place-popup p {
  margin: 0;
  font-weight: 600;
}

/* Leaflet popups, in the app's dark style. */
.leaflet-popup-content-wrapper,
.leaflet-popup-tip {
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow);
}

.leaflet-popup-content {
  margin: 14px 16px;
  font-size: 0.9rem;
}

.leaflet-container a.leaflet-popup-close-button {
  color: var(--muted);
}

.user-accuracy {
  fill: #4c8dff;
  fill-opacity: 0.12;
  stroke: #4c8dff;
  stroke-opacity: 0.4;
  stroke-width: 1;
}
</style>
