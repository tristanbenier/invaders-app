<template>
  <b-modal
    :id="id"
    :size="size"
    hide-footer
    no-close-button
    :modal-class="modalClasses"
    no-fade
    :hide-backdrop="noBackdrop"
    :scrollable="scrollable"
  >
    <template v-slot:modal-backdrop />

    <template v-slot:modal-header>
      {{ headerTitle }}
      <div class="modal-actions-container">
        <b-link
          v-for="(action, i) in headerActions"
          :key="`action-${i}`"
          class="modal-action"
          @click="$emit('on-action', action. name)"
        >
          <b-icon :icon="action.icon" />
        </b-link>

        <b-link class="modal-action modal-close-x" @click="onCloseClick">
          <b-icon icon="x" />
        </b-link>
      </div>
    </template>

    <slot />
  </b-modal>
</template>

<script>
import RandomUtils from '@/lib/utils/random';

export default {
  props: {
    id: {
      type: String,
      default: `ui-modal-${RandomUtils.randomInt()}`,
    },
    headerTitle: {
      type: String,
      default: '',
    },
    size: {
      type: String,
      default: 'lg',
    },
    fade: {
      type: Boolean,
      default: false,
    },
    noBackdrop: {
      type: Boolean,
      default: false,
    },
    scrollable: {
      type: Boolean,
      default: false,
    },
    headerActions: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    modalClasses () {
      const classes = ['ui-modal'];

      return classes;
    },
  },
  mounted () {
    this.$root.$on('bv::modal::hide', (bvEvent, modalId) => {
      if (modalId === this.id) {
        this.$emit('close');
      }
    });
  },
  methods: {
    onCloseClick () {
      this.$bvModal.hide(this.id);
    },
  },
};
</script>

<style lang="scss">
.ui-modal {
  .modal-dialog {
    margin: 70px auto 0;
    width: 100%;
    max-width: 576px;

    .modal-content {
      border: 0;
      border-radius: 4px;
      box-shadow: 0 0 2px $grey_darker;
      background-color: $grey_darker;
      color: $grey_lighter;
      margin-bottom: 40px;

      .modal-header {
        border: 0;
        text-transform: uppercase;
        font-weight: bold;
        margin-left: 10px;
        margin-right: 0px;
        border-bottom: 1px solid $grey_dark;
        padding: 10px;

        .modal-actions-container {
          position: absolute;
          top: 5px;
          right: 5px;
          height: 25px;

          .modal-action {
            line-height: 20px;
            font-size: 17px;
            vertical-align: middle;
            color: $grey;
            margin-left: 10px;

            &.modal-close-x {
              font-size: 25px;
            }
          }
        }
      }

      .modal-body {
        padding: 10px;

        @media screen and (min-width: 576px) {
          padding: 10px 30px;
        }
      }
    }
  }

  &.modal-on-top {
    .modal-dialog {
      margin-top: 20px;

      .modal-content {
        min-height: calc(100vh - 20px);
      }
    }
  }
}

.modal-backdrop {
  background-color: $grey_darker;
  opacity: 0.7;
}
</style>
