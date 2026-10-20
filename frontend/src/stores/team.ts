import { defineStore } from 'pinia'
import { ref } from 'vue'

import { teamApi } from '@/api/endpoints'
import type { Team } from '@/api/types'

export const useTeamStore = defineStore('team', () => {
  const team = ref<Team | null>(null)

  async function load() {
    team.value = await teamApi.get()
  }

  return { team, load }
})
