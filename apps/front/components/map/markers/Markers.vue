<template>
  <div id="markers">
    <InvaderMarker
      v-for="(invader, index) in filteredInvaders"
      :key="index"
      :invader="invader"
      @click="onInvaderClick(invader)"
    />
    <!-- <PlaceMarker
      v-if="placeMarkerPosition"
      :position="placeMarkerPosition"
    />
    <GeolocationMarker
      v-if="geolocationMarkerPosition"
      :position="geolocationMarkerPosition"
    /> -->
  </div>
</template>

<script>

import InvaderMarker from '@/components/map/markers/InvaderMarker';
// import GeolocationMarker from '@/components/map/markers/GeolocationMarker';
// import PlaceMarker from '@/components/map/markers/PlaceMarker';

export default {
  name: 'Markers',
  components: { InvaderMarker },
  // components: { InvaderMarker, GeolocationMarker, PlaceMarker },
  computed: {
    invaders () {
      return this.$store.getters['data/invaders'];
    },
    filteredInvaders () {
      return this.$store.getters['invaders/invadersList'];
      // return this.$store.getters['map/filteredInvaders'];
    },
    // placeMarkerPosition () {
    //   return this.$store.getters['map/placeMarkerPosition'];
    // },
    // geolocationMarkerPosition () {
    //   return this.$store.getters['map/geolocationMarkerPosition'];
    // },
  },
  methods: {
    onInvaderClick (invader) {
      this.$emit('click-invader', invader);
    },
  },
};
</script>

<style lang="scss">

</style>
