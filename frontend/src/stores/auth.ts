import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import { authApi } from '@/api/endpoints'
import type { MapTheme, Me } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const me = ref<Me | null>(null)
  const loaded = ref(false)

  const isAuthenticated = computed(() => me.value !== null)
  const isAdmin = computed(() => me.value?.role === 'admin')

  async function fetchMe() {
    try {
      me.value = await authApi.me()
    } catch (error) {
      // The API answers 403 (not 401) to anonymous requests.
      if (!(error instanceof ApiError && error.status === 403)) throw error
      me.value = null
    } finally {
      loaded.value = true
    }
  }

  async function login(email: string, password: string) {
    me.value = await authApi.login(email, password)
  }

  async function acceptInvitation(payload: Parameters<typeof authApi.acceptInvitation>[0]) {
    me.value = await authApi.acceptInvitation(payload)
  }

  /** Applied immediately, saved on the account; reverted if saving fails. */
  async function setMapTheme(theme: MapTheme) {
    if (!me.value || me.value.map_theme === theme) return
    const previous = me.value.map_theme
    me.value.map_theme = theme
    try {
      me.value = await authApi.updateMe({ map_theme: theme })
    } catch (error) {
      if (me.value) me.value.map_theme = previous
      throw error
    }
  }

  async function logout() {
    await authApi.logout()
    me.value = null
  }

  return { me, loaded, isAuthenticated, isAdmin, fetchMe, login, acceptInvitation, setMapTheme, logout }
})
