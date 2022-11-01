<template>
  <CityStatistics
    :city-slug="citySlug"
  />
</template>

<script>
import CityStatistics from '@/components/statistics/CityStatistics.vue';

export default {
  components: { CityStatistics },
  asyncData ({ app, params }) {
    return {
      citySlug: params.citySlug,
    };
  },
  async validate ({ params, app, store }) {
    const citySlug = params.citySlug;
    if (!/^[a-z]+(?:-[a-z]+)*$/.test(citySlug)) {
      return false;
    }

    /* validated if active product 'la-carte' found */
    await store.dispatch('cities/fetchAll');
    const city = store.getters['cities/cityBySlug'](citySlug);

    return !!city;
  },
};
</script>

<style lang="scss" scoped>

</style>
