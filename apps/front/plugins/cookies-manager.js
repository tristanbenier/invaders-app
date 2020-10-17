import console from 'console';
import Cookie from 'js-cookie';

const AUTH_COOKIE_NAME = '_invaders';

class CookiesManager {
  constructor (tokenManager, store) {
    this.$token = tokenManager;
    this.$store = store;

    console.info('[cookies-manager] Created');
    this.checkTokenFromCookies();
  }

  checkTokenFromCookies () {
    console.info('[token-manager] Checking cookies for authentication');

    const authCookie = this.getCookie();

    if (!authCookie) {
      return;
    }

    if (typeof authCookie !== 'object' && Object.keys(authCookie)) {
      this.cleanAuthCookie();
      return;
    }

    try {
      console.info('[token-manager] Cookie found');

      const { token } = authCookie;
      if (!token) {
        this.cleanAuthCookie();
        return;
      }

      this.$token.checkToken(token);
      this.$store.commit('auth/SET_TOKEN', token);
    } catch (e) {
      console.error(e);
    }
  }

  storeAuthTokenInCookies (token) {
    this.encodeAndSetCookie(AUTH_COOKIE_NAME, { token });
  }

  cleanAuthCookie () {
    console.info('[cookies-manager] Clean auth cookie');
    this.encodeAndSetCookie(AUTH_COOKIE_NAME, {});
  }

  /* COMMON */

  initCookie () {
    const cookieValue = {};
    this.encodeAndSetCookie(AUTH_COOKIE_NAME, cookieValue);

    return cookieValue;
  }

  getCookie () {
    const authCookie = Cookie.get(AUTH_COOKIE_NAME);

    if (!authCookie) {
      return this.initCookie();
    }

    return this.decodeCookie(authCookie);
  }

  decodeCookie (cookie) {
    const decodedCookie = Buffer.from(cookie, 'base64').toString();
    return JSON.parse(decodedCookie);
  }

  encodeAndSetCookie (key, value) {
    const base64Cookie = typeof btoa === 'function'
      ? btoa(JSON.stringify(value))
      : JSON.stringify(value).toString('base64')
    ;
    Cookie.set(key, base64Cookie, { sameSite: 'strict' });
  }
}

export default ({ app, store }, inject) => {
  inject('cookies', new CookiesManager(app.$token, store));
};
