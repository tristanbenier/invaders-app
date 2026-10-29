import { defineStore } from 'pinia'
import { computed, reactive } from 'vue'

import type { InvaderFilters } from '@/api/endpoints'
import type { Status } from '@/api/types'

/** Invader filters, shared by the map and (later) the gallery. */
export const useFiltersStore = defineStore('filters', () => {
  const state = reactive({
    flashed: 'all' as 'all' | 'yes' | 'no',
    statuses: [] as Status[],
    points: [] as number[],
    city: null as number | null,
    country: null as number | null,
    flashedBy: null as number | null,
    notFlashedBy: null as number | null,
  })

  const query = computed<InvaderFilters>(() => ({
    flashed: state.flashed === 'all' ? undefined : state.flashed === 'yes' ? 'true' : 'false',
    status: state.statuses.join(','),
    points: state.points.join(','),
    city: state.city,
    country: state.country,
    flashed_by: state.flashedBy,
    not_flashed_by: state.notFlashedBy,
  }))

  const activeCount = computed(
    () =>
      [
        state.flashed !== 'all',
        state.statuses.length > 0,
        state.points.length > 0,
        state.city,
        state.country,
        state.flashedBy,
        state.notFlashedBy,
      ].filter(Boolean).length,
  )

  function reset() {
    Object.assign(state, {
      flashed: 'all',
      statuses: [],
      points: [],
      city: null,
      country: null,
      flashedBy: null,
      notFlashedBy: null,
    })
  }

  return { state, query, activeCount, reset }
})
