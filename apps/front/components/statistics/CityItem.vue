<template>
  <div class="city-item" @click="$emit('click')">
    <UiBlurImageLoader
      v-if="city.fileUrl"
      :src="city.fileUrl"
      :small-src="city.thumbnailUrl"
      class="city-item-thumbnail"
    />

    <div class="info">
      <div class="name">
        {{ city.name }}
      </div>
      {{ invaders }} / {{ points }} pts
    </div>
  </div>
</template>

<script>
import City from '@/entities/City';

export default {
  props: {
    city: {
      type: City,
      default: null,
    },
    invaders: {
      type: Number,
      default: 0,
    },
    points: {
      type: Number,
      default: 0,
    },
  },
};
</script>

<style lang="scss" scoped>
.city-item {
  position: relative;
  background: $grey_dark;
  cursor: pointer;

  .city-item-thumbnail {
    position: absolute;
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
  }

  .info {
    position: absolute;
    bottom: 0px;
    left: 0;
    right: 0;
    background-color: rgba($grey_darker, 0.5);
    color: #fff;
    font-size: 12px;
    padding: 10px;

    .name {
      text-transform: uppercase;
      font-size: 16px;
    }
  }

  &::after {
    content: '';
    display: block;
    padding-bottom: 100%;
  }
}
</style>
