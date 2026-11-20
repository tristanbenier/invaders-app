import type { MapTheme } from '@/api/types'

// Vector basemap drawn by MapLibre from OpenFreeMap's OpenStreetMap tiles, relayed and
// cached by Django under /tiles/ (style, tiles, fonts and sprites: no third-party origin).
// Our own "day" and "night" styles (backend basemap_styles.py). The attribution
// (OpenFreeMap, OpenMapTiles, OpenStreetMap) comes from the tile set.
const BASEMAP_STYLES = { light: 'day', dark: 'night' } as const

export function basemapStyle(theme: MapTheme) {
  return new URL(`/tiles/styles/${BASEMAP_STYLES[theme]}`, window.location.origin).href
}
