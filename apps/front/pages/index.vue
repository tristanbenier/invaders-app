<template>
  <div id="map-page">
    <div id="map-container">
      <GmapMap
        ref="map"
        :cluster="{options: {styles: clusterStyle}}"
        :center="{lat: locations[0].lat, lng: locations[0].lng}"
        :options="{fullscreenControl: false, styles: mapStyle}"
        :zoom="6"
      >
        <GmapMarker
          v-for="location in locations"
          :key="location.id"
          :position="{lat: location.lat, lng: location.lng}"
          :options="{}"
          @click="currentLocation = location"
        >
          <GmapInfoWindow :options="{maxWidth: 200}">
            <code>
              lat: {{ location.lat }},
              lng: {{ location.lng }}
            </code>
          </GmapInfoWindow>
        </GmapMarker>
      </GmapMap>
    </div>
  </div>
</template>

<script>

export default {
  data () {
    return {
      currentLocation: {},
      circleOptions: {},
      locations: [
        {
          lat: 44.933076,
          lng: 15.629058,
        },
        {
          lat: 45.815,
          lng: 15.9819,
        },
        {
          lat: 45.12,
          lng: 16.21,
        },
      ],
      mapStyle: [],
      clusterStyle: [
        {
          url: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m1.png',
          width: 56,
          height: 56,
          textColor: '#fff',
        },
      ],
    };
  },
};
</script>

<style lang="scss">
#map-page {
  width: 100%;
  height: 100%;

  #map-container {
    width: 50%;
    height: 50%;

    .vue-map-container {
      width: 100%;
      height: 100%;
    }
  }
}
</style>
