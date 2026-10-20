import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

const backend = 'http://localhost:8000'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/apple-touch-icon.png'],
      manifest: {
        name: 'Invaders',
        short_name: 'Invaders',
        description: 'La carte des Space Invaders de votre équipe.',
        lang: 'fr',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#14121f',
        theme_color: '#14121f',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Only the app shell is cached: API data must always be fresh (no offline mode in V1).
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//, /^\/media\//, /^\/admin\//, /^\/static\//],
        runtimeCaching: [
          {
            // Map tiles rarely change: serve them from cache to save data and speed up the map.
            urlPattern: /^https:\/\/tile\.openstreetmap\.org\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: { maxEntries: 1000, maxAgeSeconds: 7 * 24 * 60 * 60 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  // Single project-wide .env at the repository root (only VITE_* vars are exposed).
  envDir: '..',
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    // The API and uploaded images are served by Django; same origin keeps session cookies simple.
    proxy: {
      '/api': backend,
      '/media': backend,
    },
  },
})
