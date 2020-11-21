<template>
  <b-container>
    <b-row class="cities-list mt-3">
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
    this.$store.dispatch('users/fetchAll');
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
    this.$store.dispatch('status/fetchAll');
  },
  computed: {
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
      return this.invadersList
        .filter(i => i.city.id === city.id)
      ;
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
