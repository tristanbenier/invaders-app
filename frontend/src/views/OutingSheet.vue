<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { outingsApi } from '@/api/endpoints'
import { type Outing, TRANSPORT_LABELS } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import BottomSheet from '@/components/BottomSheet.vue'
import FieldErrors from '@/components/FieldErrors.vue'
import { formatDuration } from '@/composables/format'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'
import { useOutingStore } from '@/stores/outing'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const outingStore = useOutingStore()
const { errors, capture, clear } = useFormErrors()

const outing = ref<Outing | null>(null)
const busy = ref(false)
const copied = ref(false)

const shown = computed(() => outing.value !== null && outingStore.activeId === outing.value.id)
const canDelete = computed(() => outing.value?.created_by?.id === auth.me?.id || auth.isAdmin)
const doneCount = computed(() => outing.value?.stops.filter((stop) => stop.done).length ?? 0)

async function load(id: number) {
  outing.value = null
  clear()
  try {
    outing.value = await outingsApi.get(id)
  } catch (error) {
    capture(error)
  }
}

watch(() => Number(route.params.id), load, { immediate: true })

/** Runs a change, then keeps the sheet and the map in sync with its result. */
async function run(action: () => Promise<Outing>) {
  clear()
  busy.value = true
  try {
    outing.value = await action()
    outingStore.update(outing.value)
  } catch (error) {
    capture(error)
  } finally {
    busy.value = false
  }
}

const id = () => outing.value!.id
const replan = () => run(() => outingsApi.plan(id()))
const optimize = () => run(() => outingsApi.optimize(id()))
const saveStops = (ids: number[]) => run(() => outingsApi.update(id(), { stop_ids: ids }))

function move(index: number, delta: number) {
  const ids = outing.value!.stops.map((stop) => stop.invader.id)
  const [moved] = ids.splice(index, 1)
  ids.splice(index + delta, 0, moved!)
  saveStops(ids)
}

function removeStop(index: number) {
  saveStops(outing.value!.stops.filter((_, i) => i !== index).map((stop) => stop.invader.id))
}

function toggleMap() {
  if (shown.value) outingStore.hide()
  else {
    outingStore.show(outing.value!)
    router.push({ name: 'map' })
  }
}

async function share() {
  const url = `${window.location.origin}/outings/${id()}`
  try {
    await navigator.clipboard.writeText(url)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    window.prompt('Copiez le lien :', url)
  }
}

async function remove() {
  if (!window.confirm(`Supprimer la sortie « ${outing.value!.name} » pour toute l'équipe ?`)) return
  clear()
  busy.value = true
  try {
    await outingsApi.remove(id())
    if (shown.value) outingStore.hide()
    await router.replace({ name: 'outings' })
  } catch (error) {
    capture(error)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <BottomSheet :title="outing?.name ?? 'Sortie'" @close="router.push({ name: 'outings' })">
    <FieldErrors :messages="errors._ ?? []" />
    <p v-if="!outing && !errors._" class="muted">Chargement…</p>

    <div v-if="outing" class="outing">
      <p class="outing__summary">
        <strong>{{ outing.stops.length }} invaders</strong>
        · {{ TRANSPORT_LABELS[outing.mode] }} · ≈ {{ outing.estimate.distance_km.toLocaleString('fr-FR') }} km ·
        {{ formatDuration(outing.estimate.minutes) }} sur {{ formatDuration(outing.duration_minutes) }}
      </p>
      <p class="muted outing__meta">
        {{ outing.start_label || 'Départ' }} → {{ outing.is_loop ? 'retour au départ' : outing.end_label || 'Arrivée' }}<br />
        Avec {{ outing.participant_names.map((member) => member.display_name).join(', ') }}
        · {{ doneCount }} / {{ outing.stops.length }} flashés
      </p>

      <div class="tiles">
        <button type="button" class="btn btn--tile" :class="{ 'btn--primary': !shown }" @click="toggleMap">
          <AppIcon name="flag" /> <span>{{ shown ? 'Désactiver' : 'Activer' }}</span>
        </button>
        <button type="button" class="btn btn--tile" @click="share">
          <AppIcon :name="copied ? 'check' : 'copy'" /> <span>{{ copied ? 'Copié' : 'Partager' }}</span>
        </button>
        <button type="button" class="btn btn--tile" :disabled="busy" @click="replan">
          <AppIcon name="rotate" /> <span>Recalculer</span>
        </button>
        <button type="button" class="btn btn--tile" :disabled="busy || outing.stops.length < 2" @click="optimize">
          <AppIcon name="route" /> <span>Optimiser</span>
        </button>
      </div>

      <p v-if="!outing.stops.length" class="muted">
        Aucun invader à portée : allongez la durée, changez de point de départ ou de participants.
      </p>
      <ol v-else class="outing__stops">
        <li v-for="(stop, index) in outing.stops" :key="stop.invader.id" :class="{ 'outing__stop--done': stop.done }">
          <span class="outing__number">{{ stop.position }}</span>
          <RouterLink :to="{ name: 'invader', params: { id: stop.invader.id } }" class="outing__name">
            {{ stop.invader.name }}
            <small class="muted">{{ stop.invader.points }} pts<template v-if="stop.done"> · flashé</template></small>
          </RouterLink>
          <button
            type="button"
            class="btn btn--icon outing__small"
            :disabled="busy || index === 0"
            :aria-label="`Monter ${stop.invader.name}`"
            @click="move(index, -1)"
          >
            <AppIcon name="up" :size="16" />
          </button>
          <button
            type="button"
            class="btn btn--icon outing__small"
            :disabled="busy || index === outing.stops.length - 1"
            :aria-label="`Descendre ${stop.invader.name}`"
            @click="move(index, 1)"
          >
            <AppIcon name="down" :size="16" />
          </button>
          <button
            type="button"
            class="btn btn--icon btn--danger outing__small"
            :disabled="busy"
            :aria-label="`Retirer ${stop.invader.name}`"
            @click="removeStop(index)"
          >
            <AppIcon name="close" :size="16" />
          </button>
        </li>
      </ol>
      <small class="muted">Ajoutez un invader depuis sa fiche quand la sortie est sur la carte.</small>

      <div class="tiles">
        <RouterLink :to="{ name: 'outing-edit', params: { id: outing.id } }" class="btn btn--tile">
          <AppIcon name="edit" /> <span>Modifier</span>
        </RouterLink>
        <button v-if="canDelete" type="button" class="btn btn--danger btn--tile" :disabled="busy" @click="remove">
          <AppIcon name="trash" /> <span>Supprimer</span>
        </button>
      </div>
    </div>
  </BottomSheet>
</template>

<style scoped>
.outing {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.outing p {
  margin: 0;
}

.outing__meta {
  font-size: 0.85rem;
}

.outing__stops {
  margin: 0;
  padding: 0;
  list-style: none;
}

.outing__stops li {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  border-top: 1px solid var(--border);
}

.outing__number {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--accent-text);
  font-size: 0.8rem;
  font-weight: 700;
}

.outing__stop--done .outing__number {
  background: var(--destroyed);
  color: var(--text);
}

.outing__name {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  color: var(--text);
  text-decoration: none;
}

.outing__small {
  min-width: 34px;
  min-height: 34px;
  padding: 6px;
}
</style>
