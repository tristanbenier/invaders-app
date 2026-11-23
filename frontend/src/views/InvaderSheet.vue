<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { invadersApi, outingsApi } from '@/api/endpoints'
import { type InvaderDetail, STATUS_LABELS } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import BottomSheet from '@/components/BottomSheet.vue'
import FieldErrors from '@/components/FieldErrors.vue'
import InvaderPhoto from '@/components/InvaderPhoto.vue'
import MiniMap from '@/components/MiniMap.vue'
import { directionsTo } from '@/composables/directions'
import { formatDate } from '@/composables/format'
import { useGalleryNavigation } from '@/composables/galleryNavigation'
import { useOptionalMapContext } from '@/composables/mapContext'
import { useFormErrors } from '@/composables/useFormErrors'
import { isIssInvader, useIssPosition } from '@/composables/useIssPosition'
import { useFlashSyncFailing } from '@/composables/useFlashSync'
import { useAuthStore } from '@/stores/auth'
import { useOutingStore } from '@/stores/outing'
import { useInvadersStore } from '@/stores/invaders'
import { usePlacesStore } from '@/stores/places'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const outingStore = useOutingStore()
const flashSyncFailing = useFlashSyncFailing()
// With a working Flash Invaders sync, flashes come from the app only, unless the member
// kept the manual buttons (option in the team screen).
const manualFlash = computed(() => !auth.me?.flash_sync_enabled || auth.me.manual_flash || flashSyncFailing.value)
const places = usePlacesStore()
const invaders = useInvadersStore()
const mapContext = useOptionalMapContext()
// Outside the map (gallery), the sheet is a modal and closes back to its parent screen.
const closeRoute = computed(() => (mapContext ? { name: 'map' } : { name: 'gallery' }))
const { errors, capture, clear } = useFormErrors()

const invader = ref<InvaderDetail | null>(null)
const loadError = ref<string | null>(null)
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
// SPACE2ISS is on the ISS: live position instead of a fixed spot, no directions.
const onIss = computed(() => invader.value !== null && isIssInvader(invader.value))
const iss = useIssPosition(onIss)
const directions = computed(() => (invader.value && !onIss.value ? directionsTo(invader.value) : null))
let focusedOnIss = false
// Other people's photos of this invader, to identify it or check its state.
const googleImagesUrl = computed(() =>
  invader.value
    ? `https://www.google.com/search?tbm=isch&q=${encodeURIComponent(`invader ${invader.value.name}`)}`
    : null,
)

