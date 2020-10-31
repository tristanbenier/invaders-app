<template>
  <div id="markers">
    <InvaderMarker
      v-for="(invader, index) in filteredInvaders"
      :key="index"
      :invader="invader"
      :draggable="isInvaderDraggable(invader)"
      @click="onInvaderClick(invader)"
    />
    <SearchMarker
      v-if="showSearchMarker"
      @click="onSearchMarkerClick"
    />
    <!-- <GeolocationMarker
      v-if="geolocationMarkerPosition"
      :position="geolocationMarkerPosition"
    /> -->
  </div>
</template>

<script>

import InvaderMarker from '@/components/map/markers/InvaderMarker';
// import GeolocationMarker from '@/components/map/markers/GeolocationMarker';
import SearchMarker from '@/components/map/markers/SearchMarker';

export default {
  name: 'Markers',
  components: { InvaderMarker, SearchMarker },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    selectedInvaderId () { return this.$store.getters['map/selectedInvaderId']; },
    filteredInvaders () { return this.$store.getters['map/displayedInvaders']; },
    // geolocationMarkerPosition () {
    //   return this.$store.getters['map/geolocationMarkerPosition'];
    // },
    showSearchMarker () {
      return this.mapMode === this.mapModes.SEARCH_POSITION;
    },
  },
  methods: {
    isInvaderDraggable (invader) {
      return this.mapMode === this.mapModes.MOVE_INVADER && invader.id === this.selectedInvaderId;
    },
    onInvaderClick (invader) {
      this.$emit('click-invader', invader);
    },
    onSearchMarkerClick () {
      this.$emit('click-search-marker');
    },
  },
};
</script>

<style lang="scss">

</style>
