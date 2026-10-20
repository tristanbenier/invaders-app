import { inject, type InjectionKey, type Ref } from 'vue'

export interface LatLng {
  lat: number
  lng: number
}

/** What MapView exposes to the sheets displayed over the map. */
export interface MapContext {
  focus(point: LatLng, zoom?: number): void
  /** Lets the user drag a marker; resolves with the chosen point, or null if cancelled. */
  pickLocation(initial: LatLng, message: string): Promise<LatLng | null>
  /** Current user position, if geolocation is available. */
  userPosition: Ref<LatLng | null>
  center(): LatLng
}

export const MAP_CONTEXT: InjectionKey<MapContext> = Symbol('map-context')

/** Null when the component is not displayed over the map (e.g. in the gallery). */
export function useOptionalMapContext(): MapContext | null {
  return inject(MAP_CONTEXT, null)
}

export function useMapContext(): MapContext {
  const context = inject(MAP_CONTEXT)
  if (!context) throw new Error('useMapContext() must be used inside MapView')
  return context
}
