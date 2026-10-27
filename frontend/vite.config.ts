import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Single project-wide .env at the repository root (only VITE_* vars reach the browser).
const ENV_DIR = '..'

export default defineConfig(({ mode }) => {
  // Django serves the page (templates/index.html) and mounts the app: in dev, the scripts come
  // from this Vite server (hot reload); once built, Django serves dist/ under /static/.
  // Read from the root .env, like Django's django-vite settings and invitation links.
  const env = loadEnv(mode, ENV_DIR, ['DJANGO_VITE_DEV_SERVER_', 'FRONTEND_URL'])
  const devServerPort = Number(env.DJANGO_VITE_DEV_SERVER_PORT || 5174)
  const devServer = `http://${env.DJANGO_VITE_DEV_SERVER_HOST || 'localhost'}:${devServerPort}`
  const django = new URL(env.FRONTEND_URL || 'http://localhost:8080').origin

  return {
    base: '/static/',
    plugins: [
      vue(),
      VitePWA({
        registerType: 'autoUpdate',
        // Registered in main.ts: the worker is served by Django at /sw.js to control the whole site.
        injectRegister: false,
        // Icons are already precached by globPatterns below (with the /static/ prefix).
        includeManifestIcons: false,
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
          // Not the bundles: their URL carries a content hash (?v=…) and the browser HTTP cache
          // keeps them, while a precached copy would be served stale after each new build.
          globIgnores: ['sw.js', 'bundle.min.js', 'bundle.min.css'],
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
    envDir: ENV_DIR,
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    build: {
      // Exactly two app files with fixed names, so commits of frontend/dist stay readable:
      // dist/bundle.min.js (lazy routes inlined) and dist/bundle.min.css. The Django page adds a
      // content hash to their URL (?v=…) to bust browser caches.
      cssCodeSplit: false,
      rollupOptions: {
        input: 'src/main.ts',
        output: {
          codeSplitting: false,
          entryFileNames: 'bundle.min.js',
          assetFileNames: (asset) =>
            asset.names.some((name) => name.endsWith('.css')) ? 'bundle.min.css' : 'assets/[name]-[hash][extname]',
        },
      },
    },
    server: {
      port: devServerPort,
      strictPort: true,
      // Asset URLs must point to this server, the page itself being served by Django.
      origin: devServer,
      cors: { origin: django },
    },
  }
})
