<template>
  <GmapMarker
    :position="geolocationMarkerPosition"
    :clickable="false"
    :draggable="false"
    icon="/img/marker-geolocation.png"
  />
</template>

<script>
export default {
  computed: {
    geolocationMarkerPosition () { return this.$store.getters['map/geolocationMarkerPosition']; },
  },
};
</script>
