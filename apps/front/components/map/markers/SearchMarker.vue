<template>
  <GmapMarker
    :position="position"
    :clickable="true"
    :draggable="true"
    @click="onClick"
    @drag="onDragged"
  />
</template>

<script>
export default {
  computed: {
    position () {
      return this.$store.getters['map/searchMarkerPosition'];
    },
  },
  methods: {
    onClick () {
      this.$emit('click');
    },
    onDragged (position) {
      this.$store.commit('map/SET_SEARCH_MARKER_POSITION', {
        lat: position.latLng.lat(),
        lng: position.latLng.lng(),
      });
    },
  },
};
</script>
