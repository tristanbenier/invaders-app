<template>
  <div class="searchbar">
    <input
      id="search-input"
      v-model="inputValue"
      type="text"
      :style="searchInputStyle"
    >

    <div v-if="showSuggestions" id="search-suggestions">
      <div
        v-for="(invader, index) in suggestions.invaders"
        :key="`invaders-suggestion-${index}`"
        class="suggestion-item"
        @click="onSuggestionClick('invader', invader)"
      >
        <span class="suggestion-item-icon">
          <Invader color="#fff" size="20" />
        </span>
        <span class="suggestion-item-name">
          {{ invader.name }}
        </span>
        <span class="suggestion-item-info">
          {{ invader.points }} pts,
          {{ (invader.status && invader.status.name) || '' }}
        </span>
      </div>

      <div
        v-for="(place, index) in suggestions.places"
        :key="`places-suggestion-${index}`"
        class="suggestion-item"
        @click="onSuggestionClick('place', place)"
      >
        <span class="suggestion-item-icon">
          <b-icon icon="geo-alt-fill" />
        </span>
        <span class="suggestion-item-name">
          {{ place.formatted_address }}
        </span>
        <span class="suggestion-item-info">
          {{ place.formatted_address }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { throttle } from '@/lib/utils/callable';

import Invader from '@/components/_common/Invader';

export default {
  components: { Invader },
  data () {
    return {
      input: null,
      inputValue: null,
      suggestions: { invaders: [], places: [] },
    };
  },
  computed: {
    invadersList () { return this.$store.getters['invaders/invadersList']; },
    filteredInvaders () {
      if (!this.inputValue || this.inputValue.length < 3) {
        return [];
      }
      return this.invadersList
        .filter(i => i.name.indexOf(this.inputValue) === 0)
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
    showSuggestions () {
      return !!this.inputValue;
    },
    searchInputStyle () {
      const style = {};

      if (this.showSuggestions) {
        style.borderRadius = '5px 5px 0 0';
      }

      return style;
    },
  },
  watch: {
    inputValue () {
      if (this.inputValue) {
        this.suggestions.invaders = this.filteredInvaders.slice(0, 5);
        throttle(this.searchPlaces(this.inputValue), 500);
      } else {
        this.suggestions = {
          invaders: [],
          places: [],
        };
        this.onClear();
      }
    },
  },
  methods: {
    async searchPlaces (query) {
      try {
        const places = await this.$geocoding.getPlacesFromQuery(query);
        this.suggestions.places = places;
      } catch (e) {
        // Do nothing
      }
    },
    onSuggestions (e) {
      this.suggestions = {
        invaders: this.filteredInvaders.slice(0, 5),
      };
    },
    onSuggestionClick (type, element) {
      const position = type === 'invader'
        ? (element.coordinates || null)
        : { lat: element.geometry.location.lat(), lng: element.geometry.location.lng() }
      ;

      if (!position) {
        return;
      }

      const { lat, lng } = position;
      this.$emit('click-suggestion', { lat, lng, addMarker: type === 'place' });
    },
    onClear () {
      this.$emit('clear');
    },
  },
};
</script>

<style lang="scss" scoped>
.searchbar {
  #search-input {
    background-color: $grey_darker;
    color: #fff;
    height: 35px;
    border-radius: 5px;
    border: none;
    padding: 0 1em;
    width: 100%;
  }

  #search-suggestions {
    position: absolute;
    top: 100%;
    z-index: 100;
    left: 0px;
    right: auto;
    display: block;
    width: 100%;
    background-color: $grey_darker;
    border-top: 1px solid $grey_dark;
    border-radius: 0 0 5px 5px;

    .suggestion-item {
      cursor: pointer;
      height: 46px;
      line-height: 46px;
      padding-left: 18px;
      overflow: hidden;

      .suggestion-item-icon {
        white-space: normal;
        margin-right: 10px;
        width: 14px;
        height: 20px;
        vertical-align: middle;
      }

      .suggestion-item-name {
        white-space: normal;
      }

      .suggestion-item-info {
        white-space: normal;
        font-size: smaller;
        margin-left: 12px;
        color: #aaaaaa;
      }

      &:hover {
        background-color: $grey_dark;
      }
    }
  }
}
</style>
<style lang="scss">
.ap-input-icon {
  right: 10px;
}

.ap-dropdown-menu {
  display: none !important;
}
</style>
