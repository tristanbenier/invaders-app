import console from 'console';
import Vue from 'vue';

import Invader from '@/entities/Invader';
import InvadersService from '@/services/api/InvadersService';
import ImagesService from '@/services/api/ImagesService';
import ArrayUtils from '@/lib/utils/array';
import ObjectUtils from '@/lib/utils/object';
import CacheUtils from '@/lib/utils/cache';
import Image from '~/entities/Image';

const initialState = {
  items: {},
  searchResults: {},
  errors: {},
  loadings: [], // This will be an array of loading elements
  invaderToAdd: null,
};

export const state = () => ({ ...initialState });

export const mutations = {
  SET_ITEMS (state, items = []) {
    items.forEach((item) => {
      Vue.set(state.items, item.id, item);
    });
  },
  SET_ITEM (state, item) {
    Vue.set(state.items, item.id, item);
  },
  SET_ITEM_POSITION (state, { id, latitude, longitude }) {
    Vue.set(state.items[id], 'latitude', latitude);
    Vue.set(state.items[id], 'longitude', longitude);
  },
  REMOVE_ITEM (state, id) {
    Vue.delete(state.items, id);
  },
  SET_ERROR (state, { key, error }) {
    Vue.set(state.errors, key, error);
  },
  SET_LOADING (state, { key, loading }) {
    const loadings = [...state.loadings];
    if (loading) {
      ArrayUtils.addElementIfNotExists(loadings, key);
    } else {
      ArrayUtils.removeElement(loadings, key);
    }
    Vue.set(state, 'loadings', loadings);
  },
  INCREASE_SEARCH_LOADING (state) {
    const loadings = [...state.loadings];
    loadings.push('search');
    Vue.set(state, 'loadings', loadings);
  },
  DECREASE_SEARCH_LOADING (state, { key }) {
    const loadings = [...state.loadings];
    ArrayUtils.removeElement(loadings, key);
    Vue.set(state, 'loadings', loadings);
  },
  SET_INVADER_TO_ADD (state, invader) {
    Vue.set(state, 'invaderToAdd', invader);
  },
};

