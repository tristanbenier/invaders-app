<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { geocodeApi, invadersApi } from '@/api/endpoints'
import { type Invader, STATUS_LABELS, type Status } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import BottomSheet from '@/components/BottomSheet.vue'
import FieldErrors from '@/components/FieldErrors.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import InvaderPhoto from '@/components/InvaderPhoto.vue'
import { type LatLng, useMapContext } from '@/composables/mapContext'
import { useFormErrors } from '@/composables/useFormErrors'
import { useInvadersStore } from '@/stores/invaders'
import { usePlacesStore } from '@/stores/places'

const NAME_PATTERN = /^([A-Z]+)_\d+$/
// Names outside the PREFIX_NUMBER form, with their city prefix (backend: naming.SPECIAL_NAMES).
const SPECIAL_NAMES: Record<string, string> = { SPACE2ISS: 'SPACE' }
const POINT_PRESETS = [10, 20, 30, 40, 50, 100]
const NEW_COUNTRY = -1

const route = useRoute()
const router = useRouter()
const places = usePlacesStore()
const invaders = useInvadersStore()
const mapContext = useMapContext()
const { errors, capture, clear } = useFormErrors()

const editedId = computed(() => (route.name === 'invader-edit' ? Number(route.params.id) : null))
const loading = ref(false)
const submitting = ref(false)

const form = reactive({
  name: '',
  points: 10 as number | null,
  status: 'ok' as Status,
  lat: 0,
  lng: 0,
  address1: '',
  address2: '',
  zip: '',
  comment: '',
})
const imageFile = ref<File | null>(null)
// Picked photo waiting to be cropped.
const fileToCrop = ref<File | null>(null)
const currentImage = ref<string | null>(null)
const removeImage = ref(false)
const newCity = reactive({ name: '', country: null as number | null, countryName: '' })

// An imported invader may have an unusual value: keep it selectable.
const pointOptions = computed(() =>
  form.points !== null && !POINT_PRESETS.includes(form.points)
    ? [...POINT_PRESETS, form.points].sort((a, b) => a - b)
    : POINT_PRESETS,
)
const normalizedName = computed(() => form.name.trim().toUpperCase())
const prefix = computed(
  () => SPECIAL_NAMES[normalizedName.value] ?? NAME_PATTERN.exec(normalizedName.value)?.[1] ?? null,
)
const matchedCity = computed(() => (prefix.value ? places.cityByPrefix.get(prefix.value) : undefined))
const needsCity = computed(() => prefix.value !== null && !matchedCity.value)
// The country belongs to the city: changing it here moves every invader of that city.
const cityCountry = reactive({ id: null as number | null, newName: '' })
const countryChanged = computed(
  () => matchedCity.value !== undefined && cityCountry.id !== null && cityCountry.id !== matchedCity.value.country,
)
watch(
  matchedCity,
  (city) => {
    cityCountry.id = city?.country ?? null
    cityCountry.newName = ''
  },
  { immediate: true },
)
const imagePreview = computed(() =>
  imageFile.value ? URL.createObjectURL(imageFile.value) : removeImage.value ? null : currentImage.value,
)

watch(imagePreview, (_, previous) => previous?.startsWith('blob:') && URL.revokeObjectURL(previous))
onBeforeUnmount(() => imagePreview.value?.startsWith('blob:') && URL.revokeObjectURL(imagePreview.value))

async function init() {
  clear()
  imageFile.value = null
  removeImage.value = false
  if (editedId.value) {
    loading.value = true
    try {
      const invader = await invadersApi.get(editedId.value)
      Object.assign(form, {
        name: invader.name,
        points: invader.points,
        status: invader.status,
        lat: invader.lat,
        lng: invader.lng,
        address1: invader.address1,
        address2: invader.address2,
        zip: invader.zip,
        comment: invader.comment,
      })
      currentImage.value = invader.image
      mapContext.focus(invader)
    } catch (error) {
      capture(error)
    } finally {
      loading.value = false
    }
  } else {
    const lat = Number(route.query.lat)
    const lng = Number(route.query.lng)
    const point = Number.isFinite(lat) && Number.isFinite(lng) && route.query.lat ? { lat, lng } : mapContext.center()
    Object.assign(form, { name: '', points: 10, status: 'ok', address1: '', address2: '', zip: '', comment: '', ...point })
    currentImage.value = null
    mapContext.focus(point)
  }
}

