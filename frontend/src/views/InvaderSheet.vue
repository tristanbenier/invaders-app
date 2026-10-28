<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { invadersApi } from '@/api/endpoints'
import { type InvaderDetail, STATUS_LABELS } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import BottomSheet from '@/components/BottomSheet.vue'
import FieldErrors from '@/components/FieldErrors.vue'
import InvaderHistory from '@/components/InvaderHistory.vue'
import InvaderPhoto from '@/components/InvaderPhoto.vue'
import { directionsTo } from '@/composables/directions'
import { formatDate, today } from '@/composables/format'
import { useOptionalMapContext } from '@/composables/mapContext'
import { useFormErrors } from '@/composables/useFormErrors'
import { isIssInvader, useIssPosition } from '@/composables/useIssPosition'
import { useAuthStore } from '@/stores/auth'
import { useInvadersStore } from '@/stores/invaders'
import { usePlacesStore } from '@/stores/places'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const places = usePlacesStore()
const invaders = useInvadersStore()
const mapContext = useOptionalMapContext()
// Outside the map (gallery), the sheet is a modal and closes back to its parent screen.
const closeRoute = computed(() => (mapContext ? { name: 'map' } : { name: 'gallery' }))
const { errors, capture, clear } = useFormErrors()

const invader = ref<InvaderDetail | null>(null)
const loadError = ref<string | null>(null)
const flashDate = ref(today())
const busy = ref(false)

const city = computed(() => (invader.value ? places.cityById.get(invader.value.city) : undefined))
const country = computed(() => places.countries.find((c) => c.id === city.value?.country))
const address = computed(() => {
  if (!invader.value) return []
  const { address1, address2, zip } = invader.value
  const locality = [zip, city.value?.name].filter(Boolean).join(' ')
  // Only show the locality when there is an actual street address or zip code.
  return [address1, address2, address1 || address2 || zip ? locality : ''].filter(Boolean)
})
// SPACE2ISS is on the ISS: live position instead of a fixed spot, no directions, no move.
const onIss = computed(() => invader.value !== null && isIssInvader(invader.value))
const iss = useIssPosition(onIss)
const directions = computed(() => (invader.value && !onIss.value ? directionsTo(invader.value) : null))
let focusedOnIss = false

async function load(id: number) {
  invader.value = null
  loadError.value = null
  clear()
  try {
    invader.value = await invadersApi.get(id)
    flashDate.value = invader.value.my_flashed_at ?? today()
    focusedOnIss = false
    if (onIss.value) focusIss()
    else mapContext?.focus(invader.value)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : String(error)
  }
}

/** Center the map on the ISS once its live position is known (zoomed out: it is over the planet). */
function focusIss() {
  if (focusedOnIss || !iss.position.value) return
  focusedOnIss = true
  mapContext?.focus(iss.position.value, 4)
}

watch(iss.position, () => onIss.value && focusIss())

watch(
  () => Number(route.params.id),
  (id) => id && load(id),
  { immediate: true },
)

async function run(action: () => Promise<InvaderDetail | void>) {
  clear()
  busy.value = true
  try {
    const result = await action()
    if (result) {
      invader.value = result
      invaders.upsert(result)
    }
  } catch (error) {
    capture(error)
  } finally {
    busy.value = false
  }
}

const flash = () => run(() => invadersApi.flash(invader.value!.id, flashDate.value))
const unflash = () => run(() => invadersApi.unflash(invader.value!.id))

async function move() {
  if (!mapContext) return
  const current = invader.value!
  const point = await mapContext.pickLocation(current, `Faites glisser ${current.name} à sa nouvelle position.`)
  if (!point) return
  await run(async () => {
    await invadersApi.update(current.id, { lat: point.lat, lng: point.lng })
    return invadersApi.get(current.id)
  })
  mapContext.focus(point)
}

async function remove() {
  const current = invader.value!
  if (!window.confirm(`Supprimer définitivement ${current.name} ? Les flashs associés seront aussi supprimés.`)) return
  await run(async () => {
    await invadersApi.remove(current.id)
    invaders.remove(current.id)
    await router.replace(closeRoute.value)
  })
}
</script>

