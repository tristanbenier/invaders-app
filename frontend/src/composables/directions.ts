import type { LatLng } from './mapContext'

export type DirectionsApp = 'apple' | 'google'

/** iPhone, iPod and iPad, including iPads that report a desktop Safari user agent. */
function isIOS() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
}

/**
 * Walking directions to a point: Apple Plans on iOS; Google Maps elsewhere. Android opens the
 * Google Maps app for this URL (app link), other devices the Google Maps website.
 */
export function directionsTo({ lat, lng }: LatLng): { app: DirectionsApp; url: string } {
  const destination = `${lat},${lng}`
  if (isIOS()) {
    return { app: 'apple', url: `https://maps.apple.com/?daddr=${destination}&dirflg=w` }
  }
  return { app: 'google', url: `https://www.google.com/maps/dir/?api=1&destination=${destination}&travelmode=walking` }
}
