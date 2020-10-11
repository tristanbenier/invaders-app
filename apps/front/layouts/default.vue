<template>
  <div class="default-layout-container">
    <Header @open-nav="onNavOpenClick" />

    <Nav @close-nav="onNavCloseClick" />

    <div class="page-container">
      <Nuxt />
    </div>
  </div>
</template>

<script>
import Header from '@/components/Header';
import Nav from '@/components/Nav';

export default {
  components: { Header, Nav },
  methods: {
    onNavOpenClick () {
      this.$bvModal.show('nav-modal');
    },
    onNavCloseClick () {
      this.$bvModal.hide('nav-modal');
    },
  },
};
</script>

<style lang="scss">
.default-layout-container {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;

  .page-container {
    position: relative;
    background-color: $grey_lighter;
    margin-top: $header_height;
    color: $white;
    font-size: 14px;
    min-height: calc(100vh - #{$header_height});
  }
}
</style>
