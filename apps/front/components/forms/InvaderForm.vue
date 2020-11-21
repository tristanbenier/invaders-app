<template>
  <div v-if="localData !== null">
    <b-form v-if="mode === MODES.DEFAULT" @submit.prevent="onSubmit">
      <b-row class="mb-3">
        <b-col>
          <div>
            <label>
              Caught by
            </label>
          </div>

          <b-spinner v-if="usersLoading" small />
          <b-badge
            v-for="user in usersOptions"
            :key="user.value"
            class="user-item m-1 px-2 py-1"
            :variant="localData.usersId.includes(user.value) ? 'primary': 'secondary'"
            @click="onUserClick(user.value)"
          >
            {{ user.text }}
          </b-badge>
        </b-col>
      </b-row>

      <b-row class="mb-3">
        <b-col>
          <div>
            <label>
              Status
            </label>
          </div>

          <b-spinner v-if="statusLoading" small />
          <b-badge
            v-for="status in statusOptions"
            :key="status.value"
            class="status-item m-1 px-2 py-1"
            :variant="status.value === localData.statusId ? 'primary': 'secondary'"
            @click="localData.statusId = status.value"
          >
            {{ status.text }}
          </b-badge>
        </b-col>
      </b-row>

      <b-row class="mb-3">
        <b-col>
          <div>
            <label>
              Points
            </label>
          </div>

          <b-badge
            v-for="points in pointsOptions"
            :key="points"
            class="points-item m-1 px-2 py-1"
            :variant="points === localData.points ? 'primary': 'secondary'"
            @click="localData.points = points"
          >
            {{ points }}
          </b-badge>
        </b-col>
      </b-row>

      <b-row>
        <b-col>
          <b-form-group
            id="input-group-name"
            label="Name"
            label-for="input-name"
          >
            <b-form-input
              id="input-name"
              v-model="localData.name"
              type="text"
              required
              placeholder="Name"
            />
          </b-form-group>
        </b-col>
      </b-row>

      <b-row>
        <b-col>
          <b-form-group
            id="input-group-address"
            label="Address"
            label-for="input-address"
          >
            <b-form-input
              id="input-address1"
              v-model="localData.address1"
              type="text"
              required
              placeholder="Address"
            />
            <b-form-input
              id="input-address1"
              v-model="localData.address2"
              type="text"
              placeholder="Address complement"
              class="mt-2"
            />
          </b-form-group>
        </b-col>
      </b-row>

      <b-row>
        <b-col sm>
          <b-form-group
            id="input-group-zipcode"
            label="Zipcode"
            label-for="input-zipcode"
          >
            <b-form-input
              id="input-zipcode"
              v-model="localData.zipcode"
              type="text"
              required
              placeholder="Zipcode"
            />
          </b-form-group>
        </b-col>
        <b-col sm>
          <b-form-group
            id="input-group-city"
            label="City"
            label-for="input-city"
          >
            <b-form-select
              v-if="citiesOptions.length"
              id="input-cities"
              v-model="localData.cityId"
              :options="citiesOptions"
            />
            <b-spinner v-if="citiesLoading" small />
          </b-form-group>
        </b-col>
      </b-row>

      <b-row>
        <b-col>
          <b-form-group
            id="input-group-comment"
            label="Comment"
            label-for="input-comment"
          >
            <b-form-input
              id="input-comment"
              v-model="localData.comment"
              type="text"
              placeholder="Comment"
            />
          </b-form-group>
        </b-col>
      </b-row>

      <b-row>
        <b-col cols="12">
          <label>
            Images
            <b-button variant="primary" size="sm" class="ml-2 btn-xs" @click="onImageAddClick">
              + Add image
            </b-button>
            <input id="image-input" type="file" accept="image/*" @change="onImageSelected">
          </label>
        </b-col>

        <b-col v-for="image in localData.images" :key="image.id" cols="3" class="mt-1 text-center">
          <UiBlurImageLoader
            :src="image.url"
            :small-src="image.thumbnailUrl"
            class="thumbnail-image"
          />
          <b-button variant="danger" size="sm" class="mt-2 btn-xs" @click="onImageRemoveClick(image)">
            Remove
          </b-button>
        </b-col>

        <b-col v-for="(image, index) in imagesToAddDataUrls" :key="image" cols="3" class="mt-1 text-center">
          <img
            :src="image"
            class="thumbnail-image"
          >
          <b-button variant="danger" size="sm" class="mt-2 btn-xs" @click="onImageToAddRemoveClick(index)">
            Remove
          </b-button>
        </b-col>
      </b-row>

      <b-row>
        <b-col v-if="formError" cols="12" class="mt-2">
          <b-alert show variant="danger">
            {{ formError }}
          </b-alert>
        </b-col>

        <b-col class="text-center mt-3">
          <b-button variant="secondary" @click="$emit('cancel')">
            Cancel
          </b-button>
          <b-button v-if="!loading" type="submit" variant="primary">
            <b-icon icon="check" /> Save
          </b-button>
          <b-spinner v-if="loading" small class="my-2" />
        </b-col>
      </b-row>
    </b-form>

    <b-row v-if="mode === MODES.CROP_IMAGE && selectedImage">
      <b-col>
        <ImageCropper
          :image="selectedImage"
          @cancel="onImageCropCancel"
          @save="onImageCropped"
        />
      </b-col>
    </b-row>
  </div>
</template>

<script>
import ArrayUtils from '@/lib/utils/array';

