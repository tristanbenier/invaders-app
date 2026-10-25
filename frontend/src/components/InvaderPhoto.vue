<script setup lang="ts">
/**
 * Square photo frame: the whole photo is shown (contain), and the space left by non-square
 * photos is filled with the same photo enlarged and blurred (cover). Size it with CSS on the
 * component (width); its height follows (aspect-ratio 1).
 */
defineProps<{ src: string; alt: string; lazy?: boolean }>()
</script>

<template>
  <div class="photo">
    <img :src="src" alt="" aria-hidden="true" class="photo__backdrop" :loading="lazy ? 'lazy' : undefined" />
    <img :src="src" :alt="alt" class="photo__image" :loading="lazy ? 'lazy' : undefined" />
  </div>
</template>

<style scoped>
.photo {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  background: var(--bg);
}

.photo img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* Same file as the photo: downloaded once. Enlarged so the blur does not show soft edges. */
.photo__backdrop {
  object-fit: cover;
  filter: blur(18px) brightness(0.7) saturate(1.2);
  transform: scale(1.15);
}

.photo__image {
  object-fit: contain;
}
</style>
