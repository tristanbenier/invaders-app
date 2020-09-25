<template>
  <GmapMarker
    :position="invader.coordinates"
    :clickable="true"
    :draggable="false"
    @click="onInvaderClick"
  />
</template>

<script>
import Invader from '@/entities/Invader';

export default {
  name: 'InvaderMarker',
  props: {
    invader: {
      type: Invader,
      default: null,
    },
  },
  computed: {
    icon () {
      return `/img/markers/marker-icon-${this.invader.color}.png`;
    },
  },
  methods: {
    onInvaderClick () {
      this.$emit('click');
    },
  },
};
</script>
