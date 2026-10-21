<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { geocodeApi, invadersApi, type PlaceResult } from '@/api/endpoints'
import type { Invader } from '@/api/types'
import type { LatLng } from '@/composables/mapContext'
import { usePlacesStore } from '@/stores/places'

import AppIcon from './AppIcon.vue'

// near: point used to rank addresses (the map center).
const props = defineProps<{ near?: () => LatLng }>()
const emit = defineEmits<{ select: [invader: Invader]; selectPlace: [place: PlaceResult] }>()
const places = usePlacesStore()

const MIN_ADDRESS_LENGTH = 3
// Same loose format as the API search: "pa 123", "pa123", "PA-123", "pa_0123".
const LOOSE_NAME = /^([A-Z]+)[\s_-]*(\d+)$/

/** "PA_123" for any loose spelling of an invader name (leading zeros ignored), else null. */
function nameKey(text: string) {
  const match = LOOSE_NAME.exec(text.trim().toUpperCase())
  return match ? `${match[1]}_${Number(match[2])}` : null
}

const query = ref('')
const results = ref<Invader[]>([])
const open = ref(false)
const error = ref<string | null>(null)
const pending = ref(false)
// Addresses are only searched on demand: Nominatim forbids search-as-you-type.
const addressResults = ref<PlaceResult[] | null>(null)
const addressPending = ref(false)
const addressError = ref<string | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined
let requestId = 0
let addressRequestId = 0

const trimmed = computed(() => query.value.trim())
const canSearchAddress = computed(() => trimmed.value.length >= MIN_ADDRESS_LENGTH)

watch(query, (value) => {
  clearTimeout(timer)
  addressResults.value = null
  addressError.value = null
  addressPending.value = false
  addressRequestId++
  const search = value.trim()
  if (!search) {
    results.value = []
    pending.value = false
    return
  }
  pending.value = true
  timer = setTimeout(async () => {
    const current = ++requestId
    try {
      const page = await invadersApi.search(search)
      if (current === requestId) {
        results.value = page.results
        error.value = null
        open.value = true
      }
    } catch (e) {
      if (current === requestId) error.value = e instanceof Error ? e.message : String(e)
    } finally {
      if (current === requestId) pending.value = false
    }
  }, 250)
})

function reset() {
  query.value = ''
  results.value = []
  open.value = false
}

function select(invader: Invader) {
  emit('select', invader)
  reset()
}

function selectPlace(place: PlaceResult) {
  emit('selectPlace', place)
  reset()
}

async function searchAddress() {
  if (!canSearchAddress.value) return
  const current = ++addressRequestId
  addressPending.value = true
  addressError.value = null
  open.value = true
  try {
    const found = await geocodeApi.search(trimmed.value, props.near?.())
    if (current === addressRequestId) addressResults.value = found
  } catch (e) {
    if (current === addressRequestId) addressError.value = e instanceof Error ? e.message : String(e)
  } finally {
    if (current === addressRequestId) addressPending.value = false
  }
}

function submit() {
  // An exact invader name opens it; anything else is looked up as an address.
  const key = nameKey(trimmed.value)
  const exact = key ? results.value.find((invader) => nameKey(invader.name) === key) : undefined
  if (exact) return select(exact)
  if (addressResults.value?.length) return selectPlace(addressResults.value[0]!)
  if (canSearchAddress.value) return searchAddress()
  const [first] = results.value
  if (first) select(first)
}
</script>

<template>
  <form class="search" role="search" @submit.prevent="submit">
    <AppIcon name="search" class="search__icon" :size="18" />
    <input
      v-model="query"
      class="input search__input"
      type="search"
      enterkeyhint="search"
      placeholder="Invader ou adresse"
      autocomplete="off"
      aria-label="Rechercher un invader ou une adresse"
      @focus="open = true"
      @blur="open = false"
    />
    <div v-if="open && trimmed" class="search__results">
      <!-- mousedown fires before the input blur closes the list. -->
      <ul class="search__list" aria-label="Invaders">
        <li v-if="pending" class="search__empty">Recherche…</li>
        <li v-else-if="error" class="search__empty">{{ error }}</li>
        <li v-else-if="!results.length" class="search__empty">Aucun invader trouvé.</li>
        <li v-for="invader in results" :key="invader.id">
          <button type="button" class="search__result" @mousedown.prevent="select(invader)">
            <strong>{{ invader.name }}</strong>
            <span class="muted">{{ places.cityById.get(invader.city)?.name }}</span>
          </button>
        </li>
      </ul>

      <div v-if="canSearchAddress" class="search__addresses">
        <button
          v-if="addressResults === null && !addressPending && !addressError"
          type="button"
          class="search__result search__address-action"
          @mousedown.prevent="searchAddress"
        >
          <AppIcon name="map" :size="16" />
          <span>Rechercher l'adresse « {{ trimmed }} »</span>
        </button>
        <p v-else-if="addressPending" class="search__empty">Recherche de l'adresse…</p>
        <p v-else-if="addressError" class="search__empty">{{ addressError }}</p>
        <p v-else-if="!addressResults?.length" class="search__empty">Aucune adresse trouvée.</p>
        <ul v-else class="search__list" aria-label="Adresses">
          <li v-for="place in addressResults" :key="`${place.lat},${place.lng}`">
            <button type="button" class="search__result" @mousedown.prevent="selectPlace(place)">
              <span class="search__place">{{ place.label }}</span>
              <span class="muted search__tag">Adresse</span>
            </button>
          </li>
        </ul>
      </div>
    </div>
  </form>
</template>

<style scoped>
.search {
  position: relative;
  flex: 1;
}

.search__icon {
  position: absolute;
  left: 12px;
  top: 13px;
  color: var(--muted);
  pointer-events: none;
}

.search__input {
  padding-left: 38px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.search__results {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  max-height: min(60vh, 420px);
  overflow-y: auto;
  padding: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: var(--shadow);
}

.search__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.search__addresses {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid var(--border);
}

.search__result {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.search__result:hover,
.search__result:focus-visible {
  background: var(--surface-2);
}

.search__address-action {
  justify-content: flex-start;
  color: var(--accent);
}

.search__place {
  min-width: 0;
  overflow-wrap: anywhere;
}

.search__tag {
  flex-shrink: 0;
  font-size: 0.75rem;
}

.search__empty {
  margin: 0;
  padding: 10px 12px;
  color: var(--muted);
}
</style>
