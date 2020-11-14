<template>
  <div class="my-3">
    <InvaderForm
      :invader="invader"
      :error="addError"
      :loading="initializationLoading || addLoading"
      @cancel="$emit('cancel')"
      @submit="$emit('add', $event)"
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
    initializationLoading () {
      return this.$store.getters['invaders/loading']('add:initialize');
    },
    addError () {
      return this.$store.getters['invaders/error']('add');
    },
    addLoading () {
      return this.$store.getters['invaders/loading']('add');
    },
  },
};
</script>
