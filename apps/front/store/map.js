import Vue from 'vue';

const MODES = {
  SHOW_INVADERS: 'show-invaders',
  SHOW_INVADER: 'show-invader',
  MOVE_INVADER: 'move-invader',
  ADD_INVADER: 'add-invader',
  EDIT_INVADER: 'edit-invader',
  SEARCH: 'search',
  SEARCH_POSITION: 'search-position',
};

const initialState = {
  modes: MODES,
  selectedMode: MODES.SHOW_INVADERS,
  center: { lat: 0, lng: 0 },
  zoom: 1,
  sidebarOpen: false,
  selectedInvaderId: null,
  searchMarkerPosition: {},
  geolocationMarkerPosition: {},
  filters: {},
};

export const state = () => ({ ...initialState });

export const mutations = {
  SET_SELECTED_MODE (state, mode) {
    Vue.set(state, 'selectedMode', mode);
  },
  SET_CENTER (state, center) {
    Vue.set(state, 'center', center);
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
  SET_SEARCH_MARKER_POSITION (state, { lat, lng }) {
    Vue.set(state, 'searchMarkerPosition', {});
    Vue.set(state.searchMarkerPosition, 'lat', lat);
    Vue.set(state.searchMarkerPosition, 'lng', lng);
  },
  SET_GEOLOCATION_MARKER_POSITION (state, { lat, lng }) {
    Vue.set(state, 'geolocationMarkerPosition', {});
    Vue.set(state.geolocationMarkerPosition, 'lat', lat);
    Vue.set(state.geolocationMarkerPosition, 'lng', lng);
  },
  SET_FILTER (state, { key, value }) {
    Vue.set(state.filters, key, value);
  },
};

export const actions = {};

export const getters = {
  modes (state) { return state.modes; },
  selectedMode (state) { return state.selectedMode; },

  center (state) { return state.center; },
  zoom (state) { return state.zoom; },

  isSidebarOpen (state) { return state.sidebarOpen; },

  filters (state) { return state.filters; },
  filter (state) { return key => state.filters[key] || null; },

  selectedInvaderId (state) { return state.selectedInvaderId; },
  selectedInvader (state, getters, rootState, rootGetters) {
    if (!state.selectedInvaderId) {
      return null;
    }

    return rootGetters['invaders/invader'](state.selectedInvaderId);
  },
  displayedInvaders (state, getters, rootState, rootGetters) {
    if (state.selectedMode === state.modes.MOVE_INVADER && state.selectedInvaderId) {
      return [getters.selectedInvader];
    }

    const filters = getters.filters;
    let filteredInvaders = rootGetters['invaders/invadersList'];

    if (Object.keys(filters).length) {
      filteredInvaders = filteredInvaders.filter((invader) => {
        return Object.keys(filters)
          .filter(key => !!filters[key])
          .every((key) => {
            const values = filters[key];

            if (key === 'users') {
              if (values.includes(0)) {
                return invader.users.length === 0;
              }

              return values.every(userId => invader.users.map(u => u.id).includes(userId));
            }

            if (key === 'points') {
              const points = invader.points || 0;
              return values.includes(points);
            }

            if (key === 'cities') {
              return invader.city && values.includes(invader.city.id);
            }

            if (key === 'status') {
              return invader.status && values.includes(invader.status.name);
            }
          })
        ;
      });
    }

    return filteredInvaders;
  },
  searchMarkerPosition (state) { return state.searchMarkerPosition; },
  geolocationMarkerPosition (state) { return state.geolocationMarkerPosition; },
};
