import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from './stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
  }
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
    {
      path: '/invitation/:token',
      name: 'invitation',
      component: () => import('./views/InvitationView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('./views/MapView.vue'),
      children: [
        { path: '', name: 'map', component: { render: () => null } },
        { path: 'invaders/new', name: 'invader-new', component: () => import('./views/InvaderFormView.vue') },
        { path: 'invaders/:id', name: 'invader', component: () => import('./views/InvaderSheet.vue') },
        { path: 'invaders/:id/edit', name: 'invader-edit', component: () => import('./views/InvaderFormView.vue') },
      ],
    },
    {
      path: '/gallery',
      component: () => import('./views/GalleryView.vue'),
      children: [
        { path: '', name: 'gallery', component: { render: () => null } },
        { path: 'invaders/:id', name: 'gallery-invader', component: () => import('./views/InvaderSheet.vue') },
      ],
    },
    { path: '/to-flash', name: 'to-flash', component: () => import('./views/ToFlashView.vue') },
    { path: '/stats', name: 'stats', component: () => import('./views/StatsView.vue') },
    { path: '/team', name: 'team', component: () => import('./views/TeamView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.loaded) await auth.fetchMe()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: to.fullPath === '/' ? {} : { next: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) return { name: 'map' }
})
