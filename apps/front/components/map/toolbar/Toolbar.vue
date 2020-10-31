<template>
  <div class="toolbar">
    <div class="searchbar-container">
      <Searchbar
        v-if="mapMode === mapModes.SEARCH"
        @click-suggestion="$emit('click-search-suggestion', $event)"
        @clear="$emit('clear-search')"
      />
    </div>

    <div class="toolbar-item" @click="$emit('click-filter')">
      <b-badge
        v-if="mapFiltersCount"
        variant="primary"
        class="filter-badge"
        pill
      >{{ mapFiltersCount }}</b-badge>
      <b-icon icon="filter" />
    </div>

    <div class="toolbar-item" :style="{ fontSize: '33px' }" @click="$emit('add-invader')">
      <b-icon icon="plus" />
    </div>

    <div v-if="mapMode !== mapModes.SEARCH" class="toolbar-item" :style="{ fontSize: '17px' }" @click="$emit('click-search')">
      <b-icon icon="search" />
    </div>

    <!-- <div class="toolbar-item" @click="$emit('geolocate')">
      <b-icon icon="geo-alt-fill" />
    </div> -->
  </div>
</template>

<script>
import Searchbar from '@/components/map/toolbar/Searchbar';

export default {
  components: { Searchbar },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    mapFiltersCount () {
      const filters = this.$store.getters['map/filters'];
      return Object.keys(filters).filter(key => filters[key]).length;
    },
  },
};
</script>

<style lang="scss" scoped>
.toolbar {
  float: right;

  .searchbar-container {
    position: absolute;
    top: 0;
    left: 0;
    right: 80px;
  }

  .toolbar-item {
    position: relative;
    float: right;
    text-align: center;
    width: 35px;
    height: 35px;
    font-size: 20px;
    line-height: 30px;
    background-color: $grey_darker;
    border-radius: 5px;
    margin: 0 0 0 5px;
    padding: 0;
    cursor: pointer;
  }

  .filter-badge {
    font-family: sans-serif;
    font-size: 10px;
    position: absolute;
    width: 15px;
    height: 15px;
    top: -4px;
    left: -4px;
    text-align: center;
    padding: 0;
    line-height: 15px;
    font-weight: 100;
  }
}
</style>
