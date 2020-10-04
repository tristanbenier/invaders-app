<template>
  <div class="my-3">
    <InvaderForm
      :invader="invader"
      :error="null"
      :loading="editionLoading"
      @cancel="$emit('cancel')"
      @submit="$emit('edit', $event)"
    />
  </div>
</template>

<script>
import Invader from '@/entities/Invader';

import InvaderForm from '@/components/forms/InvaderForm';

export default {
  components: { InvaderForm },
  props: {
    invader: {
      type: Invader,
      default: null,
    },
  },
  computed: {
    editionLoading () {
      return this.$store.getters['invaders/loading'](`update:${this.invader.id}`);
    },
  },
};
</script>
