import { onBeforeUnmount, watch } from 'vue'

import { invadersApi } from '@/api/endpoints'
import { useAuthStore } from '@/stores/auth'
import { useInvadersStore } from '@/stores/invaders'

const POLL_MS = 60_000

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
      // New flashes change the markers' colors: reload the map's invaders.
      if (created.length) await invaders.load()
    } catch {
      // Flash Invaders unreachable or rate limited: the next tick tries again.
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
      if (!enabled) return
      sync(true)
      timer = setInterval(sync, POLL_MS)
      document.addEventListener('visibilitychange', onVisible)
    },
    { immediate: true },
  )

  onBeforeUnmount(stop)
}
