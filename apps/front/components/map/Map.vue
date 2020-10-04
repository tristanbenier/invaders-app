<template>
  <div id="map">
    <GmapMap
      ref="map"
      :center="mapCenter"
      :zoom="mapZoom"
      :options="mapOptions"
      @center_changed="onMapCenterChanged"
      @zoom_changed="onMapZoomChanged"
    >
      <Markers @click-invader="onInvaderClick" />
    </GmapMap>

    <InvaderModal
      @close="onInvaderModalClose"
    />
  </div>
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
      mapOptions: null,
    };
  },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
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
      this.mapOptions = {
        mapTypeControl: false,
        streetViewControl: false,
      };
    },
    updateLocalMapConfig (data = {}) {
      const mapConfig = {
        ...JSON.parse(this.$storage.get('map-config') || '{}'),
        ...data,
      };
      this.$storage.set('map-config', JSON.stringify(mapConfig));
    },
    onInvaderClick (invader) {
      if (this.mapMode === this.mapModes.SHOW_INVADERS || this.mapMode === this.mapModes.SHOW_INVADER) {
        this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
        this.$store.commit('map/SET_SELECTED_INVADER_ID', invader.id);
        this.$bvModal.show('invader-modal');
      }
    },
    onInvaderModalClose () {
      this.$bvModal.hide('invader-modal');
      if (this.mapMode !== this.mapModes.ADD_INVADER) {
        this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADERS);
      }
    },
  },
};
</script>

<style lang="scss">
#map {
  width: 100%;
  height: 100%;
}
</style>
