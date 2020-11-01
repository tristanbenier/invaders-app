<template>
  <b-navbar id="navbar" toggleable="sm" fixed="top">
    <b-navbar-brand>
      <NuxtLink :to="{ name: 'index' }">
        Invaders
      </NuxtLink>
    </b-navbar-brand>

    <b-spinner v-if="loading" class="app-loading" variant="light" small />

    <b-button variant="link" class="open-nav-btn" @click="$emit('open-nav')">
      <b-icon icon="list" variant="light" />
    </b-button>
  </b-navbar>
</template>

<script>
export default {
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

  .navbar-brand {
    cursor: pointer;
    padding: 4px;
    margin: 0;

    @media screen and (min-width: 767px) {
      margin: 0 20px;
    }
  }

  .app-loading {
    position: absolute;
    top: 22px;
    right: 52px;
  }

  .open-nav-btn {
    position: absolute;
    top: 7px;
    right: 5px;
    font-size: 20px;
    color: $grey_lighter;
  }
}
</style>
