<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { statsApi } from '@/api/endpoints'
import type { MyStats, TeamStats } from '@/api/types'
import ProgressChart from '@/components/ProgressChart.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const numberFormat = new Intl.NumberFormat('fr-FR')

const mine = ref<MyStats | null>(null)
const team = ref<TeamStats | null>(null)
const error = ref<string | null>(null)
const showAllCities = ref(false)

onMounted(async () => {
  try {
    ;[mine.value, team.value] = await Promise.all([statsApi.me(), statsApi.team()])
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})

// Members who flashed at least one team invader, in the chart's (join) order.
const progressMembers = computed(() => (team.value?.timelines ?? []).filter((timeline) => timeline.points.length))

// A full city bar means 30 flashes (more stays full).
const CITY_BAR_FLASHES = 30

const PROGRESS_TABS = { points: 'Par points', flashes: 'Par flashs' } as const
const progressMetric = ref<keyof typeof PROGRESS_TABS>('points')

const BREAKDOWN_TABS = { city: 'Flashs par ville', points: 'Flashs par points' } as const
const breakdown = ref<keyof typeof BREAKDOWN_TABS>('city')

interface BreakdownRow {
  key: number
  label: string
  detail: string
  flashed: number
  total: number
  // Number of flashes that fills the bar.
  scale: number
}

// Cities without any flash of mine stay hidden until "Voir plus".
const visibleCities = computed(() => {
  const rows = mine.value?.by_city ?? []
  return showAllCities.value ? rows : rows.filter((row) => row.flashed > 0)
})

// Point values are few: all shown, each bar is the completion of that value.
const breakdownRows = computed<BreakdownRow[]>(() => {
  if (breakdown.value === 'points') {
    return (mine.value?.by_points ?? []).map((row) => ({
      key: row.points,
      label: `${row.points} pt${row.points > 1 ? 's' : ''}`,
      detail: '',
      flashed: row.flashed,
      total: row.total,
      scale: row.total,
    }))
  }
  return visibleCities.value.map((row) => ({
    key: row.city.id,
    label: row.city.name,
    detail: row.country,
    flashed: row.flashed,
    total: row.total,
    scale: CITY_BAR_FLASHES,
  }))
})
const hiddenRows = computed(() =>
  breakdown.value === 'city' ? (mine.value?.by_city.length ?? 0) - visibleCities.value.length : 0,
)

const myRank = computed(() => {
  const index = team.value?.ranking.findIndex((row) => row.user.id === auth.me?.id) ?? -1
  return index === -1 ? null : index + 1
})
</script>

<template>
  <div class="page stats">
    <h1>Statistiques</h1>

    <p v-if="error" class="errors">{{ error }}</p>
    <p v-else-if="!mine || !team" class="muted">Chargement…</p>

    <div v-else class="stats__layout">
      <section class="card stats__hero">
        <span class="stats__label">Mon score</span>
        <span class="stats__hero-value">
          {{ numberFormat.format(mine.points) }}<template v-if="mine.points_from_app">*</template>
        </span>
        <span class="muted">points</span>
      </section>

      <div class="stats__tiles">
        <div class="card stats__tile">
          <span class="stats__label">Flashs</span>
          <span class="stats__value">{{ numberFormat.format(mine.flashes) }}<small class="muted"> / {{ numberFormat.format(mine.team_invaders) }}</small></span>
        </div>
        <div class="card stats__tile">
          <span class="stats__label">Villes ouvertes</span>
          <span class="stats__value">{{ mine.cities }}<small class="muted"> / {{ numberFormat.format(mine.team_cities) }}</small></span>
        </div>
        <div class="card stats__tile">
          <span class="stats__label">Classement équipe</span>
          <span class="stats__value">{{ myRank ?? '—' }}<small v-if="myRank" class="muted"> / {{ team.ranking.length }}</small></span>
        </div>
      </div>

      <section class="card stats__section stats__progress">
        <h2>Progression</h2>
        <div class="stats__tabs" role="tablist" aria-label="Progression de l'équipe">
          <button
            v-for="(label, key) in PROGRESS_TABS"
            :key="key"
            type="button"
            role="tab"
            class="stats__tab"
            :aria-selected="progressMetric === key"
            @click="progressMetric = key"
          >
            {{ label }}
          </button>
        </div>
        <p v-if="!progressMembers.length" class="muted">Pas encore de flash : la progression de l'équipe apparaîtra ici.</p>
        <ProgressChart v-else role="tabpanel" :timelines="team.timelines" :me-id="auth.me?.id" :metric="progressMetric" />
        <small v-if="progressMembers.length" class="muted">Invaders présents sur la carte de l'équipe uniquement.</small>
      </section>

      <section class="card stats__section stats__breakdown">
        <div class="stats__tabs" role="tablist" aria-label="Répartition des flashs">
          <button
            v-for="(label, key) in BREAKDOWN_TABS"
            :key="key"
            type="button"
            role="tab"
            class="stats__tab"
            :aria-selected="breakdown === key"
            @click="breakdown = key"
          >
            {{ label }}
          </button>
        </div>
        <p v-if="!breakdownRows.length && !hiddenRows" class="muted">Aucun invader pour l'instant.</p>
        <ul v-else-if="breakdownRows.length" class="stats__cities" role="tabpanel">
          <li v-for="row in breakdownRows" :key="row.key">
            <div class="stats__city-text">
              <span>{{ row.label }} <small class="muted">{{ row.detail }}</small></span>
              <span class="stats__num">
                {{ row.flashed }} flash{{ row.flashed > 1 ? 's' : '' }} <small class="muted">/ {{ row.total }}</small>
              </span>
            </div>
            <div
              class="stats__meter"
              role="meter"
              :aria-valuenow="Math.min(row.flashed, row.scale)"
              aria-valuemin="0"
              :aria-valuemax="row.scale"
              :aria-label="`Flashs : ${row.label}`"
            >
              <span class="stats__meter-fill" :style="{ width: `${Math.min(row.flashed / row.scale, 1) * 100}%` }" />
            </div>
          </li>
        </ul>
        <p v-else class="muted">Aucun flash pour l'instant.</p>
        <button v-if="breakdown === 'city' && (hiddenRows || showAllCities)" type="button" class="stats__more" @click="showAllCities = !showAllCities">
          {{ showAllCities ? 'Voir moins' : `Voir plus (${hiddenRows} ville${hiddenRows > 1 ? 's' : ''} sans flash)` }}
        </button>
        <small class="muted">Les invaders détruits ne comptent que si vous les aviez flashés.</small>
      </section>

      <section class="card stats__section stats__ranking">
        <h2>Classement de l'équipe</h2>
        <table class="stats__table">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Membre</th>
              <th scope="col" class="stats__num">Flashs</th>
              <th scope="col" class="stats__num">Points</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in team.ranking"
              :key="row.user.id"
              :class="{ 'stats__me': row.user.id === auth.me?.id }"
            >
              <td>{{ index + 1 }}</td>
              <td>{{ row.user.display_name }}<template v-if="row.user.id === auth.me?.id"> (vous)</template></td>
              <td class="stats__num">{{ numberFormat.format(row.flashes) }}</td>
              <td class="stats__num">{{ numberFormat.format(row.points) }}<template v-if="row.points_from_app">*</template></td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
    <small class="muted">* Données provenant de l'app Flash Invaders (compte synchronisé).</small>
  </div>
</template>

<style scoped>
.stats {
  max-width: 960px;
}

.stats__layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Desktop (gallery width): score | tiles, progression, breakdown | ranking. */
@media (min-width: 768px) {
  .stats__layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    grid-template-areas:
      'hero tiles'
      'progress progress'
      'breakdown ranking';
    align-items: start;
  }

  .stats__hero {
    grid-area: hero;
    align-self: stretch;
    justify-content: center;
  }

  .stats__tiles {
    grid-area: tiles;
    align-self: stretch;
  }

  .stats__progress {
    grid-area: progress;
  }

  .stats__breakdown {
    grid-area: breakdown;
  }

  .stats__ranking {
    grid-area: ranking;
  }
}

