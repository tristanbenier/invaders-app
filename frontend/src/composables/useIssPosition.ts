import { onBeforeUnmount, ref, watch, type Ref } from 'vue'

import { type IssPosition, issApi } from '@/api/endpoints'

/** The invader sent to the International Space Station (same constant as the backend's naming.py). */
export const ISS_INVADER_NAME = 'SPACE2ISS'
const POLL_MS = 5000

export function isIssInvader(invader: { name: string }) {
  return invader.name === ISS_INVADER_NAME
}

// Shared by every component: one poll whatever the number of users (map and sheet).
const position = ref<IssPosition | null>(null)
const error = ref<string | null>(null)
let users = 0
let timer: ReturnType<typeof setInterval> | undefined

async function refresh() {
  // No need to follow the ISS in a background tab.
  if (document.hidden) return
  try {
    position.value = await issApi.position()
    error.value = null
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

function acquire() {
  if (users++ === 0) {
    refresh()
    timer = setInterval(refresh, POLL_MS)
  }
}

function release() {
  if (--users === 0) clearInterval(timer)
}

/** Live ISS position, polled every 5 s while `enabled` is true and the component is mounted. */
export function useIssPosition(enabled: Ref<boolean>) {
  let active = false
  watch(
    enabled,
    (on) => {
      if (on && !active) acquire()
      else if (!on && active) release()
      active = on
    },
    { immediate: true },
  )
  onBeforeUnmount(() => {
    if (active) release()
    active = false
  })
  return { position, error }
}
