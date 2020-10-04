import Vue from 'vue';

const MODES = {
  SHOW_INVADERS: 'show-invaders',
  SHOW_INVADER: 'show-invader',
  ADD_INVADER: 'add-invader',
  EDIT_INVADER: 'edit-invader',
};

const initialState = {
  modes: MODES,
  selectedMode: MODES.SHOW_INVADERS,
  sidebarOpen: false,
  selectedInvaderId: null,
};

export const state = () => ({ ...initialState });

export const mutations = {
  SET_SELECTED_MODE (state, mode) {
    Vue.set(state, 'selectedMode', mode);
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

  isSidebarOpen (state) { return state.sidebarOpen; },

  selectedInvaderId (state) { return state.selectedInvaderId; },
  selectedInvader (state, getters, rootState, rootGetters) {
    if (!state.selectedInvaderId) {
      return null;
    }
    return rootGetters['invaders/invader'](state.selectedInvaderId);
  },
};
