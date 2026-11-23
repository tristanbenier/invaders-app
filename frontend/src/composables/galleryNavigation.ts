import { inject, type InjectionKey, type Ref } from 'vue'

import type { Invader } from '@/api/types'

/** The gallery's current list (filters, search and ordering applied), for the invader modal's previous / next. */
export interface GalleryNavigation {
  items: Ref<Invader[]>
  /** Total number of matching invaders (all pages). */
  count: Ref<number | null>
  hasMore: Ref<boolean>
  /** Loads the next page of the list. */
  loadMore(): Promise<void>
}

export const GALLERY_NAVIGATION: InjectionKey<GalleryNavigation> = Symbol('gallery-navigation')

/** Null outside the gallery (e.g. in the sheet over the map). */
export function useGalleryNavigation(): GalleryNavigation | null {
  return inject(GALLERY_NAVIGATION, null)
}
