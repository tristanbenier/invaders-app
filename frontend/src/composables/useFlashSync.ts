import { onBeforeUnmount, readonly, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import { invadersApi } from '@/api/endpoints'
import { useAuthStore } from '@/stores/auth'
import { useInvadersStore } from '@/stores/invaders'

const POLL_MS = 60_000

// Last sync failed (Flash Invaders down or its API changed): manual flashing comes back meanwhile.
const failing = ref(false)

/** Whether the Flash Invaders sync is currently failing (shared by every component). */
export function useFlashSyncFailing() {
  return readonly(failing)
}

/**
 * Flashes here what the member flashed in the Flash Invaders app: a full sync when the app
 * opens (or the sync is turned on), then a check every minute while the tab is visible.
 */
export function useFlashSync() {
  const auth = useAuthStore()
  const invaders = useInvadersStore()
  let timer: ReturnType<typeof setInterval> | undefined
  let running = false

  async function sync(full = false) {
    if (running || document.hidden) return
    running = true
    try {
      const { created } = await invadersApi.syncFlashes(full)
      failing.value = false
      // New flashes change the markers' colors: reload the map's invaders.
      if (created.length) await invaders.load()
    } catch (error) {
      // Being rate limited is not a failure; anything else is, until a sync succeeds again.
      if (!(error instanceof ApiError && error.status === 429)) failing.value = true
    } finally {
      running = false
    }
  }

  function onVisible() {
    if (!document.hidden) sync()
  }

  function stop() {
    clearInterval(timer)
    timer = undefined
    document.removeEventListener('visibilitychange', onVisible)
  }

  watch(
    () => auth.me?.flash_sync_enabled ?? false,
    (enabled) => {
      stop()
      failing.value = false
      if (!enabled) return
      sync(true)
      timer = setInterval(sync, POLL_MS)
      document.addEventListener('visibilitychange', onVisible)
    },
    { immediate: true },
  )

  onBeforeUnmount(stop)
}
