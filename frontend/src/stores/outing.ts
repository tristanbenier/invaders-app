import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

import { outingsApi } from '@/api/endpoints'
import type { Outing } from '@/api/types'
import { useLocalStorage } from '@/composables/useLocalStorage'

import { useInvadersStore } from './invaders'

/** The outing shown on the map ("outing mode"), remembered per browser across reloads. */
export const useOutingStore = defineStore('outing', () => {
  const activeId = useLocalStorage<number | null>(
    'invaders.activeOuting',
    null,
    (value): value is number | null => value === null || typeof value === 'number',
  )
  const active = ref<Outing | null>(null)
  const stopIds = computed(() => new Set(active.value?.stops.map((stop) => stop.invader.id) ?? []))
  const progress = computed(() => {
    const stops = active.value?.stops ?? []
    return { done: stops.filter((stop) => stop.done).length, total: stops.length }
  })

  async function refresh() {
    if (activeId.value === null) {
      active.value = null
      return
    }
    try {
      active.value = await outingsApi.get(activeId.value)
    } catch {
      // Deleted meanwhile (or no longer reachable): leave the outing mode.
      activeId.value = null
      active.value = null
    }
  }

  function show(outing: Outing) {
    activeId.value = outing.id
    active.value = outing
  }

  /** Keeps the map in sync after an edit of the outing shown. */
  function update(outing: Outing) {
    if (outing.id === activeId.value) active.value = outing
  }

  function hide() {
    activeId.value = null
    active.value = null
  }

  // Flashes (button or sync) reload the map's invaders: refresh the done flags with them.
  const invaders = useInvadersStore()
  watch(() => invaders.items, refresh)

  return { activeId, active, stopIds, progress, refresh, show, update, hide }
})
