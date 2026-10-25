<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { invadersApi } from '@/api/endpoints'
import { type Invader, STATUS_LABELS } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import InvaderPhoto from '@/components/InvaderPhoto.vue'
import { useFiltersStore } from '@/stores/filters'
import { useInvadersStore } from '@/stores/invaders'
import { usePlacesStore } from '@/stores/places'
import { useTeamStore } from '@/stores/team'

const ORDERINGS = [
  ['name', 'Nom'],
  ['city', 'Ville'],
  ['-points', 'Points (décroissant)'],
  ['points', 'Points (croissant)'],
  ['-created_at', 'Ajout récent'],
] as const

const filters = useFiltersStore()
const places = usePlacesStore()
const team = useTeamStore()
const invadersStore = useInvadersStore()

const items = ref<Invader[]>([])
const count = ref<number | null>(null)
const page = ref(0)
const hasMore = ref(true)
const loading = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const ordering = ref<(typeof ORDERINGS)[number][0]>('name')
const showFilters = ref(false)
const sentinel = ref<HTMLElement>()

const query = computed(() => ({ ...filters.query, search: search.value.trim(), ordering: ordering.value }))
let generation = 0
let searchTimer: ReturnType<typeof setTimeout> | undefined
let observer: IntersectionObserver | undefined

async function loadMore() {
  if (loading.value || !hasMore.value) return
  const current = generation
  loading.value = true
  error.value = null
  try {
    const result = await invadersApi.page(query.value, page.value + 1)
    if (current !== generation) return
    items.value = [...items.value, ...result.results]
    count.value = result.count
    page.value += 1
    hasMore.value = result.next !== null
  } catch (e) {
    if (current === generation) error.value = e instanceof Error ? e.message : String(e)
  } finally {
    if (current === generation) loading.value = false
  }
}

function reset() {
  generation += 1
  items.value = []
  count.value = null
  page.value = 0
  hasMore.value = true
  loading.value = false
  loadMore()
}

watch(() => [filters.query, ordering.value], reset, { deep: true })
// Reflect flashes, edits and deletions made in the modal without reloading the list.
watch(
  () => invadersStore.lastChange,
  (change) => {
    if (!change) return
    if (change.type === 'remove') {
      if (items.value.some((item) => item.id === change.id)) {
        items.value = items.value.filter((item) => item.id !== change.id)
        if (count.value !== null) count.value -= 1
      }
    } else {
      items.value = items.value.map((item) => (item.id === change.invader.id ? change.invader : item))
    }
  },
)

watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reset, 250)
})

