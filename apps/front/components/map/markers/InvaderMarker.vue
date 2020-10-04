<template>
  <GmapMarker
    :position="invader.coordinates"
    :clickable="true"
    :draggable="false"
    :icon="icon"
    @click="onInvaderClick"
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
  },
  computed: {
    backgroundColor () {
      if (this.invader.users.length) {
        return '#003366';
      }
      return this.invader.status.color;
    },
    roundColor () {
      return '#fff';
    },
    icon () {
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="20" height="20" focusable="false" role="img" aria-label="geo alt fill" fill="${this.backgroundColor}" class="bi-geo-alt-fill mx-auto b-icon bi">
                     <path fill-rule="evenodd" d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                     <circle cx="8" cy="6" fill="${this.roundColor}" r="3"/>
                  </svg>`;
      const url = 'data:image/svg+xml;charset=UTF-8;base64,' + btoa(svg);
      return url;
      // return `/img/markers/marker-icon-${this.invader.color}.png`;
      // return {
      //   path: 'M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
      //   fillColor: '#F0F00',
      //   fillOpacity: 1,
      //   strokeWeight: 1,
      //   scale: 1,
      // };
    },
  },
  methods: {
    onInvaderClick () {
      this.$emit('click');
    },
  },
};
</script>