<template>
  <BottomSheet :title="invader?.name ?? 'Invader'" :modal="!mapContext" @close="router.push(closeRoute)">
    <p v-if="loadError" class="errors">{{ loadError }}</p>
    <p v-else-if="!invader" class="muted">Chargement…</p>

    <div v-else class="detail">
      <InvaderPhoto v-if="invader.image" :src="invader.image" :alt="`Photo de ${invader.name}`" class="detail__image" />

      <dl class="detail__facts">
        <div>
          <dt>Ville</dt>
          <dd>{{ city?.name ?? '—' }}<template v-if="country">, {{ country.name }}</template></dd>
        </div>
        <div>
          <dt>Points</dt>
          <dd>{{ invader.points }}</dd>
        </div>
        <div>
          <dt>Statut</dt>
          <dd>
            <span class="status" :class="`status--${invader.status}`">{{ STATUS_LABELS[invader.status] }}</span>
          </dd>
        </div>
        <div v-if="onIss" class="detail__wide">
          <dt>Position en temps réel</dt>
          <dd v-if="iss.position.value" class="detail__coords">
            {{ iss.position.value.lat.toFixed(2) }}, {{ iss.position.value.lng.toFixed(2) }} ·
            {{ iss.position.value.altitude_km }} km d'altitude ·
            {{ iss.position.value.velocity_kmh.toLocaleString('fr-FR') }} km/h
          </dd>
          <dd v-else class="muted">{{ iss.error.value ?? 'Recherche de la station spatiale…' }}</dd>
        </div>
        <div v-else>
          <dt>Coordonnées</dt>
          <dd class="detail__coords">{{ invader.lat.toFixed(5) }}, {{ invader.lng.toFixed(5) }}</dd>
        </div>
        <div v-if="address.length" class="detail__wide">
          <dt>Adresse</dt>
          <dd>
            <span v-for="line in address" :key="line" class="detail__address-line">{{ line }}</span>
          </dd>
        </div>
        <div v-if="invader.comment" class="detail__wide">
          <dt>Commentaire</dt>
          <dd class="detail__comment">{{ invader.comment }}</dd>
        </div>
      </dl>

      <section class="detail__flash card">
        <template v-if="invader.my_flashed_at">
          <p class="detail__flashed">
            <AppIcon name="check" :size="18" />
            Flashé le {{ formatDate(invader.my_flashed_at) }}
          </p>
          <button type="button" class="btn btn--block" :disabled="busy" @click="unflash">Annuler mon flash</button>
        </template>
        <template v-else>
          <label class="field">
            <span>Date du flash</span>
            <input v-model="flashDate" class="input" type="date" :max="today()" required />
          </label>
          <button type="button" class="btn btn--primary btn--block" :disabled="busy || !flashDate" @click="flash">
            Je l'ai flashé
          </button>
        </template>
        <FieldErrors :messages="[...(errors._ ?? []), ...(errors.flashed_at ?? [])]" />
      </section>

      <section>
        <h3 class="detail__subtitle">Flashé par l'équipe ({{ invader.flashers.length }})</h3>
        <p v-if="!invader.flashers.length" class="muted">Personne pour l'instant.</p>
        <ul v-else class="detail__flashers">
          <li v-for="flasher in invader.flashers" :key="flasher.user.id">
            <span>{{ flasher.user.display_name }}</span>
            <span class="muted">{{ formatDate(flasher.flashed_at) }}</span>
          </li>
        </ul>
      </section>

      <a
        v-if="directions"
        :href="directions.url"
        target="_blank"
        rel="noopener"
        class="btn btn--block"
        :title="directions.app === 'apple' ? 'Ouvrir dans Plans' : 'Ouvrir dans Google Maps'"
      >
        <AppIcon name="route" :size="18" /> Itinéraire
      </a>

      <RouterLink
        v-if="!mapContext"
        :to="{ name: 'invader', params: { id: invader.id } }"
        class="btn btn--primary btn--block"
      >
        <AppIcon name="map" :size="18" /> Voir sur la carte
      </RouterLink>

      <div class="detail__actions">
        <RouterLink :to="{ name: 'invader-edit', params: { id: invader.id } }" class="btn">
          <AppIcon name="edit" :size="18" /> Modifier
        </RouterLink>
        <button v-if="mapContext && !onIss" type="button" class="btn" :disabled="busy" @click="move">
          <AppIcon name="move" :size="18" /> Déplacer
        </button>
        <button v-if="auth.isAdmin" type="button" class="btn btn--danger" :disabled="busy" @click="remove">
          <AppIcon name="trash" :size="18" /> Supprimer
        </button>
      </div>

      <InvaderHistory :invader-id="invader.id" :updated-at="invader.updated_at" :lat="invader.lat" :lng="invader.lng" />

      <p v-if="invader.created_by" class="muted detail__meta">
        Ajouté par {{ invader.created_by.display_name }} le {{ formatDate(invader.created_at) }}
      </p>
    </div>
  </BottomSheet>
</template>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail__image {
  width: min(100%, 320px);
  align-self: center;
  border-radius: 10px;
}

.detail__facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 0;
}

.detail__facts dt {
  font-size: 0.8rem;
  color: var(--muted);
}

.detail__facts dd {
  margin: 0;
}

.detail__wide {
  grid-column: 1 / -1;
}

.detail__address-line {
  display: block;
}

/* Keep the line breaks typed by members. */
.detail__comment {
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.detail__coords {
  font-variant-numeric: tabular-nums;
  font-size: 0.9rem;
}

.status {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 0.85rem;
  background: var(--surface-2);
}

.status--ok {
  color: var(--flashed);
}

.status--degraded,
.status--hidden {
  color: var(--warning);
}

.status--destroyed {
  color: var(--danger);
}

.detail__flash {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--bg);
}

.detail__flashed {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: var(--flashed);
  font-weight: 600;
}

.detail__subtitle {
  font-size: 0.95rem;
  margin-bottom: 8px;
}

.detail__flashers {
  margin: 0;
  padding: 0;
  list-style: none;
}

.detail__flashers li {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.detail__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail__actions .btn {
  flex: 1;
}

.detail__meta {
  margin: 0;
  font-size: 0.8rem;
}
</style>
