import Vue from 'vue';

const initialState = {
  filters: {},
};

export const state = () => ({ ...initialState });

export const mutations = {
  SET_FILTER (state, { key, value }) {
    Vue.set(state.filters, key, value);
  },
};

export const actions = {};

export const getters = {
  filters (state) { return state.filters; },
  filter (state) { return key => state.filters[key] || null; },

  displayedInvaders (state, getters, rootState, rootGetters) {
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
              return values.includes(invader.points);
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
};
