<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

import AppIcon from './AppIcon.vue'

// modal: centered dialog over a backdrop (outside the map), instead of a panel over the map.
const props = defineProps<{ title?: string; modal?: boolean }>()
const emit = defineEmits<{ close: [] }>()

function onKeydown(event: KeyboardEvent) {
  if (props.modal && event.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <!-- A modal leaves its parent's stacking context so it covers the whole app (navigation included). -->
  <Teleport to="body" :disabled="!modal">
    <div v-if="modal" class="sheet-backdrop" @click="emit('close')" />
    <section class="sheet" :class="{ 'sheet--modal': modal }" role="dialog" :aria-modal="modal" :aria-label="title">
      <header class="sheet__header">
        <slot name="header">
          <h2 class="sheet__title">{{ title }}</h2>
        </slot>
        <button class="btn btn--icon sheet__close" type="button" aria-label="Fermer" @click="emit('close')">
          <AppIcon name="close" />
        </button>
      </header>
      <div class="sheet__body">
        <slot />
      </div>
    </section>
  </Teleport>
</template>

<style scoped>
.sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  max-height: 70%;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-top: 1px solid var(--border);
  border-radius: 18px 18px 0 0;
  box-shadow: var(--shadow);
  z-index: 1000;
}

.sheet__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 12px 8px 16px;
}

.sheet__title {
  flex: 1;
  font-size: 1.15rem;
}

.sheet__close {
  margin-left: auto;
  border: none;
  background: transparent;
}

.sheet__body {
  overflow-y: auto;
  padding: 0 16px 16px;
}

.sheet-backdrop {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.55);
  z-index: 1100;
}

.sheet--modal {
  position: fixed;
  max-height: 85%;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1101;
}

/* Side panel on larger screens. */
@media (min-width: 768px) {
  .sheet:not(.sheet--modal) {
    top: 72px;
    left: 12px;
    right: auto;
    bottom: 12px;
    width: 380px;
    max-height: none;
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
}

@media (min-width: 768px) {
  .sheet--modal {
    top: 50%;
    left: 50%;
    right: auto;
    bottom: auto;
    width: min(480px, calc(100% - 32px));
    max-height: 85%;
    transform: translate(-50%, -50%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
}
</style>
