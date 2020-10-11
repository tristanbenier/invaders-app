<template>
  <b-navbar id="navbar" toggleable="sm" fixed="top">
    <b-navbar-brand>
      <NuxtLink :to="{ name: 'index' }">
        Invaders
        <!-- <Logo :height="20" /> -->
      </NuxtLink>
    </b-navbar-brand>

    <b-spinner v-if="loading" variant="primary" small />

    <b-button variant="link" class="open-nav-btn" @click="$emit('open-nav')">
      <b-icon icon="list" variant="light" />
    </b-button>
  </b-navbar>
</template>

<script>
// import Logo from '@/components/Logo';

export default {
  // components: { Logo },
  computed: {
    loading () {
      return this.$store.getters['invaders/loading']('fetch') ||
        this.$store.getters['users/loading']('fetch') ||
        this.$store.getters['status/loading']('fetch') ||
        this.$store.getters['cities/loading']('fetch')
      ;
    },
  },
};
</script>

<style lang="scss" scoped>
#navbar {
  height: $header_height;
  width: 100vw;
  background-color: $grey_darker;

  @media screen and (min-width: 767px) {
    box-shadow: 0px 0px 6px $grey;
  }

  .navbar-brand {
    cursor: pointer;
    padding: 4px;
    margin: 0;

    @media screen and (min-width: 767px) {
      margin: 0 20px;
    }
  }

  .open-nav-btn {
    position: absolute;
    top: 9px;
    right: 5px;
    font-size: 20px;
    color: $grey_lighter;
  }
}
</style>
