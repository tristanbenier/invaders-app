<template>
  <b-navbar id="navbar" toggleable="sm" fixed="top">
    <b-navbar-brand>
      <NuxtLink :to="{ name: 'index' }">
        Invaders
        <!-- <Logo :height="20" /> -->
      </NuxtLink>
    </b-navbar-brand>

    <b-button variant="link" class="open-nav-btn" @click="$emit('open-nav')">
      <b-icon icon="list" variant="light" />
    </b-button>
  </b-navbar>
</template>

<script>
// import Logo from '@/components/Logo';

export default {
  // components: { Logo },
};
</script>

<style lang="scss" scoped>
#navbar {
  height: $header_height;
  width: 100vw;
  background-color: $black;

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
    color: $purple_dark;
  }
}
</style>
