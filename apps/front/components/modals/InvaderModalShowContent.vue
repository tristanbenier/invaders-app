<template>
  <div v-if="invader" class="show-invader-popup-content">
    <b-row>
      <b-col class="text-left">
        Caught by:
        {{ invader.users.length ? invader.users.map(u => u.name).join(', ') : '-' }}
      </b-col>
      <b-col class="text-right invader-status">
        {{ invader.status.name }}
      </b-col>
    </b-row>

    <b-row class="invader-address mt-3">
      <b-col>
        <div>
          {{ invader.address1 }}
        </div>
        <div v-if="invader.address2">
          {{ invader.address2 }}
        </div>
        <div>
          {{ invader.zipcode }} {{ invader.city.name }}
        </div>
      </b-col>
    </b-row>

    <b-row v-if="invader.comment" class="invader-comment">
      <b-col>
        {{ invader.comment }}
      </b-col>
    </b-row>

    <div class="invader-images">
      <VueCarousel
        v-if="invader.images.length > 1"
        :data="carouselImages"
        :autoplay="false"
        indicator-type="disc"
      />
      <div v-if="invader.images.length === 1" class="invader-image">
        <UiBlurImageLoader
          :src="invader.images[0].url"
          :small-src="invader.images[0].thumbnailUrl"
        />
      </div>
    </div>
  </div>
</template>

<script>
import VueCarousel from '@chenfengyuan/vue-carousel';

import Invader from '@/entities/Invader';

export default {
  components: { VueCarousel },
  props: {
    invader: {
      type: Invader,
      default: null,
    },
    position: {
      type: Object,
      default: () => ({}),
    },
    data: {
      type: Object,
      default: () => ({}),
    },
  },
  data () {
    return {
      loading: false,
    };
  },
  computed: {
    carouselImages () {
      if (this.invader && this.invader.images) {
        return this.invader.images.map(image => `
          <div class="invader-image">
            <UiBlurImageLoader
              src="${image.url}"
              small-src="${image.thumbnailUrl}"
            />
          </div>`,
        );
      }
      return [];
    },
  },
  mounted () {
    this.mount();
  },
  methods: {
    mount () {
      this.loading = true;
    },
    onRemoveClick () {
      const message = this.invader.name
        ? `Do you really want to remove ${this.invader.name} ?`
        : 'Do you really want to remove this invader ?'
      ;
      if (confirm(message)) {
        this.$emit('remove', this.invader.id);
      }
    },
    onEditClick () {
      this.$emit('click-edit', this.invader.id);
    },
  },
};
</script>

<style lang="scss" scoped>
.show-invader-popup-content {
  .header {
    .title {
      float: left;
      text-transform: uppercase;
    }

    .actions {
      float: right;

      img {
        cursor: pointer;
        height: 15px;
        margin: 2px;
      }
    }
  }

  .body {
    .user-avatar {
      border-radius: 50%;
      height: 40px;
      margin: 5px;
    }

    .invader-status {
      line-height: 40px;
      text-transform: uppercase;
    }

    .invader-address {
      margin: 10px;
    }

    .invader-comment {
      font-style: italic;
      margin: 10px;
    }
  }
}
</style>

<style lang="scss">
.invader-images {
  margin: 10px;

  .invader-image {
    margin: 10px;

    img {
      width: 100% !important;
    }
  }
}
</style>
