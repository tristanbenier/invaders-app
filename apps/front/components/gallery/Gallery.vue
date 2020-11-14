<template>
  <b-container>
    <b-row class="pt-3">
      <b-col>
        <p class="m-0">
          Found invaders: {{ invadersList.length }}
        </p>
        <p class="m-0">
          Total points: {{ filteredPoints }}
        </p>
      </b-col>
      <b-col class="text-right">
        <b-button
          variant="outline-secondary"
          size="sm"
          class="filter-button"
          @click="onFiltersClick"
        >
          <b-badge
            v-if="galleryFiltersCount"
            variant="primary"
            class="filter-badge"
            pill
          >{{ galleryFiltersCount }}</b-badge>
          <b-icon icon="filter" />
        </b-button>
      </b-col>
    </b-row>

    <b-row class="invaders-list mt-3">
      <b-col
        v-for="invader in invadersList"
        :key="invader.id"
        cols="4"
        sm="3"
        md="2"
        lg="1"
        class="invader-item"
      >
        <GalleryItem
          :invader="invader"
          @click="onInvaderClick(invader)"
        />
      </b-col>
    </b-row>

    <FiltersModal
      :filters="filters"
      :filter-values="galleryFilters"
      @click-filter-choice="onFilterUpdate"
      @clear-filters="onFiltersClear"
    />
  </b-container>
</template>

<script>
import UrlUtils from '@/lib/utils/url';

import FiltersMixin from '@/mixins/FiltersMixin';

import GalleryItem from '@/components/gallery/GalleryItem';
import FiltersModal from '@/components/modals/FiltersModal';

export default {
  components: { GalleryItem, FiltersModal },
  mixins: [FiltersMixin],
  fetch () {
    this.$store.dispatch('users/fetchAll');
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
    this.$store.dispatch('status/fetchAll');
  },
  computed: {
    invadersList () {
      return [...this.$store.getters['gallery/displayedInvaders']]
        .sort((a, b) => {
          if (a.city.prefix !== b.city.prefix) {
            return a.city.prefix.localeCompare(b.city.prefix);
          }
          if (a.name.length === b.name.length) {
            return a.name.localeCompare(b.name);
          }
          return a.name.length - b.name.length;
        })
      ;
    },
    filteredPoints () {
      return this.invadersList.reduce((total, invader) => {
        if (!isNaN(invader.points)) {
          total += parseInt(invader.points);
        }

        return total;
      }, 0);
    },
    galleryFilters () { return this.$store.getters['gallery/filters']; },
    galleryFiltersCount () {
      return Object.keys(this.galleryFilters).filter(key => this.galleryFilters[key]).length;
    },
    filterValues () { return this.galleryFilters; }, // Used in FiltersMixin
  },
  mounted () {
    this.$fetch();
  },
  methods: {
    onInvaderClick (invader) {
      this.$store.commit('map/SET_SELECTED_INVADER_ID', invader.id);
      this.$bvModal.show('invader-modal');
    },
    onFiltersClick () {
      this.$bvModal.show('filters-modal');
    },
    updateFilterValuesFromHash () {
      const hashParams = UrlUtils.getValuesFromHash(this.$route.hash);
      Object.keys(this.filters).forEach((key) => {
        if (!hashParams[key]) {
          this.$store.commit('gallery/SET_FILTER', { key, value: null });
        } else {
          const value = hashParams[key]
            .split(',')
            .map(v => ['points', 'cities', 'users'].includes(key) ? parseInt(v) : v)
          ;
          this.$store.commit('gallery/SET_FILTER', { key, value });
        }
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.filter-button {
  position: relative;

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

.invader-item {
  padding-left: 5px;
  padding-right: 5px;
  margin-bottom: 0.625rem;
  box-sizing: border-box;
}
</style>