async function load(id: number) {
  // Going to the previous / next invader keeps the current one on screen until the new one arrives.
  loadError.value = null
  clear()
  try {
    invader.value = await invadersApi.get(id)
    focusedOnIss = false
    if (onIss.value) focusIss()
    else mapContext?.focus(invader.value)
  } catch (error) {
    invader.value = null
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

// Gallery only: previous / next invader in the gallery's list (filters, search and ordering applied).
const gallery = useGalleryNavigation()
const galleryIndex = computed(() => gallery?.items.value.findIndex((item) => item.id === Number(route.params.id)) ?? -1)
const hasPrevious = computed(() => galleryIndex.value > 0)
const hasNext = computed(
  () => !!gallery && galleryIndex.value !== -1 && (galleryIndex.value < gallery.items.value.length - 1 || gallery.hasMore.value),
)

async function step(delta: -1 | 1) {
  if (!gallery || galleryIndex.value === -1) return
  const target = galleryIndex.value + delta
  if (target < 0) return
  // Past the last loaded invader: fetch the next page of the list first.
  if (target >= gallery.items.value.length) {
    if (!gallery.hasMore.value) return
    await gallery.loadMore()
  }
  const next = gallery.items.value[target]
  if (next) router.replace({ name: 'gallery-invader', params: { id: next.id } })
}

function onKeydown(event: KeyboardEvent) {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return
  const target = event.target as HTMLElement | null
  if (target?.closest('input, textarea, select, [contenteditable="true"]')) return
  if (event.key === 'ArrowLeft') step(-1)
  else if (event.key === 'ArrowRight') step(1)
}

// Mobile: a horizontal swipe on the sheet (left = next, right = previous).
const SWIPE_MIN_PX = 60
let touchStart: { x: number; y: number } | null = null

function onTouchStart(event: TouchEvent) {
  const touch = event.touches[0]
  touchStart = event.touches.length === 1 && touch ? { x: touch.clientX, y: touch.clientY } : null
}

function onTouchEnd(event: TouchEvent) {
  const touch = event.changedTouches[0]
  if (!touchStart || !touch) return
  const dx = touch.clientX - touchStart.x
  const dy = touch.clientY - touchStart.y
  touchStart = null
  // Mostly horizontal, so that scrolling the sheet never changes invader.
  if (Math.abs(dx) < SWIPE_MIN_PX || Math.abs(dx) < 2 * Math.abs(dy)) return
  step(dx < 0 ? 1 : -1)
}

onMounted(() => gallery && document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

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

// No date asked: the backend records today's, then the Flash Invaders sync sets the app's.
// Outing shown on the map: this invader can be added to or removed from its route.
const inOuting = computed(() => invader.value !== null && outingStore.stopIds.has(invader.value.id))

function toggleOutingStop() {
  const current = outingStore.active
  if (!current || !invader.value) return
  const ids = current.stops.map((stop) => stop.invader.id)
  const invaderId = invader.value.id
  run(async () => {
    const updated = await outingsApi.update(current.id, {
      stop_ids: inOuting.value ? ids.filter((id) => id !== invaderId) : [...ids, invaderId],
    })
    outingStore.update(updated)
  })
}

const flash = () => run(() => invadersApi.flash(invader.value!.id))
const unflash = () => run(() => invadersApi.unflash(invader.value!.id))

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
  <BottomSheet :title="invader ? `${invader.name} • ${invader.points} PTS` : 'Invader'" :modal="!mapContext" @close="router.push(closeRoute)">
    <template #header>
      <div class="detail__head">
        <h2 class="detail__title">{{ invader ? `${invader.name} • ${invader.points} PTS` : 'Invader' }}</h2>
        <template v-if="invader">
          <p class="muted detail__place">{{ city?.name ?? '—' }}<template v-if="country">, {{ country.name }}</template></p>
          <div class="detail__badges">
            <span class="status" :class="`status--${invader.status}`">{{ STATUS_LABELS[invader.status] }}</span>
            <span v-if="invader.my_flashed_at" class="detail__flashed">
              <AppIcon name="check" :size="16" /> Flashé le {{ formatDate(invader.my_flashed_at) }}
            </span>
            <span v-else class="muted detail__not-flashed">Pas encore flashé</span>
          </div>
        </template>
      </div>
    </template>
    <p v-if="loadError" class="errors">{{ loadError }}</p>
    <p v-else-if="!invader" class="muted">Chargement…</p>

    <div v-else class="detail" @touchstart.passive="onTouchStart" @touchend="onTouchEnd">
      <nav v-if="gallery && galleryIndex !== -1" class="detail__nav" aria-label="Invaders de la galerie">
        <button type="button" class="btn detail__nav-btn" :disabled="!hasPrevious" title="Flèche gauche" @click="step(-1)">
          <AppIcon name="back" :size="16" /> Précédent
        </button>
        <span class="muted">{{ galleryIndex + 1 }} / {{ gallery.count.value ?? gallery.items.value.length }}</span>
        <button type="button" class="btn detail__nav-btn" :disabled="!hasNext" title="Flèche droite" @click="step(1)">
          Suivant <AppIcon name="forward" :size="16" />
        </button>
      </nav>

      <section v-if="invader.image" class="card detail__card">
        <h3 class="detail__card-title"><span class="detail__card-icon"><AppIcon name="image" :size="18" /></span> Photo</h3>
        <InvaderPhoto :src="invader.image" :alt="`Photo de ${invader.name}`" class="detail__image" />
      </section>

      <section class="card detail__card">
        <h3 class="detail__card-title"><span class="detail__card-icon"><AppIcon name="pin" :size="18" /></span> Position</h3>
        <template v-if="onIss">
          <p v-if="iss.position.value" class="detail__coords">
            {{ iss.position.value.lat.toFixed(2) }}, {{ iss.position.value.lng.toFixed(2) }} ·
            {{ iss.position.value.altitude_km }} km d'altitude ·
            {{ iss.position.value.velocity_kmh.toLocaleString('fr-FR') }} km/h
          </p>
          <p v-else class="muted">{{ iss.error.value ?? 'Recherche de la station spatiale…' }}</p>
        </template>
        <p v-else-if="address.length" class="detail__address">
          <span v-for="line in address" :key="line" class="detail__address-line">{{ line }}</span>
        </p>
        <p v-if="invader.comment" class="detail__comment">{{ invader.comment }}</p>
        <!-- Gallery only: the map screen already shows where the invader is. -->
        <MiniMap v-if="!mapContext && !onIss" :lat="invader.lat" :lng="invader.lng" :label="invader.name" />
      </section>

      <section class="card detail__card">
        <h3 class="detail__card-title"><span class="detail__card-icon"><AppIcon name="flag" :size="18" /></span> Actions</h3>
        <div class="tiles">
          <template v-if="manualFlash">
            <button v-if="invader.my_flashed_at" type="button" class="btn btn--tile" :disabled="busy" @click="unflash">
              <AppIcon name="close" /> <span>Déflasher</span>
            </button>
            <button v-else type="button" class="btn btn--primary btn--tile" :disabled="busy" @click="flash">
              <AppIcon name="camera" /> <span>Flasher</span>
            </button>
          </template>
          <a
            v-if="directions"
            :href="directions.url"
            target="_blank"
            rel="noopener"
            class="btn btn--tile"
            :title="directions.app === 'apple' ? 'Ouvrir dans Plans' : 'Ouvrir dans Google Maps'"
          >
            <AppIcon name="route" /> <span>Itinéraire</span>
          </a>
          <RouterLink v-if="!mapContext" :to="{ name: 'invader', params: { id: invader.id } }" class="btn btn--tile">
            <AppIcon name="map" /> <span>Carte</span>
          </RouterLink>
          <a v-if="googleImagesUrl" :href="googleImagesUrl" target="_blank" rel="noopener" class="btn btn--tile" title="Rechercher dans Google Images">
            <AppIcon name="search" /> <span>Google</span>
          </a>
          <button
            v-if="mapContext && outingStore.active"
            type="button"
            class="btn btn--tile"
            :disabled="busy"
            :title="inOuting ? `Retirer de « ${outingStore.active.name} »` : `Ajouter à « ${outingStore.active.name} »`"
            @click="toggleOutingStop"
          >
            <AppIcon :name="inOuting ? 'close' : 'flag'" /> <span>{{ inOuting ? 'Hors sortie' : 'Sortie' }}</span>
          </button>
          <RouterLink :to="{ name: 'invader-edit', params: { id: invader.id } }" class="btn btn--tile">
            <AppIcon name="edit" /> <span>Modifier</span>
          </RouterLink>
          <button v-if="auth.isAdmin" type="button" class="btn btn--danger btn--tile" :disabled="busy" @click="remove">
            <AppIcon name="trash" /> <span>Supprimer</span>
          </button>
        </div>
        <p v-if="auth.me?.flash_sync_enabled && flashSyncFailing" class="muted">
          La synchro Flash Invaders ne répond pas : vous pouvez flasher à la main en attendant.
        </p>
        <FieldErrors :messages="[...(errors._ ?? []), ...(errors.flashed_at ?? [])]" />
      </section>

      <section v-if="invader.flashers.length" class="card detail__card">
        <h3 class="detail__card-title">
          <span class="detail__card-icon"><AppIcon name="team" :size="18" /></span> Flashé par ({{ invader.flashers.length }})
        </h3>
        <p v-if="!invader.flashers.length" class="muted">Personne pour l'instant.</p>
        <ul v-else class="detail__flashers">
          <li v-for="flasher in invader.flashers" :key="flasher.user.id">
            <span>{{ flasher.user.display_name }}</span>
            <span class="muted">{{ formatDate(flasher.flashed_at) }}</span>
          </li>
        </ul>
      </section>
    </div>
  </BottomSheet>
</template>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Header slot: replaces BottomSheet's own title. */
.detail__head {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail__title {
  font-size: 1.15rem;
}

.detail__place {
  margin: 0;
  font-size: 0.9rem;
}

.detail__badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  font-size: 0.85rem;
}

.detail__flashed {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--flashed);
  font-weight: 600;
}

/* Buttons for mouse and keyboard users; touch screens swipe instead. */
.detail__nav {
  display: none;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.detail__nav-btn {
  min-height: 32px;
  padding: 4px 10px;
  gap: 4px;
  font-size: 0.85rem;
}

@media (hover: hover) and (pointer: fine) {
  .detail__nav {
    display: flex;
  }
}

.detail__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.detail__card p {
  margin: 0;
}

.detail__card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1rem;
}

.detail__card-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--surface-2);
  color: var(--accent);
}

.detail__image {
  width: min(100%, 320px);
  align-self: center;
  border-radius: 10px;
}

.detail__address-line {
  display: block;
}

/* Keep the line breaks typed by members. */
.detail__comment {
  white-space: pre-line;
  overflow-wrap: anywhere;
  font-size: 0.9rem;
  color: var(--muted);
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

.detail__flashers {
  margin: 0;
  padding: 0;
  list-style: none;
}

.detail__flashers li {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-top: 1px solid var(--border);
}

.detail__meta {
  margin: 0;
  font-size: 0.8rem;
}
</style>
