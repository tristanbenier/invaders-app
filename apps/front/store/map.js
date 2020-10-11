import Vue from 'vue';

const MODES = {
  SHOW_INVADERS: 'show-invaders',
  SHOW_INVADER: 'show-invader',
  MOVE_INVADER: 'move-invader',
  ADD_INVADER: 'add-invader',
  EDIT_INVADER: 'edit-invader',
};

const initialState = {
  modes: MODES,
  selectedMode: MODES.SHOW_INVADERS,
  zoom: 1,
  sidebarOpen: false,
  selectedInvaderId: null,
};

export const state = () => ({ ...initialState });

export const mutations = {
  SET_SELECTED_MODE (state, mode) {
    Vue.set(state, 'selectedMode', mode);
  },
  SET_ZOOM (state, zoom) {
    Vue.set(state, 'zoom', zoom);
  },
  OPEN_SIDEBAR (state) {
    Vue.set(state, 'sidebarOpen', true);
  },
  CLOSE_SIDEBAR (state) {
    Vue.set(state, 'sidebarOpen', false);
  },
  SET_SELECTED_INVADER_ID (state, invaderId) {
    Vue.set(state, 'selectedInvaderId', invaderId);
  },
};

export const actions = {};

export const getters = {
  modes (state) { return state.modes; },
  selectedMode (state) { return state.selectedMode; },

  zoom (state) { return state.zoom; },

  isSidebarOpen (state) { return state.sidebarOpen; },

  selectedInvaderId (state) { return state.selectedInvaderId; },
  selectedInvader (state, getters, rootState, rootGetters) {
    if (!state.selectedInvaderId) {
      return null;
    }

    return rootGetters['invaders/invader'](state.selectedInvaderId);
  },
  displayedInvaders (state, getters, rootState, rootGetters) {
    const invadersList = rootGetters['invaders/invadersList'];

    if (state.selectedMode === state.modes.MOVE_INVADER && state.selectedInvaderId) {
      return [getters.selectedInvader];
    }

    return invadersList;
  },
};
