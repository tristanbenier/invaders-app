<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { invadersApi } from '@/api/endpoints'
import { type Invader, STATUS_LABELS } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import { distanceMeters, formatDistance } from '@/composables/distance'
import { useGeolocation } from '@/composables/useGeolocation'
import { usePlacesStore } from '@/stores/places'

// Destroyed invaders cannot be flashed anymore.
const FLASHABLE_STATUSES = 'ok,degraded,hidden,unknown'

interface Row {
  invader: Invader
  distance: number | null
}

interface Group {
  cityId: number
  cityName: string
  country: string
  rows: Row[]
  points: number
  nearest: number | null
}

const places = usePlacesStore()
const geo = useGeolocation()

const invaders = ref<Invader[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const cityFilter = ref<number | null>(null)

onMounted(async () => {
  geo.start()
  try {
    const [list] = await Promise.all([
      invadersApi.list({ flashed: 'false', status: FLASHABLE_STATUSES }),
      places.load(),
    ])
    invaders.value = list
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
})

const groups = computed<Group[]>(() => {
  const position = geo.position.value
  const byCity = new Map<number, Group>()
  for (const invader of invaders.value) {
    if (cityFilter.value !== null && invader.city !== cityFilter.value) continue
    let group = byCity.get(invader.city)
    if (!group) {
      const city = places.cityById.get(invader.city)
      const country = places.countries.find((c) => c.id === city?.country)
      group = { cityId: invader.city, cityName: city?.name ?? '—', country: country?.name ?? '', rows: [], points: 0, nearest: null }
      byCity.set(invader.city, group)
    }
    const distance = position ? distanceMeters(position, invader) : null
    group.rows.push({ invader, distance })
    group.points += invader.points
    if (distance !== null && (group.nearest === null || distance < group.nearest)) group.nearest = distance
  }

  const byDistanceThenName = (a: number | null, b: number | null, nameA: string, nameB: string) =>
    a !== null && b !== null ? a - b : nameA.localeCompare(nameB, 'fr', { numeric: true })

  const sorted = [...byCity.values()]
  for (const group of sorted) {
    group.rows.sort((a, b) => byDistanceThenName(a.distance, b.distance, a.invader.name, b.invader.name))
  }
  return sorted.sort((a, b) => byDistanceThenName(a.nearest, b.nearest, a.cityName, b.cityName))
})

const total = computed(() => groups.value.reduce((sum, group) => sum + group.rows.length, 0))
const totalPoints = computed(() => groups.value.reduce((sum, group) => sum + group.points, 0))
const cities = computed(() => {
  const ids = new Set(invaders.value.map((invader) => invader.city))
  return places.cities.filter((city) => ids.has(city.id))
})
</script>

<template>
  <div class="page to-flash">
    <header>
      <h1>À flasher</h1>
      <p class="muted">
        <template v-if="!loading">{{ total }} invader{{ total > 1 ? 's' : '' }} · {{ totalPoints }} points à gagner</template>
        <template v-else>&nbsp;</template>
      </p>
    </header>

    <div class="to-flash__toolbar">
      <label class="field to-flash__city">
        <span>Ville</span>
        <select v-model="cityFilter" class="input">
          <option :value="null">Toutes</option>
          <option v-for="city in cities" :key="city.id" :value="city.id">{{ city.name }}</option>
        </select>
      </label>
      <p class="to-flash__location muted">
        <AppIcon name="locate" :size="16" />
        <template v-if="geo.position.value">Triés par distance</template>
        <template v-else-if="geo.error.value">{{ geo.error.value }}</template>
        <template v-else>Recherche de votre position…</template>
      </p>
    </div>

    <p v-if="error" class="errors">{{ error }}</p>
    <p v-else-if="loading" class="muted">Chargement…</p>
    <p v-else-if="!groups.length" class="card muted">Rien à flasher ici : tout est flashé !</p>

    <section v-for="group in groups" :key="group.cityId" class="card to-flash__group">
      <header class="to-flash__group-header">
        <div>
          <h2>{{ group.cityName }}</h2>
          <small class="muted">{{ group.country }}</small>
        </div>
        <span class="muted">{{ group.rows.length }} · {{ group.points }} pts</span>
      </header>
      <ul class="to-flash__list">
        <li v-for="{ invader, distance } in group.rows" :key="invader.id">
          <RouterLink :to="{ name: 'invader', params: { id: invader.id } }" class="to-flash__row">
            <span class="to-flash__name">{{ invader.name }}</span>
            <span v-if="invader.status !== 'ok'" class="to-flash__status">{{ STATUS_LABELS[invader.status] }}</span>
            <span class="muted to-flash__points">{{ invader.points }} pts</span>
            <span class="to-flash__distance">{{ distance !== null ? formatDistance(distance) : '' }}</span>
          </RouterLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.to-flash header p {
  margin: 4px 0 0;
}

.to-flash__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.to-flash__city {
  min-width: 180px;
}

.to-flash__location {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 0.85rem;
}

.to-flash__group {
  padding: 12px 16px;
}

.to-flash__group-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.to-flash__group-header h2 {
  font-size: 1.05rem;
}

.to-flash__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.to-flash__row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  border-top: 1px solid var(--border);
  color: var(--text);
  text-decoration: none;
}

.to-flash__name {
  font-weight: 600;
}

.to-flash__status {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--warning);
  font-size: 0.75rem;
}

.to-flash__points {
  margin-left: auto;
  font-size: 0.85rem;
}

.to-flash__distance {
  min-width: 64px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
