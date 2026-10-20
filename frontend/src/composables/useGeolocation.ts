import { onBeforeUnmount, ref } from 'vue'

export interface Position {
  lat: number
  lng: number
  accuracy: number
}

const ERROR_MESSAGES: Record<number, string> = {
  1: "La géolocalisation est refusée. Autorisez-la dans les réglages du navigateur.",
  2: 'Position indisponible.',
  3: 'La géolocalisation a pris trop de temps.',
}

/** Live position via watchPosition; stops when the component unmounts. */
export function useGeolocation() {
  const position = ref<Position | null>(null)
  const error = ref<string | null>(null)
  let watchId: number | null = null

  function start() {
    if (watchId !== null) return
    if (!('geolocation' in navigator)) {
      error.value = "La géolocalisation n'est pas disponible sur cet appareil."
      return
    }
    watchId = navigator.geolocation.watchPosition(
      ({ coords }) => {
        error.value = null
        position.value = { lat: coords.latitude, lng: coords.longitude, accuracy: coords.accuracy }
      },
      (e) => {
        error.value = ERROR_MESSAGES[e.code] ?? e.message
        if (e.code === e.PERMISSION_DENIED) stop()
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 },
    )
  }

  function stop() {
    if (watchId !== null) navigator.geolocation.clearWatch(watchId)
    watchId = null
  }

  onBeforeUnmount(stop)

  return { position, error, start, stop }
}
