import console from 'console';
import Vue from 'vue';

import User from '@/entities/User';
import UsersService from '@/services/api/UsersService';
import ArrayUtils from '@/lib/utils/array';

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
          const response = await UsersService.fetch({ page, itemsPerPage, ...params });
          items = response.map(e => User.createFromApi(e));
          commit('SET_ITEMS', items);
          page++;
        } while (items.length === itemsPerPage);
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
};

export const getters = {
  loading (state) { return key => ArrayUtils.hasElement(state.loadings, key); },
  error (state) { return key => state.errors[key]; },

  users (state) { return state.items; },
  user (state) { return userId => state.items[userId] || null; },
  usersList (state) { return Object.values(state.items); },
};
