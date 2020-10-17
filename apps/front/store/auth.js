import Vue from 'vue';

const initialState = {
  user: null,
  userToken: null,
  refreshToken: null,
  error: null,
  loading: null,
};

export const state = () => ({ ...initialState });

export const mutations = {
  SET_USER (state, user) {
    Vue.set(state, 'user', user);
  },
  SET_TOKEN (state, token) {
    Vue.set(state, 'token', token);
  },
  SET_ERROR (state, error) {
    Vue.set(state, 'error', error);
  },
  SET_LOADING (state, loading) {
    Vue.set(state, 'loading', loading);
  },
};

export const actions = {
  async login ({ commit }, { email, password }) {
    let success = true;

    try {
      commit('SET_ERROR', null);
      commit('SET_LOADING', true);

      const { token } = await this.$auth.login(email, password);

      this.$token.checkToken(token);
      this.$cookies.storeAuthTokenInCookies(token);

      commit('SET_TOKEN', token);
    } catch (err) {
      commit('SET_ERROR', err.message || 'An error occured');
      success = false;
    } finally {
      commit('SET_LOADING', false);
    }

    return success;
  },
  logout ({ commit }) {
    commit('SET_TOKEN', null);
    this.$cookies.cleanAuthCookie();
  },
};

export const getters = {
  error (state) { return state.error; },
  loading (state) { return state.loading; },

  token (state) { return state.token; },
  authenticated (state) { return !!state.token; },
};
