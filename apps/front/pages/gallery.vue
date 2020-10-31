<template>
  <b-container>
    <h1>Gallery</h1>

    <b-row class="invaders-list">
      <b-col
        v-for="invader in invadersList"
        :key="invader.id"
        cols="4"
        sm="3"
        md="2"
        lg="1"
        class="invader-item"
      >
        <GalleryItem
          :invader="invader"
          @click="onInvaderClick(invader)"
        />
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
import GalleryItem from '@/components/gallery/GalleryItem';

export default {
  components: { GalleryItem },
  fetch () {
    this.$store.dispatch('users/fetchAll');
    this.$store.dispatch('cities/fetchAll');
    this.$store.dispatch('invaders/fetchAll');
    this.$store.dispatch('status/fetchAll');
  },
  computed: {
    invadersList () {
      return [...this.$store.getters['invaders/invadersList']]
        .sort((a, b) => {
          if (a.city.prefix !== b.city.prefix) {
            return a.city.prefix.localeCompare(b.city.prefix);
          }
          if (a.name.length === b.name.length) {
            return a.name.localeCompare(b.name);
          }
          return a.name.length - b.name.length;
        })
      ;
    },
  },
  mounted () {
    this.$fetch();
  },
  methods: {
    onInvaderClick (invader) {
      this.$store.commit('map/SET_SELECTED_INVADER_ID', invader.id);
      this.$bvModal.show('invader-modal');
    },
  },
};
</script>

<style lang="scss" scoped>
.invader-item {
  padding-left: 5px;
  padding-right: 5px;
  margin-bottom: 0.625rem;
  box-sizing: border-box;
}
</style>