onMounted(() => {
  places.load()
  team.load()
  reset()
  // Infinite scroll: load the next page when the sentinel below the grid becomes visible.
  observer = new IntersectionObserver((entries) => entries.some((e) => e.isIntersecting) && loadMore(), {
    rootMargin: '400px',
  })
  if (sentinel.value) observer.observe(sentinel.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  clearTimeout(searchTimer)
})

function state(invader: Invader) {
  if (invader.status === 'destroyed') return 'destroyed'
  return invader.my_flashed_at ? 'flashed' : 'not-flashed'
}
</script>

<template>
  <div class="page gallery">
    <header class="gallery__header">
      <h1>Galerie</h1>
      <p class="muted">
        <template v-if="count !== null">{{ count }} invader{{ count > 1 ? 's' : '' }}</template>
        <template v-else>&nbsp;</template>
      </p>
    </header>

    <div class="gallery__toolbar">
      <div class="gallery__search">
        <AppIcon name="search" :size="18" class="gallery__search-icon" />
        <input
          v-model="search"
          class="input"
          type="search"
          placeholder="Rechercher (PA_123)"
          autocapitalize="characters"
          autocomplete="off"
          aria-label="Rechercher un invader"
        />
      </div>
      <button
        type="button"
        class="btn btn--icon gallery__filter-button"
        :class="{ 'gallery__filter-button--active': filters.activeCount }"
        :aria-expanded="showFilters"
        aria-label="Filtres"
        @click="showFilters = !showFilters"
      >
        <AppIcon name="filter" />
        <span v-if="filters.activeCount" class="badge">{{ filters.activeCount }}</span>
      </button>
    </div>

    <section v-if="showFilters" class="card">
      <FilterPanel />
    </section>

    <label class="field gallery__ordering">
      <span>Trier par</span>
      <select v-model="ordering" class="input">
        <option v-for="[value, label] in ORDERINGS" :key="value" :value="value">{{ label }}</option>
      </select>
    </label>

    <ul class="gallery__grid">
      <li v-for="invader in items" :key="invader.id">
        <RouterLink :to="{ name: 'gallery-invader', params: { id: invader.id } }" class="tile" :class="`tile--${state(invader)}`">
          <div class="tile__visual">
            <InvaderPhoto v-if="invader.image" :src="invader.image" :alt="`Photo de ${invader.name}`" lazy class="tile__photo" />
            <span v-else class="tile__placeholder" aria-hidden="true" />
            <span v-if="invader.my_flashed_at" class="tile__badge">
              <AppIcon name="check" :size="14" /> Flashé
            </span>
            <span v-else-if="invader.status === 'destroyed'" class="tile__badge tile__badge--muted">
              {{ STATUS_LABELS.destroyed }}
            </span>
          </div>
          <div class="tile__text">
            <strong>{{ invader.name }}</strong>
            <span class="muted">{{ places.cityById.get(invader.city)?.name ?? '' }}</span>
          </div>
          <span class="tile__points">{{ invader.points }} pts</span>
        </RouterLink>
      </li>
    </ul>

    <p v-if="error" class="errors">{{ error }}</p>
    <p v-else-if="!loading && count === 0" class="muted gallery__empty">Aucun invader ne correspond à ces critères.</p>
    <p v-if="loading" class="muted gallery__empty">Chargement…</p>
    <div ref="sentinel" class="gallery__sentinel" />

    <!-- Invader modal (child route), over the gallery. -->
    <RouterView />
  </div>
</template>

<style scoped>
.gallery {
  max-width: 960px;
}

.gallery__header p {
  margin: 4px 0 0;
}

.gallery__toolbar {
  display: flex;
  gap: 8px;
}

.gallery__search {
  position: relative;
  flex: 1;
}

.gallery__search-icon {
  position: absolute;
  left: 12px;
  top: 13px;
  color: var(--muted);
  pointer-events: none;
}

.gallery__search .input {
  padding-left: 38px;
}

.gallery__filter-button {
  position: relative;
}

.gallery__filter-button--active {
  color: var(--accent);
}

.gallery__ordering {
  max-width: 260px;
}

.gallery__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.tile {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  text-decoration: none;
}

.tile:focus-visible {
  outline: 2px solid var(--accent);
}

.tile__visual {
  position: relative;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  background: var(--bg);
}

.tile__photo {
  width: 100%;
}

.tile__placeholder {
  width: 45%;
  height: 45%;
  background: currentColor;
  mask: url('@/assets/invader.svg') center / contain no-repeat;
}

.tile--flashed .tile__placeholder {
  color: var(--flashed);
}

.tile--not-flashed .tile__placeholder {
  color: var(--not-flashed);
}

.tile--destroyed .tile__placeholder {
  color: var(--destroyed);
}

.tile__badge {
  position: absolute;
  top: 8px;
  left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-text);
  font-size: 0.75rem;
  font-weight: 600;
}

.tile__badge--muted {
  background: var(--surface-2);
  color: var(--muted);
}

.tile__text {
  display: flex;
  flex-direction: column;
  padding: 8px 10px 0;
  min-width: 0;
}

.tile__text span {
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tile__points {
  padding: 2px 10px 10px;
  font-size: 0.85rem;
  color: var(--muted);
}

.gallery__empty {
  text-align: center;
}

.gallery__sentinel {
  height: 1px;
}
</style>
