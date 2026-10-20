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
.app {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

.app__main {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow-y: auto;
}
</style>
