import console from 'console';
import Vue from 'vue';

import Invader from '@/entities/Invader';
import InvadersService from '@/services/api/InvadersService';
import ArrayUtils from '@/lib/utils/array';
import CacheUtils from '@/lib/utils/cache';

const initialState = {
  items: {},
  searchResults: {},
  errors: {},
  loadings: [], // This will be an array of loading elements
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
};

export const actions = {
  async fetchAll ({ state, commit }, { forceFetch = false, itemsPerPage = 5, params = {} } = {}) {
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
        } while (page < 5 && items.length === itemsPerPage);
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
};

export const getters = {
  invaders (state) { return state.items; },
  invadersList (state) { return Object.values(state.items); },
};
