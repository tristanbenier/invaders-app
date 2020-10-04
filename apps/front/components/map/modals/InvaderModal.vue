<template>
  <UiModal
    id="invader-modal"
    :header-title="modalTitle"
    :header-actions="[
      { icon: 'pencil', name: 'edit' },
      { icon: 'trash', name: 'remove' },
    ]"
    scrollable
    @on-action="onHeaderAction"
    @close="$emit('close')"
  >
    <InvaderModalShowContent
      v-if="mapMode === mapModes.SHOW_INVADER"
      :invader="selectedInvader"
    />

    <InvaderModalEditContent
      v-if="mapMode === mapModes.EDIT_INVADER"
      :invader="selectedInvader"
      @edit="onEdit"
      @cancel="onEditCancel"
    />
  </UiModal>
</template>

<script>
import InvaderModalShowContent from '@/components/map/modals/InvaderModalShowContent';
import InvaderModalEditContent from '@/components/map/modals/InvaderModalEditContent';

export default {
  components: { InvaderModalShowContent, InvaderModalEditContent },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    selectedInvaderId () { return this.$store.getters['map/selectedInvaderId']; },
    selectedInvader () { return this.$store.getters['map/selectedInvader']; },
    modalTitle () {
      if (this.selectedInvader) {
        return this.selectedInvader.name;
      }
      if (this.mapMode === this.mapModes.ADD_INVADER) {
        return 'Add invader';
      }
      return '';
    },
  },
  methods: {
    onHeaderAction (actionName) {
      switch (actionName) {
        case 'edit': {
          this.onEditClick();
          break;
        }
        case 'remove': {
          this.onRemoveClick();
          break;
        }
      }
    },
    onEditClick () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.EDIT_INVADER);
    },
    onEditCancel () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
    },
    async onEdit ({ formData, imagesToAdd, imagesToDelete }) {
      if (this.selectedInvaderId) {
        if (await this.$store.dispatch('invaders/updateInvader', { id: this.selectedInvaderId, data: formData })) {
          this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
        }
      }
    },
    async onRemoveClick () {
      if (await this.$bvModal.msgBoxConfirm('Do you really want to remove this invader ?')) {
        if (await this.$store.dispatch('invaders/removeInvader', { id: this.selectedInvaderId })) {
          this.$emit('close');
        }
      }
    },
  },
};
</script>

<style lang="scss" scoped>

</style>
