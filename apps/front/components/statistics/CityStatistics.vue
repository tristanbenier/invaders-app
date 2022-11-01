<template>
  <div>
    <div v-if="city">
      <UiPieChart :height="200" :chart-data="statusPieChartData" :options="{}" />
    </div>
  </div>
</template>

<script>

export default {
  props: {
    citySlug: {
      type: String,
      default: '',
    },
  },
  fetch () {
    this.$store.dispatch('status/fetchAll');
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
  },
  computed: {
    city () {
      return this.$store.getters['cities/cityBySlug'](this.citySlug);
    },
    statusList () {
      return this.$store.getters['status/statusesList'];
    },
    cityInvaders () {
      if (!this.city) {
        return [];
      }

      return this.$store.getters['invaders/invadersByCityId'](this.city.id);
    },
    statusPieChartData () {
      return {
        options: { tooltips: { enabled: false } },
        labels: this.statusList.map(s => s.name),
        datasets: [{
          data: this.statusList.map(s => this.cityInvaders.filter(i => i.status.id === s.id).length),
          backgroundColor: this.statusList.map(s => s.color),
        }],
      };
    },
  },
  beforeCreate () {
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
  },
};
</script>

<style lang="scss" scoped>

</style>