import Invader from '@/entities/Invader';
import Status from '@/entities/Status';

import ImageCropper from '@/components/ImageCropper';

const MODES = {
  DEFAULT: 'default',
  CROP_IMAGE: 'crop-image',
};

export default {
  components: { ImageCropper },
  props: {
    invader: {
      type: Invader,
      default: null,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    error: {
      type: String,
      default: null,
    },
  },
  data () {
    return {
      mode: MODES.DEFAULT,
      MODES,
      STATUS: Status.STATUSES,
      localData: null,
      selectedImage: null,
      imagesToAddDataUrls: [],
      pointsOptions: Invader.POINTS,
      formError: null,
    };
  },
  computed: {
    users () {
      return this.$store.getters['users/users'];
    },
    usersList () {
      return this.$store.getters['users/usersList'];
    },
    usersOptions () {
      return this.usersList.map(c => ({
        text: c.name,
        value: c.id,
      }));
    },
    usersLoading () {
      return this.$store.getters['users/loading']('fetch');
    },
    statuses () {
      return this.$store.getters['status/statuses'];
    },
    statusList () {
      return this.$store.getters['status/statusesList'];
    },
    statusOptions () {
      return this.statusList.map(c => ({
        text: c.name,
        value: c.id,
      }));
    },
    statusLoading () {
      return this.$store.getters['status/loading']('fetch');
    },
    cities () {
      return this.$store.getters['cities/cities'];
    },
    citiesList () {
      return this.$store.getters['cities/citiesList'];
    },
    citiesOptions () {
      return this.citiesList.map(c => ({
        text: c.name,
        value: c.id,
      }));
    },
    citiesLoading () {
      return this.$store.getters['cities/loading']('fetch');
    },
    invadersList () {
      return this.$store.getters['invaders/invadersList'];
    },
  },
  mounted () {
    this.loadInvaders();
    this.loadUsers();
    this.loadStatuses();
    this.loadCities();
    this.buildLocalData();
  },
  methods: {
    loadInvaders () {
      this.$store.dispatch('invaders/fetchAll');
    },
    loadUsers () {
      this.$store.dispatch('users/fetchAll');
    },
    loadCities () {
      this.$store.dispatch('cities/fetchAll');
    },
    loadStatuses () {
      this.$store.dispatch('status/fetchAll');
    },
    buildLocalData () {
      this.localData = this.invader.toFormData();
    },
    onUserClick (userId) {
      this.localData.usersId = ArrayUtils.toggleElement(this.localData.usersId, userId);
    },
    onImageRemoveClick (image) {
      this.localData.imagesToRemove = this.localData.imagesToRemove || [];
      this.localData.imagesToRemove.push(image);

      this.localData.images = this.localData.images.filter(i => i.id !== image.id);
    },
    onImageAddClick () {
      this.$el.querySelector('#image-input').click();
    },
    onImageSelected (e) {
      const file = e.target && e.target.files && e.target.files[0];
      if (file) {
        this.selectedImage = file;
        this.mode = MODES.CROP_IMAGE;
        e.target.value = '';
      }
    },
    onImageCropCancel () {
      this.selectedImage = null;
      this.mode = MODES.DEFAULT;
    },
    onImageCropped (image) {
      this.mode = MODES.DEFAULT;

      this.localData.imagesToAdd = this.localData.imagesToAdd || [];
      this.localData.imagesToAdd.push(image);

      const reader = new FileReader();
      reader.addEventListener('load', () => {
        this.imagesToAddDataUrls.push(reader.result);
      }, false);
      reader.readAsDataURL(image);
    },
    onImageToAddRemoveClick (imageIndex) {
      this.imagesToAddDataUrls.splice(imageIndex, 1);
      this.localData.imagesToAdd.splice(imageIndex, 1);
    },
    onSubmit () {
      // Check data
      this.formError = null;

      // Check if name selected
      if (!this.localData.name) {
        this.formError = 'No name selected';
        return;
      }

      // Check if invader already exists with same name
      if (this.invadersList.find(i => i.name === this.localData.name & i.id !== this.localData.id)) {
        this.formError = `Invader ${this.localData.name} already exists`;
        return;
      }

      // Check if status selected
      if (!this.localData.statusId) {
        this.formError = 'No status selected';
        return;
      }
      // Check if city selected
      if (!this.localData.cityId) {
        this.formError = 'No city selected';
        return;
      }

      // Check if selected city found
      const city = this.cities[this.localData.cityId];
      if (!city) {
        this.formError = 'No city found';
        return;
      }

      // Check if invader prefix matches with city prefix
      const invaderPrefix = `${this.localData.name.split('_').shift()}_`;
      if (invaderPrefix !== city.prefix) {
        this.formError = `Bad invader name (should start with "${city.prefix}")`;
        return;
      }

      const formData = JSON.parse(JSON.stringify(this.localData));

      formData.city = this.cities[formData.cityId].iri;
      formData.cityId = undefined;

      formData.status = this.statuses[formData.statusId].iri;
      formData.statusId = undefined;

      formData.users = formData.usersId.map(userId => this.users[userId].iri);
      formData.usersId = undefined;

      formData.images = undefined;
      formData.imagesToAdd = this.localData.imagesToAdd;

      this.$emit('submit', { formData });
    },
  },
};
</script>

<style lang="scss" scoped>
.user-item,
.status-item,
.points-item {
  cursor: pointer;
}
#image-input {
  display: none;
}
.thumbnail-image {
  width: 100%;
}
</style>
