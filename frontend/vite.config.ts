import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Django serves the page (templates/index.html) and mounts the app: in dev, the scripts come
// from this Vite server (hot reload); once built, Django serves dist/ under /static/.
const DEV_SERVER = 'http://localhost:5173'
const DJANGO = 'http://localhost:8000'

export default defineConfig({
  base: '/static/',
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      // Registered in main.ts: the worker is served by Django at /sw.js to control the whole site.
      injectRegister: false,
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
        // Relative to the manifest, itself served from /static/.
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Only static files are cached: the page is rendered by Django and API data must stay
        // fresh (no offline mode in V1).
        globPatterns: ['**/*.{js,css,svg,png,woff2}'],
        globIgnores: ['sw.js'],
        modifyURLPrefix: { '': '/static/' },
        navigateFallback: null,
        inlineWorkboxRuntime: true,
        runtimeCaching: [
          {
            // Map tiles (relayed by Django) rarely change: serve them from cache to save data.
            urlPattern: ({ url, sameOrigin }) => sameOrigin && url.pathname.startsWith('/tiles/'),
            handler: 'CacheFirst',
            options: {
              cacheName: 'map-tiles',
              expiration: { maxEntries: 1000, maxAgeSeconds: 7 * 24 * 60 * 60 },
              cacheableResponse: { statuses: [200] },
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
  build: {
    // Read by django-vite to inject the hashed files into the Django page.
    manifest: true,
    rollupOptions: { input: 'src/main.ts' },
  },
  server: {
    port: 5173,
    strictPort: true,
    // Asset URLs must point to this server, the page itself being served by Django.
    origin: DEV_SERVER,
    cors: { origin: DJANGO },
  },
})