export const actions = {
  async fetchAll ({ state, commit }, { forceFetch = false, itemsPerPage = 100, params = {} } = {}) {
    let success = true;
    commit('SET_LOADING', { key: 'fetch', loading: true });
    commit('SET_ERROR', { key: 'fetch', error: null });

    try {
      // Retrieve if force or less than 2 items in store
      if (forceFetch || Object.values(state.items).length < 2) {
        let items = [];
        let page = 1;

        do {
          const response = await InvadersService.fetch({ page, itemsPerPage, ...params });
          items = response.map(e => Invader.createFromApi(e));
          commit('SET_ITEMS', items);
          page++;
        } while (page < 2 && items.length === itemsPerPage);
      }
    } catch (e) {
      console.error(e);
      commit('SET_ERROR', { key: 'fetch', error: e.message });
      success = false;
    } finally {
      commit('SET_LOADING', { key: 'fetch', loading: false });
    }

    return success;
  },
  async search ({ commit, state }, { forceSearch = false, itemsPerPage = 100, page = 1, filters = {} }) {
    commit('INCREASE_SEARCH_LOADING');
    commit('SET_ERROR', { key: 'search', error: null });

    try {
      const params = { page, itemsPerPage, ...filters };
      const searchKey = CacheUtils.buildCacheKey(params);
      const promises = [];

      // Search results if force or not already searched
      if (forceSearch || !state.searchResults[searchKey]) {
        promises.push(InvadersService.fetch(params)
          .then((response) => {
            const items = response.map(e => Invader.createFromApi(e));
            const ids = items.map(item => item.id);
            commit('SET_SEARCH_RESULT', { key: searchKey, value: ids });
            commit('SET_ITEMS', items);
          }),
        );
      }

      await Promise.all(promises);
    } catch (e) {
      this.$logger.error(e);
      commit('SET_ERROR', { key: 'search', error: e.message });
    } finally {
      commit('DECREASE_SEARCH_LOADING', { key: 'search' });
    }
  },
  async updateInvader ({ commit, state }, { id, data }) {
    let success = true;

    try {
      commit('SET_ERROR', { key: 'update', error: null });
      commit('SET_LOADING', { key: 'update', loading: true });
      commit('SET_LOADING', { key: `update:${id}`, loading: true });

      const invader = ObjectUtils.cloneDeep(state.items[id]);

      // Add new images if needed
      const { imagesToAdd } = data;
      if (imagesToAdd && imagesToAdd.length) {
        const addImagesPromises = [];
        for (let i = 0; i < imagesToAdd.length; i++) {
          if (imagesToAdd[i]) {
            // Add new image
            addImagesPromises.push(
              ImagesService.createOne({ invaderId: id, file: imagesToAdd[i] }).then((response) => {
                invader.addImage(Image.createFromApi(response));
              }),
            );
          }
        };

        await Promise.all(addImagesPromises);
        data.imagesToAdd = undefined;
      }

      const { imagesToRemove } = data;
      if (imagesToRemove && imagesToRemove.length) {
        const imagesIdsToRemove = imagesToRemove.map(image => image.id);
        data.images = invader.images
          .filter(image => !imagesIdsToRemove.includes(image.id))
          .map(image => image.iri)
        ;
      }

      const response = await InvadersService.updateOne(id, data);
      commit('SET_ITEM', Invader.createFromApi(response));
    } catch (e) {
      success = false;
      commit('SET_ERROR', { key: 'update', error: e.message });
      throw e;
    } finally {
      commit('SET_LOADING', { key: 'update', loading: false });
      commit('SET_LOADING', { key: `update:${id}`, loading: false });
    }

    return success;
  },
  async removeInvader ({ commit }, { id }) {
    let success = true;

    try {
      commit('SET_ERROR', { key: 'remove', error: null });
      commit('SET_LOADING', { key: 'remove', loading: true });
      commit('SET_LOADING', { key: `remove:${id}`, loading: true });

      await InvadersService.removeOne(id);
      commit('REMOVE_ITEM', id);
    } catch (e) {
      success = false;
      commit('SET_ERROR', { key: 'remove', error: e.message });
      throw e;
    } finally {
      commit('SET_LOADING', { key: 'remove', loading: false });
      commit('SET_LOADING', { key: `remove:${id}`, loading: false });
    }

    return success;
  },
  async initializeInvaderToAdd ({ commit, rootGetters }, { lat, lng }) {
    let success = true;

    const invader = new Invader();
    invader.latitude = lat;
    invader.longitude = lng;

    try {
      commit('SET_ERROR', { key: 'add:initialize', error: null });
      commit('SET_LOADING', { key: 'add:initialize', loading: true });

      const result = await this.$geocoding.getAddressFromLatLng(lat, lng);
      if (result.status === 200) {
        const addressData = result.data.address;
        const number = addressData.house_number;
        invader.address1 = number ? `${number} ${addressData.road}` : addressData.road;
        invader.zipcode = addressData.postcode;
        const city = rootGetters['cities/cityByName'](addressData.city) || null;
        if (city) {
          invader.city = city;
          invader.name = city.prefix;
        }
      }
    } catch (e) {
      success = false;
      console.error(e);
      commit('SET_ERROR', { key: 'add:initialize', error: e.message });
    } finally {
      commit('SET_LOADING', { key: 'add:initialize', loading: false });
    }

    commit('SET_INVADER_TO_ADD', invader);

    return success;
  },
  async addInvader ({ commit }, { data }) {
    let newInvaderId = null;

    try {
      commit('SET_ERROR', { key: 'add', error: null });
      commit('SET_LOADING', { key: 'add', loading: true });

      const response = await InvadersService.createOne(data);
      const newInvader = Invader.createFromApi(response);
      newInvaderId = newInvader.id;

      // Add new images if needed
      const { imagesToAdd } = data;
      if (imagesToAdd && imagesToAdd.length) {
        const addImagesPromises = [];
        for (let i = 0; i < imagesToAdd.length; i++) {
          if (imagesToAdd[i]) {
            // Add new image
            addImagesPromises.push(
              ImagesService.createOne({ invaderId: newInvaderId, file: imagesToAdd[i] }).then((response) => {
                newInvader.addImage(Image.createFromApi(response));
              }),
            );
          }
        };

        await Promise.all(addImagesPromises);
        data.imagesToAdd = undefined;
      }

      commit('SET_ITEM', newInvader);
    } catch (e) {
      commit('SET_ERROR', { key: 'add', error: e.message });
      throw e;
    } finally {
      commit('SET_LOADING', { key: 'add', loading: false });
    }

    return newInvaderId;
  },
};

export const getters = {
  loading (state) { return key => ArrayUtils.hasElement(state.loadings, key); },
  error (state) { return key => state.errors[key]; },

  invaders (state) { return state.items; },
  invader (state) { return invaderId => state.items[invaderId] || null; },
  invadersList (state) { return Object.values(state.items); },
  invaderToAdd (state) { return state.invaderToAdd; },
};
