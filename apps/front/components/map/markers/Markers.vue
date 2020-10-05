<template>
  <div id="markers">
    <InvaderMarker
      v-for="(invader, index) in filteredInvaders"
      :key="index"
      :invader="invader"
      :draggable="isInvaderDraggable(invader)"
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
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    selectedInvaderId () { return this.$store.getters['map/selectedInvaderId']; },
    filteredInvaders () { return this.$store.getters['map/displayedInvaders']; },
    // placeMarkerPosition () {
    //   return this.$store.getters['map/placeMarkerPosition'];
    // },
    // geolocationMarkerPosition () {
    //   return this.$store.getters['map/geolocationMarkerPosition'];
    // },
  },
  methods: {
    isInvaderDraggable (invader) {
      return this.mapMode === this.mapModes.MOVE_INVADER && invader.id === this.selectedInvaderId;
    },
    onInvaderClick (invader) {
      this.$emit('click-invader', invader);
    },
  },
};
</script>

<style lang="scss">

</style>
