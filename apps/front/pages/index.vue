<template>
  <div id="map-page" class="site-page">
    <div id="map-container">
      <Map />
    </div>
  </div>
</template>

<script>
import Map from '@/components/map/Map';

export default {
  components: { Map },
};
</script>

<style lang="scss">
#map-page {
  position: absolute;
  width: 100%;
  height: 100%;

  #map-container {
    position: relative;
    width: 100%;
    height: 100%;

    .vue-map-container {
      width: 100%;
      height: 100%;
    }
  }
}
</style>
