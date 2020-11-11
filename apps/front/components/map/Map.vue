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
      <Markers
        :filters="filters"
        @click-invader="onInvaderClick"
        @click-search-marker="onSearchMarkerClick"
      />
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
        @geolocate="onGeolocate"
        @click-search="onSearchClick"
        @click-search-suggestion="onSearchSuggestionClick"
        @clear-search="onSearchClear"
        @click-filter="onFilterClick"
      />
    </div>

    <FiltersModal
      :filters="filters"
      :filter-values="mapFilters"
      @click-filter-choice="onFilterUpdate"
      @clear-filters="onFiltersClear"
    />
  </div>
</template>

<script>
import UrlUtils from '@/lib/utils/url';

import FiltersMixin from '@/mixins/FiltersMixin';

import FiltersModal from '@/components/modals/FiltersModal';
import Toolbar from '@/components/map/toolbar/Toolbar';
import Markers from '@/components/map/markers/Markers';

export default {
  components: { Toolbar, Markers, FiltersModal },
  mixins: [FiltersMixin],
  fetch () {
    this.$store.dispatch('users/fetchAll');
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
    this.$store.dispatch('status/fetchAll');
  },
  data () {
    return {
      mapOptions: null,
    };
  },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    mapCenter () { return this.$store.getters['map/center']; },
    mapZoom () { return this.$store.getters['map/zoom']; },
    mapFilters () { return this.$store.getters['map/filters']; },
    filterValues () { return this.mapFilters; }, // Used in FiltersMixin
  },
  beforeMount () {
    this.$fetch();
    this.loadMapConfig();
  },
  methods: {
    onMapClick (e) {
      if (this.mapMode === this.mapModes.ADD_INVADER) {
        const lat = e.latLng.lat();
        const lng = e.latLng.lng();
        this.onInvaderAdd({ lat, lng });
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
    loadMapConfig () {
      const hashParams = UrlUtils.getValuesFromHash(this.$route.hash);
      const mapConfig = JSON.parse(this.$storage.get('map-config') || '{}');
      const lat = (hashParams.lat && parseFloat(hashParams.lat)) || (mapConfig.center && mapConfig.center.lat) || 0;
      const lng = (hashParams.lng && parseFloat(hashParams.lng)) || (mapConfig.center && mapConfig.center.lng) || 0;
      const zoom = (hashParams.zoom && parseInt(hashParams.zoom)) || mapConfig.zoom || 1;
      UrlUtils.removeHashKeys(['lat', 'lng', 'zoom']);

      this.$store.commit('map/SET_CENTER', { lat, lng });
      this.$store.commit('map/SET_ZOOM', zoom);
      this.mapOptions = {
        fullscreenControl: false,
        mapTypeControl: false,
        streetViewControl: false,
        gestureHandling: 'greedy',
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
      if (this.mapMode === this.mapModes.SHOW_INVADERS ||
        this.mapMode === this.mapModes.SHOW_INVADER ||
        this.mapMode === this.mapModes.SEARCH ||
        this.mapMode === this.mapModes.SEARCH_POSITION
      ) {
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
    async onInvaderAdd ({ lat, lng }) {
      await this.$store.dispatch('invaders/initializeInvaderToAdd', { lat, lng });
      this.$bvModal.show('invader-modal');
    },
    onSearchClick () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SEARCH);
    },
    onSearchSuggestionClick ({ lat, lng, addMarker = false }) {
      const zoom = 18;
      const center = { lat, lng };
      if (addMarker) {
        this.$store.commit('map/SET_SEARCH_MARKER_POSITION', center);
      }

      this.$store.commit('map/SET_CENTER', center);
      this.$store.commit('map/SET_ZOOM', zoom);
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SEARCH_POSITION);

      this.updateLocalMapConfig({ center, zoom });
    },
    onSearchMarkerClick () {
      const searchMarkerPosition = this.$store.getters['map/searchMarkerPosition'];
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.ADD_INVADER);
      this.onInvaderAdd(searchMarkerPosition);
    },
    onSearchClear () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADERS);
    },
    onFilterClick () {
      this.$bvModal.show('filters-modal');
    },
    updateFilterValuesFromHash () {
      const hashParams = UrlUtils.getValuesFromHash(this.$route.hash);
      Object.keys(this.filters).forEach((key) => {
        if (!hashParams[key]) {
          this.$store.commit('map/SET_FILTER', { key, value: null });
        } else {
          const value = hashParams[key]
            .split(',')
            .map(v => ['points', 'cities', 'users'].includes(key) ? parseInt(v) : v)
          ;
          this.$store.commit('map/SET_FILTER', { key, value });
        }
      });
    },
    onGeolocate () {
      if (!navigator.geolocation) {
        return;
      }

      navigator.geolocation.getCurrentPosition((pos) => {
        const center = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        this.$store.commit('map/SET_GEOLOCATION_MARKER_POSITION', center);
        this.$store.commit('map/SET_CENTER', center);
        this.$store.commit('map/SET_ZOOM', 18);
      }, (err) => {
        alert('Unable to get location');
        console.error(err);
      });
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
    left: 5px;
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
