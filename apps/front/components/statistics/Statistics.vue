<template>
  <b-container>
    <div v-if="citiesLoading || invadersLoading" class="text-center mt-5">
      <div v-if="citiesLoading" class="mt-3">
        <b-spinner variant="light" small />&nbsp;&nbsp;&nbsp;Loading cities...
      </div>

      <div v-if="!citiesLoading && invadersLoading" class="mt-3">
        <b-spinner variant="light" small />&nbsp;&nbsp;&nbsp;Loading invaders...
      </div>
    </div>

    <b-row v-if="!citiesLoading && !invadersLoading" class="cities-list mt-3">
      <b-col
        v-for="city in citiesList"
        :key="city.id"
        cols="6"
        md="4"
        lg="3"
        class="city-item"
      >
        <CityItem
          :city="city"
          :invaders="cityInvaders(city).length"
          :points="cityPoints(city)"
          @click="onCityClick(city)"
        />
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
import CityItem from '@/components/statistics/CityItem';

export default {
  components: { CityItem },
  fetch () {
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
  },
  computed: {
    citiesLoading () {
      return this.$store.getters['cities/loading']('fetch');
    },
    invadersLoading () {
      return this.$store.getters['invaders/loading']('fetch');
    },
    citiesList () {
      return [...this.$store.getters['cities/citiesList']]
        .sort((a, b) => a.name.localeCompare(b.name))
      ;
    },
    invadersList () {
      return [...this.$store.getters['invaders/invadersList']];
    },
  },
  mounted () {
    this.$fetch();
  },
  methods: {
    cityInvaders (city) {
      return this.$store.getters['invaders/invadersByCityId'](city.id);
    },
    cityPoints (city) {
      return this.cityInvaders(city)
        .reduce((total, i) => {
          if (!isNaN(i.points)) {
            total += parseInt(i.points);
          }
          return total;
        }, 0)
      ;
    },
    onCityClick (city) {
      return this.$router.push({ name: 'statistics-citySlug', params: { citySlug: city.slug } });
    },
  },
};
</script>

<style lang="scss" scoped>
.city-item {
  margin-bottom: 0.625rem;
  margin-bottom: 1rem;
  box-sizing: border-box;
}
</style>