.stats__hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stats__hero-value {
  font-size: 3.25rem;
  font-weight: 600;
  line-height: 1.1;
}

.stats__label {
  font-size: 0.85rem;
  color: var(--muted);
}

.stats__tiles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.stats__tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-align: center;
  padding: 12px;
  min-width: 0;
}

.stats__value {
  font-size: 1.5rem;
  font-weight: 600;
}

.stats__value small {
  font-size: 0.9rem;
  font-weight: 400;
}

.stats__section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats__section h2 {
  font-size: 1.05rem;
}

.stats__cities {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.stats__city-text {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.stats__tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 10px;
  background: var(--surface-2);
}

.stats__tab {
  flex: 1;
  min-height: 36px;
  padding: 6px 8px;
  border: 0;
  border-radius: 7px;
  background: none;
  color: var(--muted);
  font: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.stats__tab[aria-selected='true'] {
  background: var(--accent);
  color: var(--surface);
  box-shadow: 0 1px 2px rgb(0 0 0 / 15%);
}

.stats__more {
  align-self: flex-start;
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font: inherit;
  font-size: 0.85rem;
  text-decoration: underline;
  cursor: pointer;
}

.stats__meter {
  height: 8px;
  border-radius: 4px;
  background: var(--surface-2);
  overflow: hidden;
}

.stats__meter-fill {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: var(--accent);
}

.stats__num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stats__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.stats__table th {
  font-weight: 500;
  color: var(--muted);
  text-align: left;
  padding: 6px 4px;
  border-bottom: 1px solid var(--border);
}

.stats__table td {
  padding: 8px 4px;
  border-bottom: 1px solid var(--border);
}

.stats__table .stats__num {
  text-align: right;
}

.stats__me td {
  color: var(--accent);
  font-weight: 600;
}
</style>
