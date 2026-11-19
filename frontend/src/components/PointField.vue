<script setup lang="ts">
import { ref } from 'vue'

import { geocodeApi, type PlaceResult } from '@/api/endpoints'
import { useMapContext } from '@/composables/mapContext'

export interface Point {
  lat: number
  lng: number
  label: string
}

/** A start or end point: my position, a point dragged on the map, or an address (searched on submit). */
const props = defineProps<{ legend: string }>()
const point = defineModel<Point | null>({ required: true })

const mapContext = useMapContext()
const query = ref('')
const results = ref<PlaceResult[]>([])
const message = ref<string | null>(null)
const searching = ref(false)

const round = (value: number) => Number(value.toFixed(6))

async function labelFor(lat: number, lng: number, fallback: string) {
  try {
    const address = await geocodeApi.reverse(lat, lng)
    return [address.address1, address.city].filter(Boolean).join(', ') || fallback
  } catch {
    return fallback
  }
}

async function useMyPosition() {
  message.value = null
  const position = mapContext.userPosition.value
  if (!position) {
    message.value = 'Position indisponible : autorisez la géolocalisation ou choisissez sur la carte.'
    return
  }
  point.value = { lat: round(position.lat), lng: round(position.lng), label: 'Ma position' }
}

async function pickOnMap() {
  message.value = null
  const initial = point.value ?? mapContext.center()
  const picked = await mapContext.pickLocation(initial, `${props.legend} : déplacez le repère puis validez.`)
  if (!picked) return
  point.value = { lat: round(picked.lat), lng: round(picked.lng), label: 'Point sur la carte' }
  point.value = { ...point.value, label: await labelFor(picked.lat, picked.lng, 'Point sur la carte') }
}

// Nominatim's policy forbids searching as the user types: only on submit.
async function search() {
  const text = query.value.trim()
  if (!text) return
  message.value = null
  searching.value = true
  try {
    results.value = await geocodeApi.search(text, mapContext.center())
    if (!results.value.length) message.value = 'Aucune adresse trouvée.'
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  } finally {
    searching.value = false
  }
}

function choose(place: PlaceResult) {
  point.value = { lat: round(place.lat), lng: round(place.lng), label: place.label }
  results.value = []
  query.value = ''
}
</script>

<template>
  <fieldset class="point">
    <legend>{{ legend }}</legend>
    <p v-if="point" class="point__current">{{ point.label }}</p>
    <p v-else class="muted point__current">Pas encore choisi</p>
    <div class="point__actions">
      <button type="button" class="btn" @click="useMyPosition">Ma position</button>
      <button type="button" class="btn" @click="pickOnMap">Sur la carte</button>
    </div>
    <form class="point__search" @submit.prevent="search">
      <input v-model="query" class="input" type="search" placeholder="Adresse, quartier, lieu…" :aria-label="`${legend} : adresse`" />
      <button type="submit" class="btn" :disabled="searching || !query.trim()">Chercher</button>
    </form>
    <ul v-if="results.length" class="point__results">
      <li v-for="place in results" :key="`${place.lat},${place.lng}`">
        <button type="button" @click="choose(place)">{{ place.label }}</button>
      </li>
    </ul>
    <p v-if="message" class="muted point__message">{{ message }}</p>
  </fieldset>
</template>

<style scoped>
.point {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  border: none;
}

.point legend {
  margin-bottom: 4px;
  font-size: 0.85rem;
  color: var(--muted);
}

.point__current {
  margin: 0;
  font-weight: 500;
}

.point__actions,
.point__search {
  display: flex;
  gap: 8px;
}

.point__actions .btn {
  flex: 1;
}

.point__results {
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.point__results button {
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-bottom: 1px solid var(--border);
  background: none;
  text-align: left;
  cursor: pointer;
}

.point__results li:last-child button {
  border-bottom: none;
}

.point__message {
  margin: 0;
  font-size: 0.85rem;
}
</style>
