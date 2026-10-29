<script setup lang="ts">
import { computed } from 'vue'

import { STATUS_LABELS, type Status } from '@/api/types'
import { useFiltersStore } from '@/stores/filters'
import { usePlacesStore } from '@/stores/places'
import { useTeamStore } from '@/stores/team'

const filters = useFiltersStore()
const places = usePlacesStore()
const team = useTeamStore()

const statuses = Object.entries(STATUS_LABELS) as [Status, string][]
// Point values used by Invader.
const POINT_VALUES = [10, 20, 30, 40, 50, 100]
const members = computed(() => team.team?.members ?? [])
const cities = computed(() =>
  places.cities.filter((city) => filters.state.country === null || city.country === filters.state.country),
)

function toggleStatus(status: Status) {
  const current = filters.state.statuses
  filters.state.statuses = current.includes(status) ? current.filter((s) => s !== status) : [...current, status]
}

function togglePoints(value: number) {
  const current = filters.state.points
  filters.state.points = current.includes(value) ? current.filter((p) => p !== value) : [...current, value]
}

function onCountryChange() {
  // Keep the city consistent with the selected country.
  const city = filters.state.city === null ? undefined : places.cityById.get(filters.state.city)
  if (city && filters.state.country !== null && city.country !== filters.state.country) filters.state.city = null
}
</script>

<template>
  <div class="filters">
    <fieldset class="filters__group">
      <legend>Mes flashs</legend>
      <div class="chips">
        <button
          v-for="[value, label] in [['all', 'Tous'], ['no', 'Non flashés'], ['yes', 'Flashés']] as const"
          :key="value"
          type="button"
          class="chip"
          :class="{ 'chip--active': filters.state.flashed === value }"
          @click="filters.state.flashed = value"
        >
          {{ label }}
        </button>
      </div>
    </fieldset>

    <fieldset class="filters__group">
      <legend>Statut</legend>
      <div class="chips">
        <button
          v-for="[value, label] in statuses"
          :key="value"
          type="button"
          class="chip"
          :class="{ 'chip--active': filters.state.statuses.includes(value) }"
          :aria-pressed="filters.state.statuses.includes(value)"
          @click="toggleStatus(value)"
        >
          {{ label }}
        </button>
      </div>
    </fieldset>

    <fieldset class="filters__group">
      <legend>Points</legend>
      <div class="chips">
        <button
          v-for="value in POINT_VALUES"
          :key="value"
          type="button"
          class="chip"
          :class="{ 'chip--active': filters.state.points.includes(value) }"
          :aria-pressed="filters.state.points.includes(value)"
          @click="togglePoints(value)"
        >
          {{ value }}
        </button>
      </div>
    </fieldset>

    <div class="filters__row">
      <label class="field">
        <span>Pays</span>
        <select v-model="filters.state.country" class="input" @change="onCountryChange">
          <option :value="null">Tous</option>
          <option v-for="country in places.countries" :key="country.id" :value="country.id">{{ country.name }}</option>
        </select>
      </label>
      <label class="field">
        <span>Ville</span>
        <select v-model="filters.state.city" class="input">
          <option :value="null">Toutes</option>
          <option v-for="city in cities" :key="city.id" :value="city.id">{{ city.name }}</option>
        </select>
      </label>
    </div>

    <div class="filters__row">
      <label class="field">
        <span>Flashé par</span>
        <select v-model="filters.state.flashedBy" class="input">
          <option :value="null">Peu importe</option>
          <option v-for="member in members" :key="member.id" :value="member.id">{{ member.display_name }}</option>
        </select>
      </label>
      <label class="field">
        <span>Non flashé par</span>
        <select v-model="filters.state.notFlashedBy" class="input">
          <option :value="null">Peu importe</option>
          <option v-for="member in members" :key="member.id" :value="member.id">{{ member.display_name }}</option>
        </select>
      </label>
    </div>

    <button type="button" class="btn btn--block" :disabled="!filters.activeCount" @click="filters.reset()">
      Réinitialiser les filtres
    </button>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filters__group {
  margin: 0;
  padding: 0;
  border: none;
}

.filters__group legend {
  margin-bottom: 6px;
  font-size: 0.85rem;
  color: var(--muted);
}

.filters__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
