import { defineStore } from 'pinia'
import { ref, shallowRef, watch } from 'vue'

import { invadersApi } from '@/api/endpoints'
import type { Invader } from '@/api/types'

import { useFiltersStore } from './filters'

/** Invaders shown on the map, matching the current filters. */
export const useInvadersStore = defineStore('invaders', () => {
  const filters = useFiltersStore()
  const items = ref<Invader[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  // Last change made from a sheet or form, so other lists (gallery) can patch themselves.
  const lastChange = shallowRef<{ type: 'upsert'; invader: Invader } | { type: 'remove'; id: number } | null>(null)
  let requestId = 0

  async function load() {
    const current = ++requestId
    loading.value = true
    error.value = null
    try {
      const result = await invadersApi.list(filters.query)
      // Ignore responses to outdated filters.
      if (current === requestId) items.value = result
    } catch (e) {
      if (current === requestId) error.value = e instanceof Error ? e.message : String(e)
    } finally {
      if (current === requestId) loading.value = false
    }
  }

  watch(() => filters.query, load, { deep: true })

  /** Keep the list in sync after a create/update without reloading everything. */
  function upsert(invader: Invader) {
    lastChange.value = { type: 'upsert', invader }
    // Replace the array so watchers (map markers) see the change.
    const exists = items.value.some((item) => item.id === invader.id)
    items.value = exists
      ? items.value.map((item) => (item.id === invader.id ? invader : item))
      : [...items.value, invader]
  }

  function remove(id: number) {
    lastChange.value = { type: 'remove', id }
    items.value = items.value.filter((item) => item.id !== id)
  }

  return { items, loading, error, lastChange, load, upsert, remove }
})
