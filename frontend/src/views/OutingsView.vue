<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { outingsApi } from '@/api/endpoints'
import { type Outing, TRANSPORT_LABELS } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import BottomSheet from '@/components/BottomSheet.vue'
import { formatDate, formatDuration } from '@/composables/format'
import { useOutingStore } from '@/stores/outing'

const router = useRouter()
const outing = useOutingStore()
const outings = ref<Outing[] | null>(null)
const error = ref<string | null>(null)

/** Points of the route's invaders: all of them, or only those already flashed. */
const points = (item: Outing, doneOnly = false) =>
  item.stops.filter((stop) => !doneOnly || stop.done).reduce((sum, stop) => sum + stop.invader.points, 0)

onMounted(async () => {
  try {
    outings.value = await outingsApi.list()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})
</script>

<template>
  <BottomSheet title="Sorties" @close="router.push({ name: 'map' })">
    <div class="outings">
      <RouterLink :to="{ name: 'outing-new' }" class="btn btn--primary btn--block">
        <AppIcon name="plus" />
        Nouvelle sortie
      </RouterLink>

      <p v-if="error" class="errors">{{ error }}</p>
      <p v-else-if="!outings" class="muted">Chargement…</p>
      <p v-else-if="!outings.length" class="muted">
        Préparez un parcours : départ, durée et moyen de transport. Il sera visible par toute l'équipe.
      </p>
      <ul v-else class="outings__list">
        <li v-for="item in outings" :key="item.id">
          <RouterLink :to="{ name: 'outing', params: { id: item.id } }" class="outings__item">
            <span class="outings__name">
              {{ item.name }}
              <small v-if="item.id === outing.activeId" class="outings__active">Sur la carte</small>
            </span>
            <small class="muted">
              {{ TRANSPORT_LABELS[item.mode] }} · {{ formatDuration(item.duration_minutes) }} · {{ item.stops.length }} invaders
              · {{ points(item, true) }} / {{ points(item) }} pts
            </small>
            <small class="muted">
              {{ item.participant_names.map((member) => member.display_name).join(', ') }} · {{ formatDate(item.created_at) }}
            </small>
          </RouterLink>
        </li>
      </ul>
    </div>
  </BottomSheet>
</template>

<style scoped>
.outings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.outings p {
  margin: 0;
}

.outings__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.outings__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 0;
  border-top: 1px solid var(--border);
  color: var(--text);
  text-decoration: none;
}

.outings__name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.outings__active {
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--accent);
  color: var(--accent-text);
  font-size: 0.7rem;
}
</style>
