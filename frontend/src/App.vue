<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AppNav from './components/AppNav.vue'

const route = useRoute()
const showNav = computed(() => !route.meta.public && route.name !== undefined)
</script>

<template>
  <div class="app" :class="{ 'app--with-nav': showNav }">
    <main class="app__main">
      <RouterView />
    </main>
    <AppNav v-if="showNav" />
  </div>
</template>

<style scoped>
/* Pinned to the visible screen: mobile browsers keep fixed elements above their toolbars, while
   a document taller than the screen would push the bottom nav out of view. */
.app {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
}

.app > :deep(.nav) {
  flex-shrink: 0;
}

.app__main {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow-y: auto;
}
</style>
