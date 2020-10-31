<template>
  <UiModal
    id="invader-modal"
    :header-title="modalTitle"
    :header-actions="modalHeaderActions"
    scrollable
    @on-action="onHeaderAction"
    @close="$emit('close')"
  >
    <InvaderModalAddContent
      v-if="displayInvaderAddContent"
      :invader="invaderToAdd"
      @cancel="onAddCancel"
      @add="onAdd"
    />

    <InvaderModalShowContent
      v-if="displayInvaderShowContent"
      :invader="selectedInvader"
    />

    <InvaderModalEditContent
      v-if="displayInvaderEditContent"
      :invader="selectedInvader"
      @edit="onEdit"
      @cancel="onEditCancel"
    />
  </UiModal>
</template>

<script>
import InvaderModalShowContent from '@/components/modals/InvaderModalShowContent';
import InvaderModalEditContent from '@/components/modals/InvaderModalEditContent';
import InvaderModalAddContent from '@/components/modals/InvaderModalAddContent';

export default {
  components: { InvaderModalShowContent, InvaderModalEditContent, InvaderModalAddContent },
  computed: {
    mapModes () { return this.$store.getters['map/modes']; },
    mapMode () { return this.$store.getters['map/selectedMode']; },
    displayInvaderAddContent () {
      return this.mapMode === this.mapModes.ADD_INVADER;
    },
    displayInvaderShowContent () {
      return this.$route.name === 'gallery' || this.mapMode === this.mapModes.SHOW_INVADER;
    },
    displayInvaderEditContent () {
      return this.$route.name === 'index' && this.mapMode === this.mapModes.EDIT_INVADER;
    },
    invaderToAdd () {
      return this.$route.name === 'index' && this.$store.getters['invaders/invaderToAdd'];
    },
    selectedInvaderId () {
      return this.$store.getters['map/selectedInvaderId'];
    },
    selectedInvader () {
      return this.$store.getters['map/selectedInvader'];
    },
    modalTitle () {
      if (this.selectedInvader) {
        return `${this.selectedInvader.name} > ${this.selectedInvader.points} pts`;
      } else if (this.$route.name === 'index' && this.mapMode === this.mapModes.ADD_INVADER) {
        return 'Add invader';
      }

      return '';
    },
    modalHeaderActions () {
      if (this.$route.name === 'index') {
        if (this.mapMode === this.mapModes.SHOW_INVADER) {
          return [
            { icon: 'pencil', name: 'map-edit' },
          ];
        } else if (this.mapMode === this.mapModes.EDIT_INVADER) {
          return [
            { icon: 'geo-alt-fill', name: 'map-move' },
            { icon: 'trash', name: 'map-remove' },
          ];
        }
      } else if (this.$route.name === 'gallery') {
        return [
          { icon: 'geo-alt-fill', name: 'gallery-show' },
        ];
      }

      return [];
    },
  },
  methods: {
    onHeaderAction (actionName) {
      switch (actionName) {
        case 'map-move': {
          this.onMapMoveClick();
          break;
        }
        case 'map-edit': {
          this.onMapEditClick();
          break;
        }
        case 'map-remove': {
          this.onMapRemoveClick();
          break;
        }
        case 'gallery-show': {
          this.onGalleryShowClick();
          break;
        }
      }
    },
    onMapMoveClick () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.MOVE_INVADER);

      const clearListeners = () => {
        this.$root.$off('map::move-invader::save');
        this.$root.$off('map::move-invader::cancel');
      };

      // Add listeners for toolbar
      this.$root.$on('map::move-invader::save', () => {
        const data = {
          latitude: this.selectedInvader.latitude,
          longitude: this.selectedInvader.longitude,
        };
        this.$store.dispatch('invaders/updateInvader', {
          id: this.selectedInvaderId,
          data,
        });
        clearListeners();
      });
      this.$root.$on('map::move-invader::cancel', () => {
        this.$store.commit('invaders/SET_ITEM_POSITION', {
          id: this.selectedInvaderId,
          ...this.selectedInvader.position,
        });
        clearListeners();
      });

      this.$emit('close');
    },
    onMapEditClick () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.EDIT_INVADER);
    },
    onEditCancel () {
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
    },
    onGalleryShowClick () {
      const { lat, lng } = this.selectedInvader.coordinates;
      this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADERS);
      this.$router.push({ name: 'index', hash: `#lat=${lat}&lng=${lng}&zoom=20` });
      this.$emit('close');
    },
    async onEdit ({ formData }) {
      if (this.selectedInvaderId) {
        if (await this.$store.dispatch('invaders/updateInvader', { id: this.selectedInvaderId, data: formData })) {
          this.$store.commit('map/SET_SELECTED_MODE', this.mapModes.SHOW_INVADER);
        }
      }
    },
    async onMapRemoveClick () {
      if (await this.$bvModal.msgBoxConfirm('Do you really want to remove this invader ?')) {
        if (await this.$store.dispatch('invaders/removeInvader', { id: this.selectedInvaderId })) {
          this.$emit('close');
        }
      }
    },
    onAddCancel () {
      this.$store.commit('invaders/SET_INVADER_TO_ADD', null);
      this.$emit('close');
    },
    async onAdd ({ formData }) {
      if (formData) {
        const newInvaderId = await this.$store.dispatch('invaders/addInvader', { data: formData });
        if (newInvaderId) {
          this.$emit('close');
        }
      }
    },
  },
};
</script>

<style lang="scss" scoped>

</style>