watch(() => route.fullPath, init, { immediate: true })

const addressLookup = ref<'idle' | 'loading' | 'error'>('idle')
let addressRequest = 0

/** New invaders only: prefill the address from the chosen point (the user can still edit it). */
async function fillAddress(point: LatLng) {
  if (editedId.value) return
  const current = ++addressRequest
  addressLookup.value = 'loading'
  try {
    const result = await geocodeApi.reverse(point.lat, point.lng)
    if (current !== addressRequest) return
    if (result.address1) form.address1 = result.address1
    if (result.zip) form.zip = result.zip
    addressLookup.value = 'idle'
  } catch {
    if (current === addressRequest) addressLookup.value = 'error'
  }
}

async function pickOnMap() {
  const point = await mapContext.pickLocation(
    { lat: form.lat, lng: form.lng },
    "Faites glisser le marqueur à l'emplacement de l'invader.",
  )
  if (!point) return
  Object.assign(form, { lat: Number(point.lat.toFixed(6)), lng: Number(point.lng.toFixed(6)) })
  fillAddress(point)
}

function useMyPosition() {
  const position = mapContext.userPosition.value
  if (!position) {
    errors.value = { ...errors.value, location: ['Position indisponible : autorisez la géolocalisation.'] }
    return
  }
  Object.assign(form, { lat: Number(position.lat.toFixed(6)), lng: Number(position.lng.toFixed(6)) })
  mapContext.focus(position)
  fillAddress(position)
}

function onImageChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  // Reset so picking the same file again still triggers a change.
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    errors.value = { ...errors.value, image: ["Ce fichier n'est pas une image."] }
    return
  }
  fileToCrop.value = file
}

function onCropped(file: File) {
  imageFile.value = file
  removeImage.value = false
  fileToCrop.value = null
}

function clearImage() {
  imageFile.value = null
  removeImage.value = true
}

async function createMissingCity() {
  if (!needsCity.value || !prefix.value) return
  const country = newCity.country === NEW_COUNTRY ? undefined : (newCity.country ?? undefined)
  try {
    await places.createCity({
      name: newCity.name.trim(),
      prefix: prefix.value,
      ...(country ? { country } : { country_name: newCity.countryName.trim() }),
    })
  } catch (error) {
    // Show city errors next to the city fields.
    capture(error)
    errors.value = Object.fromEntries(Object.entries(errors.value).map(([key, value]) => [`city_${key}`, value]))
    throw error
  }
}

async function updateCityCountry() {
  const city = matchedCity.value
  if (!city || !countryChanged.value) return
  const newCountry = cityCountry.id === NEW_COUNTRY
  try {
    await places.updateCity(
      city.id,
      newCountry ? { country_name: cityCountry.newName.trim() } : { country: cityCountry.id! },
    )
  } catch (error) {
    capture(error)
    errors.value = Object.fromEntries(Object.entries(errors.value).map(([key, value]) => [`city_${key}`, value]))
    throw error
  }
}

function payload(): FormData | Partial<Invader> {
  const fields = {
    name: normalizedName.value,
    points: form.points ?? 0,
    status: form.status,
    lat: form.lat,
    lng: form.lng,
    address1: form.address1,
    address2: form.address2,
    zip: form.zip,
    comment: form.comment,
  }
  if (!imageFile.value) {
    return editedId.value && removeImage.value ? { ...fields, image: null } : fields
  }
  const data = new FormData()
  for (const [key, value] of Object.entries(fields)) data.append(key, String(value))
  data.append('image', imageFile.value)
  return data
}

