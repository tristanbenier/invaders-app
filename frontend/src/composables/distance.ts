import type { LatLng } from './mapContext'

const EARTH_RADIUS_M = 6_371_000

/** Great-circle distance in meters (haversine). */
export function distanceMeters(a: LatLng, b: LatLng) {
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const dLat = toRad(b.lat - a.lat)
  const dLng = toRad(b.lng - a.lng)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(h))
}

export function formatDistance(meters: number) {
  if (meters < 1000) return `${Math.round(meters / 10) * 10} m`
  if (meters < 10_000) return `${(meters / 1000).toFixed(1).replace('.', ',')} km`
  return `${Math.round(meters / 1000)} km`
}
