<template>
  <div>
    <div class="cropper-container" :style="containerStyle">
      <img id="image">
    </div>

    <b-alert v-model="showQualityWarning" variant="danger" class="text-center p-1">
      Bad quality
    </b-alert>

    <b-row class="cropper-actions">
      <b-col />
      <b-col class="text-center">
        <b-button variant="link" class="cropper-action-btn">
          <b-icon icon="arrow-clockwise" @click="rotate(90)" />
        </b-button>
      </b-col>
      <b-col class="text-center">
        <b-button variant="link" class="cropper-action-btn">
          <b-icon icon="arrow-counterclockwise" @click="rotate(-90)" />
        </b-button>
      </b-col>
      <b-col />
    </b-row>

    <b-row>
      <b-col class="text-center">
        <b-button variant="secondary" @click="onCancelClick">
          Cancel
        </b-button>

        <b-button variant="primary" @click="onSaveClick">
          Save image
        </b-button>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import Cropper from 'cropperjs';
import '@/node_modules/cropperjs/dist/cropper.min.css';

// import Utils from 'shared-js-lib/utils/utils';

export default {
  props: {
    image: {
      type: null,
      default: null,
    },
    wantedSize: {
      type: Number,
      default: 750,
    },
  },
  data () {
    return {
      cropper: null,
      showQualityWarning: false,
      croppedImage: null,
    };
  },
  computed: {
    containerStyle () {
      const style = {};
      const windowWidth = window && window.innerWidth;
      if (windowWidth) {
        if (windowWidth < 576) {
          const width = windowWidth - 60;
          style.width = `${width}px`;
          style.height = `${width}px`;
        }
      }
      return style;
    },
  },
  mounted () {
    if (this.image) {
      const image = document.getElementById('image');
      const reader = new FileReader();

      reader.addEventListener('load', () => {
        image.src = reader.result;
        this.initCropper();
      }, false);

      reader.readAsDataURL(this.image);
      this.croppedImage = this.image;
    } else {
      this.cropper = null;
    }
  },
  methods: {
    initCropper () {
      const image = document.getElementById('image');

      const callback = this.onImageCropped;
      // const callback = Utils.throttle(this.onImageCropped, 500);

      this.cropper = new Cropper(image, {
        aspectRatio: 1,
        dragMode: 'move',
        viewMode: 1,
        guides: false,
        center: false,
        background: false,
        autoCropArea: 1,
        cropBoxResizable: false,
        cropBoxMovable: false,
        crop (e) {
          return callback(e);
        },
      });

      this.cropper.setCropBoxData({
        left: 10,
        top: 10,
      });
    },
    rotate (angle) {
      this.cropper.rotate(angle);
    },
    onImageCropped (e) {
      const width = e.detail.width;
      this.showQualityWarning = width < this.wantedSize * 0.9;

      if (this.cropper) {
        const canvas = this.cropper.getCroppedCanvas({
          width: this.wantedSize,
          height: this.wantedSize,
        });
        canvas.toBlob((blob) => {
          const file = new File([blob], 'cropped-image');
          this.$emit('changed', file);
          this.croppedImage = file;
        });
      }
    },
    onCancelClick () {
      this.$emit('cancel');
    },
    onSaveClick () {
      this.$emit('save', this.croppedImage);
    },
  },
};
</script>

<style lang="scss" scoped>
#image {
  display: block;
  max-width: 100%;
}

.cropper-container {
  position: relative;
  margin: 0 auto 10px;
  width: 100%;
  height: 300px;

  .cropper-view-box {
    outline: 1px solid #ddd;
    outline-color: #ddd;
  }
}

.cropper-actions {
  margin-top: 20px;
  color: #ddd;
  text-transform: uppercase;
  font-size: 12px;
  font-weight: bold;

  .cropper-action-btn {
    font-size: 20px;
    margin-bottom: 5px;
  }
}

.validate {
  margin-top: 20px;
}
</style>
