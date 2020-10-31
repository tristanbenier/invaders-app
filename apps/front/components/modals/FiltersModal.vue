<template>
  <UiModal
    id="filters-modal"
    header-title="filters"
    :header-actions="[
      { icon: 'trash', name: 'clear-filters' },
    ]"
    @on-action="onHeaderAction"
    @close="$emit('close')"
  >
    <b-row class="filters my-3">
      <b-col cols="12">
        <div
          v-for="(filter, key) in filters"
          :key="key"
          class="filter-section"
          :class="`filter-${key}`"
        >
          <label>{{ filter.label }}</label>
          <div>
            <b-badge
              v-for="(choice, i) in filter.choices"
              :key="`choice-${i}`"
              class="filter-choice-item m-1 px-2 py-1"
              :variant="filterChoiceSelected(key, choice.value) ? 'primary' : 'secondary'"
              @click="$emit('click-filter-choice', { key, value: choice.value })"
            >
              {{ choice.label }}
            </b-badge>
          </div>
        </div>
      </b-col>
    </b-row>
  </UiModal>
</template>

<script>
export default {
  props: {
    filters: {
      type: Object,
      default: () => ({}),
    },
    filterValues: {
      type: Object,
      default: () => ({}),
    },
  },
  methods: {
    onHeaderAction (actionName) {
      switch (actionName) {
        case 'clear-filters': {
          this.$emit('clear-filters');
          break;
        }
      }
    },
    filterChoiceSelected (key, value) {
      return this.filterValues[key] && this.filterValues[key].includes(value);
    },
  },
};
</script>

<style lang="scss" scoped>
.filters {
  .filter-section {
    .filter-choice-item {
      cursor: pointer;
    }
  }
}
</style>