async function submit() {
  clear()
  submitting.value = true
  try {
    await createMissingCity()
    await updateCityCountry()
    const body = payload()
    let saved: Invader
    if (editedId.value) {
      saved = await invadersApi.update(editedId.value, body)
    } else {
      saved = await invadersApi.create(body instanceof FormData ? body : toFormData(body))
    }
    invaders.upsert(saved)
    await router.replace({ name: 'invader', params: { id: saved.id } })
  } catch (error) {
    if (!Object.keys(errors.value).length) capture(error)
  } finally {
    submitting.value = false
  }
}

function toFormData(fields: Partial<Invader>) {
  const data = new FormData()
  for (const [key, value] of Object.entries(fields)) if (value !== null) data.append(key, String(value))
  return data
}

function close() {
  if (editedId.value) router.push({ name: 'invader', params: { id: editedId.value } })
  else router.push({ name: 'map' })
}
</script>

<template>
  <BottomSheet :title="editedId ? `Modifier ${form.name}` : 'Nouvel invader'" @close="close">
    <p v-if="loading" class="muted">Chargement…</p>

    <form v-else class="form" novalidate @submit.prevent="submit">
      <label class="field">
        <span>Nom</span>
        <input
          v-model="form.name"
          class="input form__name"
          placeholder="PA_123"
          autocapitalize="characters"
          autocomplete="off"
          spellcheck="false"
          required
        />
        <small v-if="matchedCity" class="muted">Ville : {{ matchedCity.name }}</small>
        <FieldErrors :messages="errors.name" />
      </label>

      <template v-if="matchedCity">
        <label class="field">
          <span>Pays</span>
          <select v-model="cityCountry.id" class="input">
            <option v-for="country in places.countries" :key="country.id" :value="country.id">{{ country.name }}</option>
            <option :value="NEW_COUNTRY">+ Nouveau pays</option>
          </select>
          <small v-if="countryChanged" class="muted">
            S'applique à toute la ville {{ matchedCity.name }} et à tous ses invaders.
          </small>
        </label>
        <label v-if="cityCountry.id === NEW_COUNTRY" class="field">
          <span>Nom du nouveau pays</span>
          <input v-model="cityCountry.newName" class="input" required />
        </label>
        <FieldErrors
          :messages="[...(errors.city_country ?? []), ...(errors.city_country_name ?? []), ...(errors.city__ ?? [])]"
        />
      </template>

      <fieldset v-if="needsCity" class="form__city card">
        <legend>Nouvelle ville pour le préfixe {{ prefix }}</legend>
        <p class="muted form__hint">Aucune ville de l'équipe n'utilise ce préfixe. Elle sera créée avec l'invader.</p>
        <label class="field">
          <span>Nom de la ville</span>
          <input v-model="newCity.name" class="input" required />
          <FieldErrors :messages="errors.city_name" />
        </label>
        <label class="field">
          <span>Pays</span>
          <select v-model="newCity.country" class="input" required>
            <option :value="null" disabled>Choisir…</option>
            <option v-for="country in places.countries" :key="country.id" :value="country.id">{{ country.name }}</option>
            <option :value="NEW_COUNTRY">+ Nouveau pays</option>
          </select>
        </label>
        <label v-if="newCity.country === NEW_COUNTRY" class="field">
          <span>Nom du nouveau pays</span>
          <input v-model="newCity.countryName" class="input" required />
        </label>
        <FieldErrors
          :messages="[
            ...(errors.city_country ?? []),
            ...(errors.city_country_name ?? []),
            ...(errors.city_prefix ?? []),
            ...(errors.city__ ?? []),
          ]"
        />
      </fieldset>
      <FieldErrors :messages="errors.city" />

      <div class="field">
        <span>Points</span>
        <div class="form__points">
          <button
            v-for="value in pointOptions"
            :key="value"
            type="button"
            class="chip"
            :class="{ 'chip--active': form.points === value }"
            :aria-pressed="form.points === value"
            @click="form.points = value"
          >
            {{ value }}
          </button>
        </div>
        <FieldErrors :messages="errors.points" />
      </div>

      <label class="field">
        <span>Statut</span>
        <select v-model="form.status" class="input">
          <option v-for="(label, value) in STATUS_LABELS" :key="value" :value="value">{{ label }}</option>
        </select>
        <FieldErrors :messages="errors.status" />
      </label>

      <div class="field">
        <span>Emplacement</span>
        <p class="form__coords">{{ form.lat.toFixed(5) }}, {{ form.lng.toFixed(5) }}</p>
        <div class="form__location-actions">
          <button type="button" class="btn" @click="pickOnMap"><AppIcon name="move" :size="18" /> Sur la carte</button>
          <button type="button" class="btn" @click="useMyPosition"><AppIcon name="locate" :size="18" /> Ma position</button>
        </div>
        <FieldErrors :messages="[...(errors.location ?? []), ...(errors.lat ?? []), ...(errors.lng ?? [])]" />
      </div>

      <fieldset class="form__address">
        <legend class="visually-hidden">Adresse</legend>
        <p v-if="addressLookup === 'loading'" class="muted form__hint" role="status">Recherche de l'adresse…</p>
        <p v-else-if="addressLookup === 'error'" class="muted form__hint" role="status">
          Adresse introuvable automatiquement : vous pouvez la saisir.
        </p>
        <label class="field">
          <span>Adresse</span>
          <input v-model="form.address1" class="input" maxlength="255" autocomplete="address-line1" placeholder="12 rue des Arts" />
          <FieldErrors :messages="errors.address1" />
        </label>
        <label class="field">
          <span>Complément</span>
          <input v-model="form.address2" class="input" maxlength="255" autocomplete="address-line2" placeholder="Au-dessus de la porte" />
          <FieldErrors :messages="errors.address2" />
        </label>
        <label class="field form__zip">
          <span>Code postal</span>
          <input v-model="form.zip" class="input" maxlength="20" autocomplete="postal-code" />
          <FieldErrors :messages="errors.zip" />
        </label>
      </fieldset>

      <label class="field">
        <span>Commentaire</span>
        <textarea v-model="form.comment" class="input form__comment" rows="3" placeholder="Accès, hauteur, astuce pour le flasher…" />
        <FieldErrors :messages="errors.comment" />
      </label>

      <div class="field">
        <span>Photo</span>
        <InvaderPhoto v-if="imagePreview" :src="imagePreview" alt="Aperçu de la photo" class="form__preview" />
        <div class="form__location-actions">
          <label class="btn">
            {{ imagePreview ? 'Changer la photo' : 'Ajouter une photo' }}
            <input type="file" accept="image/*" class="form__file" @change="onImageChange" />
          </label>
          <button v-if="imagePreview" type="button" class="btn btn--danger" @click="clearImage">Retirer</button>
        </div>
        <FieldErrors :messages="errors.image" />
      </div>

      <FieldErrors :messages="errors._" />
      <button type="submit" class="btn btn--primary btn--block" :disabled="submitting">
        {{ editedId ? 'Enregistrer' : "Ajouter l'invader" }}
      </button>
    </form>

    <ImageCropper v-if="fileToCrop" :file="fileToCrop" @done="onCropped" @cancel="fileToCrop = null" />
  </BottomSheet>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form__name {
  text-transform: uppercase;
}

.form__city {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  background: var(--bg);
}

.form__city legend {
  font-weight: 600;
  padding: 0 4px;
}

.form__hint {
  margin: 0;
  font-size: 0.85rem;
}

.form__points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.form__address {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  border: none;
}

.form__zip {
  max-width: 160px;
}

.form__comment {
  resize: vertical;
  min-height: 88px;
}

.form__coords {
  margin: 0;
  font-variant-numeric: tabular-nums;
}

.form__location-actions {
  display: flex;
  gap: 8px;
}

.form__location-actions .btn {
  flex: 1;
}

.form__preview {
  width: min(100%, 240px);
  border-radius: 10px;
}

.form__file {
  display: none;
}
</style>
