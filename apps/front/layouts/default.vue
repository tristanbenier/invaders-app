<template>
  <div class="default-layout-container">
    <Header @open-nav="onNavOpenClick" />

    <Nav
      @logout="onLogoutClick"
      @close-nav="onNavCloseClick"
    />

    <div class="page-container">
      <Nuxt />
    </div>

    <InvaderModal
      @close="onInvaderModalClose"
    />
  </div>
</template>

<script>
import Header from '@/components/Header';
import Nav from '@/components/Nav';
import InvaderModal from '@/components/modals/InvaderModal';

export default {
  components: { Header, Nav, InvaderModal },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
  },
  methods: {
    onNavOpenClick () {
      this.$bvModal.show('nav-modal');
    },
    onNavCloseClick () {
      this.$bvModal.hide('nav-modal');
    },
    onLogoutClick () {
      this.$store.dispatch('auth/logout');
      this.$router.push({ name: 'login' });
    },
    onInvaderModalClose () {
      this.$bvModal.hide('invader-modal');

      if (this.$route.name === 'index' && ![this.mapModes.MOVE_INVADER].includes(this.mapMode)) {
        this.$store.commit('map/SET_SELECTED_INVADER_ID', null);
        this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADERS);
      } else if (this.$route.name === 'gallery') {
        // TODO
      }
    },
  },
};
</script>

<style lang="scss">
.default-layout-container {
  position: relative;
  height: 100%;
  overflow-x: hidden;

  .page-container {
    position: relative;
    background-color: $grey_darker;
    margin-top: $header_height;
    color: $white;
    font-size: 14px;
    min-height: calc(100% - #{$header_height});
  }
}
</style>
