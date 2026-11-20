<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { outingsApi } from '@/api/endpoints'
import { TRANSPORT_LABELS, type TransportMode } from '@/api/types'
import BottomSheet from '@/components/BottomSheet.vue'
import FieldErrors from '@/components/FieldErrors.vue'
import PointField, { type Point } from '@/components/PointField.vue'
import { formatDate, formatDuration, today } from '@/composables/format'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'
import { useOutingStore } from '@/stores/outing'
import { useTeamStore } from '@/stores/team'

const DURATIONS = [30, 45, 60, 90, 120, 180, 240, 360, 480]
const modes = Object.entries(TRANSPORT_LABELS) as [TransportMode, string][]

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const team = useTeamStore()
const outing = useOutingStore()
const { errors, capture, clear } = useFormErrors()

const editedId = computed(() => (route.params.id ? Number(route.params.id) : null))
const form = reactive({
  name: `Sortie du ${formatDate(today())}`,
  participants: auth.me ? [auth.me.id] : ([] as number[]),
  mode: 'walk' as TransportMode,
  duration_minutes: 120,
  is_loop: true,
})
const start = ref<Point | null>(null)
const end = ref<Point | null>(null)
const busy = ref(false)
const members = computed(() => team.team?.members ?? [])

onMounted(async () => {
  if (!editedId.value) return
  try {
    const current = await outingsApi.get(editedId.value)
    Object.assign(form, {
      name: current.name,
      participants: current.participants,
      mode: current.mode,
      duration_minutes: current.duration_minutes,
      is_loop: current.is_loop,
    })
    start.value = { lat: current.start_lat, lng: current.start_lng, label: current.start_label }
    end.value = { lat: current.end_lat, lng: current.end_lng, label: current.end_label }
  } catch (error) {
    capture(error)
  }
})

function toggleParticipant(id: number) {
  form.participants = form.participants.includes(id)
    ? form.participants.filter((member) => member !== id)
    : [...form.participants, id]
}

async function submit() {
  clear()
  if (!start.value) return (errors.value = { _: ['Choisissez un point de départ.'] })
  if (!form.is_loop && !end.value) return (errors.value = { _: ["Choisissez un point d'arrivée, ou faites une boucle."] })
  const body = {
    ...form,
    start_lat: start.value.lat,
    start_lng: start.value.lng,
    start_label: start.value.label,
    ...(form.is_loop || !end.value ? {} : { end_lat: end.value.lat, end_lng: end.value.lng, end_label: end.value.label }),
  }
  busy.value = true
  try {
    // New settings: the route is recomputed (a new outing is planned on creation).
    const saved = editedId.value
      ? await outingsApi.update(editedId.value, body).then((updated) => outingsApi.plan(updated.id))
      : await outingsApi.create(body)
    outing.show(saved)
    await router.replace({ name: 'outing', params: { id: saved.id } })
  } catch (error) {
    capture(error)
  } finally {
    busy.value = false
  }
}

function close() {
  router.push(editedId.value ? { name: 'outing', params: { id: editedId.value } } : { name: 'outings' })
}
</script>

<template>
  <BottomSheet :title="editedId ? 'Modifier la sortie' : 'Nouvelle sortie'" @close="close">
    <form class="outing-form" @submit.prevent="submit">
      <label class="field">
        <span>Nom</span>
        <input v-model="form.name" class="input" maxlength="100" required />
      </label>

      <fieldset class="outing-form__group">
        <legend>Participants <small class="muted">(seuls leurs invaders non flashés)</small></legend>
        <div class="chips">
          <button
            v-for="member in members"
            :key="member.id"
            type="button"
            class="chip"
            :class="{ 'chip--active': form.participants.includes(member.id) }"
            :aria-pressed="form.participants.includes(member.id)"
            @click="toggleParticipant(member.id)"
          >
            {{ member.display_name }}
          </button>
        </div>
        <FieldErrors :messages="errors.participants ?? []" />
      </fieldset>

      <fieldset class="outing-form__group">
        <legend>Moyen de transport</legend>
        <div class="chips">
          <button
            v-for="[value, label] in modes"
            :key="value"
            type="button"
            class="chip"
            :class="{ 'chip--active': form.mode === value }"
            :aria-pressed="form.mode === value"
            @click="form.mode = value"
          >
            {{ label }}
          </button>
        </div>
      </fieldset>

      <label class="field">
        <span>Durée</span>
        <select v-model="form.duration_minutes" class="input">
          <option v-for="minutes in DURATIONS" :key="minutes" :value="minutes">{{ formatDuration(minutes) }}</option>
        </select>
      </label>

      <PointField v-model="start" legend="Départ" />

      <label class="outing-form__check">
        <input v-model="form.is_loop" type="checkbox" />
        <span>Boucle : revenir au point de départ</span>
      </label>

      <PointField v-if="!form.is_loop" v-model="end" legend="Arrivée" />

      <FieldErrors :messages="[...(errors._ ?? []), ...(errors.end_lat ?? [])]" />
      <button type="submit" class="btn btn--primary btn--block" :disabled="busy">
        {{ editedId ? 'Enregistrer et recalculer' : 'Créer le parcours' }}
      </button>
      <small class="muted">Distances à vol d'oiseau + 30 % pour les rues, et 2 min par invader.</small>
    </form>
  </BottomSheet>
</template>

<style scoped>
.outing-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.outing-form__group {
  margin: 0;
  padding: 0;
  border: none;
}

.outing-form__group legend {
  margin-bottom: 6px;
  font-size: 0.85rem;
  color: var(--muted);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}


.outing-form__check {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
