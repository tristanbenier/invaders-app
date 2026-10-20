<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { statsApi } from '@/api/endpoints'
import type { MyStats, TeamStats } from '@/api/types'
import ProgressChart from '@/components/ProgressChart.vue'
import { formatDate } from '@/composables/format'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const numberFormat = new Intl.NumberFormat('fr-FR')
const percentFormat = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 0 })

const mine = ref<MyStats | null>(null)
const team = ref<TeamStats | null>(null)
const error = ref<string | null>(null)
const showTable = ref(false)

onMounted(async () => {
  try {
    ;[mine.value, team.value] = await Promise.all([statsApi.me(), statsApi.team()])
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})

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

    <template v-else>
      <section class="card stats__hero">
        <span class="stats__label">Mon score</span>
        <span class="stats__hero-value">{{ numberFormat.format(mine.points) }}</span>
        <span class="muted">points</span>
      </section>

      <div class="stats__tiles">
        <div class="card stats__tile">
          <span class="stats__label">Flashs</span>
          <span class="stats__value">{{ numberFormat.format(mine.flashes) }}</span>
          <small class="muted">sur {{ numberFormat.format(mine.team_invaders) }} recensés</small>
        </div>
        <div class="card stats__tile">
          <span class="stats__label">Villes</span>
          <span class="stats__value">{{ mine.cities }}</span>
          <small class="muted">avec au moins un flash</small>
        </div>
        <div class="card stats__tile">
          <span class="stats__label">Classement</span>
          <span class="stats__value">{{ myRank ?? '—' }}<small v-if="myRank" class="muted"> / {{ team.ranking.length }}</small></span>
          <small class="muted">dans l'équipe</small>
        </div>
      </div>

      <section class="card stats__section">
        <header class="stats__section-header">
          <h2>Progression du score</h2>
          <button v-if="mine.timeline.length" type="button" class="btn stats__toggle" @click="showTable = !showTable">
            {{ showTable ? 'Voir le graphique' : 'Voir les données' }}
          </button>
        </header>
        <p v-if="!mine.timeline.length" class="muted">Pas encore de flash : votre progression apparaîtra ici.</p>
        <table v-else-if="showTable" class="stats__table">
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col" class="stats__num">Flashs</th>
              <th scope="col" class="stats__num">Points</th>
              <th scope="col" class="stats__num">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="point in [...mine.timeline].reverse()" :key="point.date">
              <td>{{ formatDate(point.date) }}</td>
              <td class="stats__num">{{ point.flashes }}</td>
              <td class="stats__num">+{{ point.points }}</td>
              <td class="stats__num">{{ numberFormat.format(point.cumulative_points) }}</td>
            </tr>
          </tbody>
        </table>
        <ProgressChart v-else :points="mine.timeline" />
      </section>

      <section class="card stats__section">
        <h2>Complétion par ville</h2>
        <p v-if="!mine.by_city.length" class="muted">Aucune ville pour l'instant.</p>
        <ul v-else class="stats__cities">
          <li v-for="row in mine.by_city" :key="row.city.id">
            <div class="stats__city-text">
              <span>{{ row.city.name }} <small class="muted">{{ row.country }}</small></span>
              <span class="stats__num">
                {{ row.flashed }} / {{ row.total }} · {{ percentFormat.format(row.flashed / row.total) }}
              </span>
            </div>
            <div
              class="stats__meter"
              role="meter"
              :aria-valuenow="row.flashed"
              aria-valuemin="0"
              :aria-valuemax="row.total"
              :aria-label="`Complétion à ${row.city.name}`"
            >
              <span class="stats__meter-fill" :style="{ width: `${(row.flashed / row.total) * 100}%` }" />
            </div>
          </li>
        </ul>
        <small class="muted">Les invaders détruits ne comptent que si vous les aviez flashés.</small>
      </section>

      <section class="card stats__section">
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
              <td class="stats__num">{{ numberFormat.format(row.points) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>

<style scoped>
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
  gap: 2px;
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

.stats__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stats__toggle {
  flex-shrink: 0;
  white-space: nowrap;
  min-height: 36px;
  padding: 6px 12px;
  font-size: 0.85rem;
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
