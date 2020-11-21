<template>
  <div class="gallery-item" :style="galleryItemStyle" @click="$emit('click')">
    <UiBlurImageLoader
      v-if="invader.images.length"
      :src="invader.images[0].url"
      :small-src="invader.images[0].thumbnailUrl"
      class="gallery-item-thumbnail"
    />
    <div class="gallery-item-name">
      {{ invader.name }} / {{ invader.points }} pts
    </div>
  </div>
</template>

<script>
import Invader from '@/entities/Invader';

export default {
  props: {
    invader: {
      type: Invader,
      default: null,
    },
  },
  computed: {
    galleryItemStyle () {
      const style = {};

      return style;
    },
  },
};
</script>

<style lang="scss" scoped>
.gallery-item {
  position: relative;
  background: $grey_dark;
  cursor: pointer;

  .gallery-item-thumbnail {
    position: absolute;
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
  }

  .gallery-item-name {
    position: absolute;
    width: 100%;
    bottom: 4px;
    text-align: center;
    color: #fff;
    background-color: rgba($grey_darker, 0.5);

    @media (min-width: 577px) {
      font-size: 12px;
    }

    @media (min-width: 768px) {
      font-size: 12px;
      opacity: 0;
    }
  }

  &:hover {
    .gallery-item-name {
      opacity: 1;
    }
  }

  &::after {
    content: '';
    display: block;
    padding-bottom: 100%;
  }
}
</style>
