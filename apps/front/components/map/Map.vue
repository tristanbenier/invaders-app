<template>
  <GmapMap
    ref="map"
    :center="mapCenter"
    :zoom="mapZoom"
    @center_changed="onMapCenterChanged"
    @zoom_changed="onMapZoomChanged"
  >
    <Markers @click-invader="onInvaderClick" />

    <InvaderModal />
  </GmapMap>
</template>

<script>
import Markers from '@/components/map/markers/Markers';
import InvaderModal from '@/components/map/modals/InvaderModal';

export default {
  components: { Markers, InvaderModal },
  fetch () {
    this.$store.dispatch('invaders/fetchAll');
  },
  data () {
    return {
      mapCenter: null,
      mapZoom: null,
    };
  },
  beforeMount () {
    this.$fetch();
    this.loadLocalMapConfig();
  },
  methods: {
    onMapCenterChanged (mapCenter) {
      const center = { lat: mapCenter.lat(), lng: mapCenter.lng() };
      this.updateLocalMapConfig({ center });
    },
    onMapZoomChanged (zoom) {
      this.updateLocalMapConfig({ zoom });
    },
    loadLocalMapConfig () {
      const mapConfig = JSON.parse(this.$storage.get('map-config') || '{}');
      const mapCenterLat = (mapConfig.center && mapConfig.center.lat) || 0;
      const mapCenterLng = (mapConfig.center && mapConfig.center.lng) || 0;
      this.mapCenter = {
        lat: mapCenterLat,
        lng: mapCenterLng,
      };
      this.mapZoom = mapConfig.zoom || 1;
    },
    updateLocalMapConfig (data = {}) {
      const mapConfig = {
        ...JSON.parse(this.$storage.get('map-config') || '{}'),
        ...data,
      };
      this.$storage.set('map-config', JSON.stringify(mapConfig));
    },
    onInvaderClick (invader) {
      this.$bvModal.show('invader-modal');
      console.log('click on invader');
      console.log(invader);
    },
  },
};
</script>

<style lang="scss">

</style>
