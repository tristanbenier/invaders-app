<template>
  <b-modal
    id="nav-modal"
    no-fade
    hide-header-close
    hide-backdrop
    :modal-class="['nav-container']"
  >
    <template v-slot:modal-title>
      <b-button variant="link" class="close-nav-btn" @click="$emit('close-nav')">
        <b-icon icon="x" />
      </b-button>
    </template>

    <template v-slot:modal-footer>
      footer
    </template>

    <div class="links-container text-center">
      <NuxtLink
        :to="{name: 'index' }"
        class="nav-link-item d-block my-2"
        @click.native="$emit('close-nav')"
      >
        Map
      </NuxtLink>

      <NuxtLink
        :to="{ name: 'gallery' }"
        class="nav-link-item d-block my-2"
        @click.native="$emit('close-nav')"
      >
        Gallery
      </NuxtLink>

      <NuxtLink
        :to="{ name: 'my-account' }"
        class="nav-link-item d-block my-2 mb-5"
        @click.native="$emit('close-nav')"
      >
        My account
      </NuxtLink>
    </div>
  </b-modal>
</template>

<script>

export default {
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

<style lang="scss">
$nav_header_height: 50px;
$nav_footer_height: 50px;

.nav-container {
  background-color: $grey_darker;

  .modal-dialog {
    margin: 0;
    max-width: 100%;

    .modal-content {
      border: none;
      background: none;

      .modal-header {
        border: none;
        height: $nav_header_height;

        .close-nav-btn {
          color: $white;
          font-size: 20px;
          position: absolute;
          top: 9px;
          right: 5px;
        }
      }

      .modal-body {
        width: 100%;
        height: calc(100vh - #{$nav_footer_height} - #{$nav_header_height});
        max-width: 300px;
        margin: 0 auto;
        padding: 0;

        .links-container {
          position: absolute;
          margin: 0 auto;
          left: 0;
          width: 100%;
          top: 50%;
          transform: translateY(-60%);

          .nav-link-item {
            font-size: 20px;
            font-weight: 500;
            color: $white;
          }
        }
      }

      .modal-footer {
        height: $nav_footer_height;
        justify-content: center;
        padding: 0;
        border: none;
        border-top: 1px solid $grey;

        .footer-link-item {
          color: $grey;
          font-size: 12px;
          font-weight: 300;
          text-transform: uppercase;
        }
      }
    }
  }
}
</style>
