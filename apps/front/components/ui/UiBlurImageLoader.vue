<template>
  <img class="blur-image" :src="imageSrc">
</template>

<script>
export default {
  props: {
    src: {
      type: String,
      default: null,
    },
    smallSrc: {
      type: String,
      default: null,
    },
  },
  data () {
    return {
      imageSrc: this.smallSrc,
    };
  },
  mounted () {
    const img = new Image();
    img.onload = () => {
      this.imageSrc = this.src;
    };
    img.src = this.src;
  },
};
</script>
