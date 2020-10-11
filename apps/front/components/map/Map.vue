<template>
  <div id="map">
    <GmapMap
      ref="map"
      :center="mapCenter"
      :zoom="mapZoom"
      :options="mapOptions"
      @center_changed="onMapCenterChanged"
      @zoom_changed="onMapZoomChanged"
      @click="onMapClick"
    >
      <Markers @click-invader="onInvaderClick" />
    </GmapMap>

    <div v-if="mapMode === mapModes.MOVE_INVADER || mapMode === mapModes.ADD_INVADER" id="action-bar-container" class="text-center">
      <div v-if="mapMode === mapModes.MOVE_INVADER">
        <span class="float-left">Save this position</span>

        <b-button variant="primary" size="sm" class="float-right ml-2" @click="onInvaderMoveSave">
          Save
        </b-button>

        <b-button variant="secondary" size="sm" class="float-right ml-2" @click="onInvaderMoveCancel">
          Cancel
        </b-button>
      </div>
      <div v-if="mapMode === mapModes.ADD_INVADER">
        <span class="float-left"> Add position</span>

        <b-button variant="secondary" size="sm" class="float-right ml-2" @click="onInvaderAddCancel">
          Cancel
        </b-button>
      </div>
    </div>

    <div id="toolbar-container">
      <Toolbar
        @add-invader="onInvaderAddClick"
      />
    </div>

    <InvaderModal
      @close="onInvaderModalClose"
    />
  </div>
</template>

<script>
import Toolbar from '@/components/map/toolbar/Toolbar';
import Markers from '@/components/map/markers/Markers';
import InvaderModal from '@/components/map/modals/InvaderModal';

export default {
  components: { Toolbar, Markers, InvaderModal },
  fetch () {
    this.$store.dispatch('users/fetchAll');
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
    this.$store.dispatch('status/fetchAll');
  },
  data () {
    return {
      mapCenter: null,
      mapOptions: null,
    };
  },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    mapZoom () { return this.$store.getters['map/zoom']; },
  },
  beforeMount () {
    this.$fetch();
    this.loadLocalMapConfig();
  },
  methods: {
    async onMapClick (e) {
      if (this.mapMode === this.mapModes.ADD_INVADER) {
        const lat = e.latLng.lat();
        const lng = e.latLng.lng();

        await this.$store.dispatch('invaders/initializeInvaderToAdd', { lat, lng });
        this.$bvModal.show('invader-modal');
      }
    },
    onMapCenterChanged (mapCenter) {
      const center = { lat: mapCenter.lat(), lng: mapCenter.lng() };
      this.updateLocalMapConfig({ center });
    },
    onMapZoomChanged (zoom) {
      this.$store.commit('map/SET_ZOOM', zoom);
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
      this.$store.commit('map/SET_ZOOM', mapConfig.zoom || 1);
      this.mapOptions = {
        fullscreenControl: false,
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

      if (![this.mapModes.MOVE_INVADER].includes(this.mapMode)) {
        this.$store.commit('map/SET_SELECTED_INVADER_ID', null);
        this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADERS);
      }
    },
    onInvaderMoveCancel () {
      this.$root.$emit('map::move-invader::cancel');
      this.$bvModal.show('invader-modal');
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
    },
    onInvaderMoveSave () {
      this.$root.$emit('map::move-invader::save');
      this.$bvModal.show('invader-modal');
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
    },
    onInvaderAddClick () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.ADD_INVADER);
    },
    onInvaderAddCancel () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADERS);
    },
  },
};
</script>

<style lang="scss">
#map {
  width: 100%;
  height: 100%;

  #toolbar-container {
    position: absolute;
    top: 5px;
    right: 5px;
  }

  #action-bar-container {
    position: absolute;
    bottom: 5px;
    height: 50px;
    left: 10%;
    width: 80%;
    border-radius: 5px;
    line-height: 36px;
    padding: 7px 15px 7px 30px;
    background-color: $grey_darker;

    @media screen and (min-width: 567px) {
      left: 25%;
      width: 50%;
    }
  }
}
</style>
