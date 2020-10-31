<template>
  <div class="gallery-item" :style="galleryItemStyle" @click="$emit('click')">
    <div class="gallery-item-name">
      {{ invader.name }}
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

      if (this.invader.images.length) {
        style.backgroundImage = `url(${this.invader.images[0].url})`;
      }

      return style;
    },
  },
};
</script>

<style lang="scss" scoped>
.gallery-item {
  background: $grey_dark;
  background-size: cover;
  background-position: center;
  cursor: pointer;

  .gallery-item-name {
    position: absolute;
    width: 100%;
    bottom: 0;
    text-align: center;
    color: #fff;
    background-color: rgba($grey_darker, 0.5);
  }

  &::after {
    content: '';
    display: block;
    padding-bottom: 100%;
  }
}
</style>
