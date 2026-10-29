<script setup lang="ts">
import AppIcon from './AppIcon.vue'
</script>

<template>
  <nav class="nav" aria-label="Navigation principale">
    <RouterLink to="/" class="nav__link" :class="{ 'nav__link--active': $route.path === '/' || $route.path.startsWith('/invaders') }">
      <AppIcon name="map" />
      <span>Carte</span>
    </RouterLink>
    <RouterLink to="/gallery" class="nav__link" active-class="nav__link--active">
      <AppIcon name="grid" />
      <span>Galerie</span>
    </RouterLink>
    <RouterLink to="/stats" class="nav__link" active-class="nav__link--active">
      <AppIcon name="chart" />
      <span>Stats</span>
    </RouterLink>
    <RouterLink to="/to-flash" class="nav__link" active-class="nav__link--active">
      <AppIcon name="target" />
      <span>À flasher</span>
    </RouterLink>
    <RouterLink to="/team" class="nav__link" active-class="nav__link--active">
      <AppIcon name="team" />
      <span>Équipe</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.nav {
  display: flex;
  justify-content: space-around;
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1000;
}

.nav__link {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 0;
  color: var(--muted);
  font-size: 0.7rem;
  text-decoration: none;
  white-space: nowrap;
}

.nav__link--active {
  color: var(--accent);
}
</style>
