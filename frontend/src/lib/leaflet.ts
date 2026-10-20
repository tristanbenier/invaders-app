// leaflet.markercluster is a legacy plugin that extends the global `L`.
// This module must be imported before the plugin so the global exists.
import L from 'leaflet'

declare global {
  interface Window {
    L: typeof L
  }
}

window.L = L

export default L
