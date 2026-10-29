import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { placesApi } from '@/api/endpoints'
import type { City, Country } from '@/api/types'

/** Team cities and countries: small lists, loaded once and kept in memory. */
export const usePlacesStore = defineStore('places', () => {
  const cities = ref<City[]>([])
  const countries = ref<Country[]>([])
  let loading: Promise<void> | null = null

  const cityById = computed(() => new Map(cities.value.map((city) => [city.id, city])))
  const cityByPrefix = computed(() => new Map(cities.value.map((city) => [city.prefix, city])))

  function load(force = false) {
    if (!loading || force) {
      loading = Promise.all([placesApi.cities(), placesApi.countries()]).then(([c, k]) => {
        cities.value = c
        countries.value = k
      })
      loading.catch(() => (loading = null))
    }
    return loading
  }

  async function createCity(payload: Parameters<typeof placesApi.createCity>[0]) {
    const city = await placesApi.createCity(payload)
    // A new country may have been created along with the city.
    await load(true)
    return city
  }

  async function updateCity(id: number, payload: Parameters<typeof placesApi.updateCity>[1]) {
    const city = await placesApi.updateCity(id, payload)
    // The country may have been created on the fly.
    await load(true)
    return city
  }

  return { cities, countries, cityById, cityByPrefix, load, createCity, updateCity }
})
