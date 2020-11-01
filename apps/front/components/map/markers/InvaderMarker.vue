<template>
  <GmapMarker
    :position="invader.coordinates"
    :clickable="true"
    :draggable="draggable"
    :icon="icon"
    @click="onInvaderClick"
    @drag="onInvaderDragged"
  />
</template>

<script>
import Invader from '@/entities/Invader';

export default {
  name: 'InvaderMarker',
  props: {
    invader: {
      type: Invader,
      default: null,
    },
    draggable: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    users () { return this.$store.getters['users/usersList']; },
    mapZoom () { return this.$store.getters['map/zoom']; },
    size () {
      return (this.mapZoom >= 12) ? 20 : 10;
    },
    backgroundColor () {
      if (this.invader.users.length) {
        if (this.invader.users.length === 1) {
          return this.invader.users[0].color;
        } else if (this.invader.users.length === this.users.length) {
          return '#13931c';
        }
      }
      return this.invader.status.color;
    },
    roundColor () {
      return '#fff';
    },
    icon () {
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="${this.size}" height="${this.size}" focusable="false" role="img" aria-label="geo alt fill" fill="${this.backgroundColor}" class="bi-geo-alt-fill mx-auto b-icon bi">
                     <path fill-rule="evenodd" d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                     <circle cx="8" cy="6" fill="${this.roundColor}" r="3"/>
                  </svg>`
      ;
      return `data:image/svg+xml;charset=UTF-8;base64,${btoa(svg)}`;
    },
  },
  methods: {
    onInvaderClick () {
      this.$emit('click');
    },
    onInvaderDragged (position) {
      this.$store.commit('invaders/SET_ITEM_POSITION', {
        id: this.invader.id,
        latitude: position.latLng.lat(),
        longitude: position.latLng.lng(),
      });
    },
  },
};
</script>
